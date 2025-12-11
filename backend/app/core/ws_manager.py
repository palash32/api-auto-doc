"""WebSocket connection manager for real-time updates."""

from typing import Dict, List, Optional
from fastapi import WebSocket
import asyncio
import json
from datetime import datetime

from app.core.logger import logger


class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""
    
    def __init__(self):
        # Map user_id -> list of websocket connections
        self.active_connections: Dict[str, List[WebSocket]] = {}
        # Map organization_id -> list of user_ids (for org-wide broadcasts)
        self.org_users: Dict[str, List[str]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str, org_id: Optional[str] = None):
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        
        # Track org membership for org-wide broadcasts
        if org_id:
            if org_id not in self.org_users:
                self.org_users[org_id] = []
            if user_id not in self.org_users[org_id]:
                self.org_users[org_id].append(user_id)
        
        logger.info(f"WebSocket connected: user={user_id}, org={org_id}")
    
    def disconnect(self, websocket: WebSocket, user_id: str):
        """Remove a WebSocket connection."""
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        logger.info(f"WebSocket disconnected: user={user_id}")
    
    async def send_to_user(self, user_id: str, message: dict):
        """Send a message to all connections of a specific user."""
        if user_id in self.active_connections:
            disconnected = []
            for ws in self.active_connections[user_id]:
                try:
                    await ws.send_json(message)
                except Exception as e:
                    logger.warning(f"Failed to send to user {user_id}: {e}")
                    disconnected.append(ws)
            
            # Clean up disconnected sockets
            for ws in disconnected:
                self.disconnect(ws, user_id)
    
    async def broadcast_to_org(self, org_id: str, message: dict):
        """Broadcast a message to all users in an organization."""
        if org_id in self.org_users:
            for user_id in self.org_users[org_id]:
                await self.send_to_user(user_id, message)
    
    async def broadcast_all(self, message: dict):
        """Broadcast a message to all connected users."""
        for user_id in list(self.active_connections.keys()):
            await self.send_to_user(user_id, message)
    
    def get_connection_count(self) -> int:
        """Get total number of active connections."""
        return sum(len(conns) for conns in self.active_connections.values())


# Singleton instance
ws_manager = ConnectionManager()


# Message types for real-time updates
class WSMessageType:
    """WebSocket message types."""
    SCAN_STARTED = "scan_started"
    SCAN_PROGRESS = "scan_progress"
    SCAN_COMPLETED = "scan_completed"
    SCAN_FAILED = "scan_failed"
    REPO_UPDATED = "repo_updated"
    ENDPOINT_DISCOVERED = "endpoint_discovered"
    NOTIFICATION = "notification"


def create_ws_message(
    msg_type: str,
    data: dict,
    repository_id: Optional[str] = None
) -> dict:
    """Create a standardized WebSocket message."""
    return {
        "type": msg_type,
        "data": data,
        "repository_id": repository_id,
        "timestamp": datetime.utcnow().isoformat()
    }


# Convenience functions for scan progress updates
async def notify_scan_started(user_id: str, repo_id: str, repo_name: str):
    """Notify user that a scan has started."""
    await ws_manager.send_to_user(user_id, create_ws_message(
        WSMessageType.SCAN_STARTED,
        {"repository_name": repo_name, "status": "scanning"},
        repo_id
    ))


async def notify_scan_progress(
    user_id: str,
    repo_id: str,
    repo_name: str,
    progress: int,
    files_scanned: int,
    total_files: int,
    endpoints_found: int
):
    """Notify user of scan progress."""
    await ws_manager.send_to_user(user_id, create_ws_message(
        WSMessageType.SCAN_PROGRESS,
        {
            "repository_name": repo_name,
            "progress": progress,
            "files_scanned": files_scanned,
            "total_files": total_files,
            "endpoints_found": endpoints_found
        },
        repo_id
    ))


async def notify_scan_completed(
    user_id: str,
    repo_id: str,
    repo_name: str,
    endpoints_count: int,
    duration_seconds: float
):
    """Notify user that a scan has completed."""
    await ws_manager.send_to_user(user_id, create_ws_message(
        WSMessageType.SCAN_COMPLETED,
        {
            "repository_name": repo_name,
            "endpoints_count": endpoints_count,
            "duration_seconds": round(duration_seconds, 2),
            "status": "completed"
        },
        repo_id
    ))


async def notify_scan_failed(user_id: str, repo_id: str, repo_name: str, error: str):
    """Notify user that a scan has failed."""
    await ws_manager.send_to_user(user_id, create_ws_message(
        WSMessageType.SCAN_FAILED,
        {
            "repository_name": repo_name,
            "error": error,
            "status": "failed"
        },
        repo_id
    ))
