"use client";

import { useState, useEffect, useRef, useCallback } from "react";

export interface WSMessage {
    type: string;
    data: Record<string, any>;
    repository_id?: string;
    timestamp: string;
}

export type WSMessageType =
    | "scan_started"
    | "scan_progress"
    | "scan_completed"
    | "scan_failed"
    | "repo_updated"
    | "endpoint_discovered"
    | "notification";

interface UseWebSocketOptions {
    userId?: string;
    orgId?: string;
    onMessage?: (message: WSMessage) => void;
    onConnect?: () => void;
    onDisconnect?: () => void;
    reconnectInterval?: number;
    maxReconnectAttempts?: number;
}

interface UseWebSocketReturn {
    isConnected: boolean;
    messages: WSMessage[];
    lastMessage: WSMessage | null;
    send: (data: string) => void;
    connect: () => void;
    disconnect: () => void;
}

export function useWebSocket(options: UseWebSocketOptions = {}): UseWebSocketReturn {
    const {
        userId = "anonymous",
        orgId,
        onMessage,
        onConnect,
        onDisconnect,
        reconnectInterval = 3000,
        maxReconnectAttempts = 5
    } = options;

    const [isConnected, setIsConnected] = useState(false);
    const [messages, setMessages] = useState<WSMessage[]>([]);
    const [lastMessage, setLastMessage] = useState<WSMessage | null>(null);

    const wsRef = useRef<WebSocket | null>(null);
    const reconnectAttemptsRef = useRef(0);
    const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
    const pingIntervalRef = useRef<NodeJS.Timeout | null>(null);

    const getWsUrl = useCallback(() => {
        // Determine WebSocket URL based on environment
        const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
        const host = process.env.NEXT_PUBLIC_WS_HOST || "localhost:8000";

        let url = `${protocol}//${host}/ws?user_id=${userId}`;
        if (orgId) {
            url += `&org_id=${orgId}`;
        }

        return url;
    }, [userId, orgId]);

    const connect = useCallback(() => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            return;
        }

        try {
            const url = getWsUrl();
            console.log("[WS] Connecting to:", url);

            wsRef.current = new WebSocket(url);

            wsRef.current.onopen = () => {
                console.log("[WS] Connected");
                setIsConnected(true);
                reconnectAttemptsRef.current = 0;
                onConnect?.();

                // Start ping interval to keep connection alive
                pingIntervalRef.current = setInterval(() => {
                    if (wsRef.current?.readyState === WebSocket.OPEN) {
                        wsRef.current.send("ping");
                    }
                }, 30000); // Ping every 30 seconds
            };

            wsRef.current.onmessage = (event) => {
                // Handle pong
                if (event.data === "pong") {
                    return;
                }

                try {
                    const message: WSMessage = JSON.parse(event.data);
                    console.log("[WS] Message received:", message.type);

                    setMessages(prev => [...prev.slice(-99), message]); // Keep last 100 messages
                    setLastMessage(message);
                    onMessage?.(message);
                } catch (e) {
                    console.warn("[WS] Failed to parse message:", event.data);
                }
            };

            wsRef.current.onclose = (event) => {
                console.log("[WS] Disconnected:", event.code, event.reason);
                setIsConnected(false);
                onDisconnect?.();

                // Clear ping interval
                if (pingIntervalRef.current) {
                    clearInterval(pingIntervalRef.current);
                }

                // Attempt to reconnect
                if (reconnectAttemptsRef.current < maxReconnectAttempts) {
                    reconnectAttemptsRef.current += 1;
                    console.log(`[WS] Reconnecting in ${reconnectInterval}ms (attempt ${reconnectAttemptsRef.current}/${maxReconnectAttempts})`);

                    reconnectTimeoutRef.current = setTimeout(() => {
                        connect();
                    }, reconnectInterval);
                }
            };

            wsRef.current.onerror = (error) => {
                console.error("[WS] Error:", error);
            };

        } catch (error) {
            console.error("[WS] Connection failed:", error);
        }
    }, [getWsUrl, onConnect, onDisconnect, onMessage, reconnectInterval, maxReconnectAttempts]);

    const disconnect = useCallback(() => {
        // Clear timers
        if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current);
        }
        if (pingIntervalRef.current) {
            clearInterval(pingIntervalRef.current);
        }

        // Reset reconnect attempts
        reconnectAttemptsRef.current = maxReconnectAttempts;

        // Close connection
        if (wsRef.current) {
            wsRef.current.close();
            wsRef.current = null;
        }
    }, [maxReconnectAttempts]);

    const send = useCallback((data: string) => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(data);
        } else {
            console.warn("[WS] Cannot send - not connected");
        }
    }, []);

    // Connect on mount, disconnect on unmount
    useEffect(() => {
        connect();

        return () => {
            disconnect();
        };
    }, [connect, disconnect]);

    return {
        isConnected,
        messages,
        lastMessage,
        send,
        connect,
        disconnect
    };
}

// Helper hook for scan progress specifically
export function useScanProgress(onScanComplete?: (repoId: string) => void) {
    const [activeScan, setActiveScan] = useState<{
        repoId: string;
        repoName: string;
        progress: number;
        filesScanned: number;
        totalFiles: number;
        endpointsFound: number;
    } | null>(null);

    const handleMessage = useCallback((message: WSMessage) => {
        switch (message.type) {
            case "scan_started":
                setActiveScan({
                    repoId: message.repository_id || "",
                    repoName: message.data.repository_name || "Repository",
                    progress: 0,
                    filesScanned: 0,
                    totalFiles: 0,
                    endpointsFound: 0
                });
                break;

            case "scan_progress":
                setActiveScan(prev => prev ? {
                    ...prev,
                    progress: message.data.progress || 0,
                    filesScanned: message.data.files_scanned || 0,
                    totalFiles: message.data.total_files || 0,
                    endpointsFound: message.data.endpoints_found || 0
                } : null);
                break;

            case "scan_completed":
                if (message.repository_id) {
                    onScanComplete?.(message.repository_id);
                }
                // Clear after a delay so user sees completion
                setTimeout(() => setActiveScan(null), 3000);
                break;

            case "scan_failed":
                setTimeout(() => setActiveScan(null), 5000);
                break;
        }
    }, [onScanComplete]);

    const ws = useWebSocket({ onMessage: handleMessage });

    return {
        ...ws,
        activeScan
    };
}
