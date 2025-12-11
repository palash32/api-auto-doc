"""WebSocket endpoint for real-time updates."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Optional

from app.core.ws_manager import ws_manager
from app.core.logger import logger

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: Optional[str] = Query(None),
    org_id: Optional[str] = Query(None)
):
    """
    WebSocket endpoint for real-time updates.
    
    Connect with: ws://localhost:8000/ws?user_id=xxx&org_id=yyy
    
    Message types received:
    - scan_started: A repository scan has begun
    - scan_progress: Scan progress update (files, endpoints found)
    - scan_completed: Scan finished successfully
    - scan_failed: Scan encountered an error
    - repo_updated: Repository was modified
    - notification: General notification
    """
    
    # Use a default user_id if not provided (for dev/testing)
    effective_user_id = user_id or "anonymous"
    
    await ws_manager.connect(websocket, effective_user_id, org_id)
    
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            
            # Handle ping/pong for keep-alive
            if data == "ping":
                await websocket.send_text("pong")
            else:
                # Log any other incoming messages (could add command handling)
                logger.debug(f"WS received from {effective_user_id}: {data}")
                
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, effective_user_id)
    except Exception as e:
        logger.error(f"WebSocket error for {effective_user_id}: {e}")
        ws_manager.disconnect(websocket, effective_user_id)


@router.get("/ws/status")
async def websocket_status():
    """Get WebSocket connection status."""
    return {
        "active_connections": ws_manager.get_connection_count(),
        "connected_users": len(ws_manager.active_connections)
    }
