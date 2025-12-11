"use client";

import React, { useEffect, useState } from "react";
import { X, CheckCircle, AlertCircle, Loader2, FileCode } from "lucide-react";
import { cn } from "@/lib/utils";
import { WSMessage } from "@/hooks/useWebSocket";

interface ScanProgressToastProps {
    message: WSMessage | null;
    onDismiss: () => void;
    onViewResults?: (repoId: string) => void;
}

export function ScanProgressToast({
    message,
    onDismiss,
    onViewResults
}: ScanProgressToastProps) {
    const [visible, setVisible] = useState(false);

    useEffect(() => {
        if (message) {
            setVisible(true);
        }
    }, [message]);

    useEffect(() => {
        // Auto-dismiss after scan completes/fails
        if (message?.type === "scan_completed" || message?.type === "scan_failed") {
            const timer = setTimeout(() => {
                setVisible(false);
                setTimeout(onDismiss, 300); // Wait for animation
            }, 5000);
            return () => clearTimeout(timer);
        }
    }, [message, onDismiss]);

    if (!message) return null;

    const { type, data, repository_id } = message;
    const repoName = data.repository_name || "Repository";

    const getIcon = () => {
        switch (type) {
            case "scan_started":
            case "scan_progress":
                return <Loader2 className="w-5 h-5 text-blue-400 animate-spin" />;
            case "scan_completed":
                return <CheckCircle className="w-5 h-5 text-emerald-400" />;
            case "scan_failed":
                return <AlertCircle className="w-5 h-5 text-red-400" />;
            default:
                return <FileCode className="w-5 h-5 text-gray-400" />;
        }
    };

    const getTitle = () => {
        switch (type) {
            case "scan_started":
                return "Scan Started";
            case "scan_progress":
                return "Scanning...";
            case "scan_completed":
                return "Scan Complete";
            case "scan_failed":
                return "Scan Failed";
            default:
                return "Update";
        }
    };

    const getMessage = () => {
        switch (type) {
            case "scan_started":
                return `Scanning ${repoName}`;
            case "scan_progress":
                return `${data.files_scanned || 0}/${data.total_files || "?"} files • ${data.endpoints_found || 0} endpoints`;
            case "scan_completed":
                return `Found ${data.endpoints_count || 0} endpoints in ${data.duration_seconds || 0}s`;
            case "scan_failed":
                return data.error || "An error occurred";
            default:
                return "";
        }
    };

    const progress = type === "scan_progress" ? data.progress || 0 :
        type === "scan_completed" ? 100 : 0;

    return (
        <div
            className={cn(
                "fixed bottom-6 right-6 z-50 w-80",
                "transition-all duration-300 ease-out",
                visible ? "translate-y-0 opacity-100" : "translate-y-4 opacity-0"
            )}
        >
            <div className={cn(
                "rounded-xl border backdrop-blur-xl shadow-2xl overflow-hidden",
                type === "scan_failed"
                    ? "bg-red-900/40 border-red-500/30"
                    : type === "scan_completed"
                        ? "bg-emerald-900/40 border-emerald-500/30"
                        : "bg-gray-900/90 border-white/10"
            )}>
                {/* Progress bar */}
                {(type === "scan_progress" || type === "scan_started") && (
                    <div className="h-1 bg-white/5">
                        <div
                            className="h-full bg-gradient-to-r from-blue-500 to-blue-400 transition-all duration-500"
                            style={{ width: `${progress}%` }}
                        />
                    </div>
                )}

                <div className="p-4">
                    <div className="flex items-start gap-3">
                        {getIcon()}

                        <div className="flex-1 min-w-0">
                            <p className="font-medium text-sm text-white">
                                {getTitle()}
                            </p>
                            <p className="text-xs text-gray-400 truncate mt-0.5">
                                {getMessage()}
                            </p>
                        </div>

                        <button
                            onClick={() => {
                                setVisible(false);
                                setTimeout(onDismiss, 300);
                            }}
                            className="p-1 hover:bg-white/10 rounded-lg transition-colors"
                        >
                            <X className="w-4 h-4 text-gray-500" />
                        </button>
                    </div>

                    {/* View Results button for completed scans */}
                    {type === "scan_completed" && repository_id && onViewResults && (
                        <button
                            onClick={() => onViewResults(repository_id)}
                            className="mt-3 w-full py-2 text-xs font-medium text-emerald-400 bg-emerald-500/10 hover:bg-emerald-500/20 rounded-lg transition-colors"
                        >
                            View Results
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
}

// Container component that manages multiple toasts
export function ScanProgressToastContainer({
    messages,
    onViewResults
}: {
    messages: WSMessage[];
    onViewResults?: (repoId: string) => void;
}) {
    const [visibleMessages, setVisibleMessages] = useState<WSMessage[]>([]);

    useEffect(() => {
        // Only show scan-related messages
        const scanMessages = messages.filter(m =>
            ["scan_started", "scan_progress", "scan_completed", "scan_failed"].includes(m.type)
        );

        // Keep only the most recent message per repository
        const byRepo = new Map<string, WSMessage>();
        scanMessages.forEach(m => {
            if (m.repository_id) {
                byRepo.set(m.repository_id, m);
            }
        });

        setVisibleMessages(Array.from(byRepo.values()));
    }, [messages]);

    const dismissMessage = (repoId: string | undefined) => {
        if (repoId) {
            setVisibleMessages(prev => prev.filter(m => m.repository_id !== repoId));
        }
    };

    return (
        <>
            {visibleMessages.map((msg, idx) => (
                <div
                    key={msg.repository_id || idx}
                    style={{ bottom: `${1.5 + idx * 6}rem` }}
                    className="fixed right-6 z-50"
                >
                    <ScanProgressToast
                        message={msg}
                        onDismiss={() => dismissMessage(msg.repository_id)}
                        onViewResults={onViewResults}
                    />
                </div>
            ))}
        </>
    );
}
