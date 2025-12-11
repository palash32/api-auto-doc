"use client";

import React, { createContext, useContext, useState, useCallback } from "react";
import { X, CheckCircle, AlertCircle, Info, AlertTriangle } from "lucide-react";
import { cn } from "@/lib/utils";

type ToastType = "success" | "error" | "info" | "warning";

interface Toast {
    id: string;
    message: string;
    type: ToastType;
}

interface ToastContextType {
    showToast: (message: string, type?: ToastType) => void;
    success: (message: string) => void;
    error: (message: string) => void;
    info: (message: string) => void;
    warning: (message: string) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export function ToastProvider({ children }: { children: React.ReactNode }) {
    const [toasts, setToasts] = useState<Toast[]>([]);

    const showToast = useCallback((message: string, type: ToastType = "info") => {
        const id = Math.random().toString(36).slice(2);
        setToasts((prev) => [...prev, { id, message, type }]);

        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            setToasts((prev) => prev.filter((t) => t.id !== id));
        }, 5000);
    }, []);

    const success = useCallback((message: string) => showToast(message, "success"), [showToast]);
    const error = useCallback((message: string) => showToast(message, "error"), [showToast]);
    const info = useCallback((message: string) => showToast(message, "info"), [showToast]);
    const warning = useCallback((message: string) => showToast(message, "warning"), [showToast]);

    const removeToast = (id: string) => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
    };

    return (
        <ToastContext.Provider value={{ showToast, success, error, info, warning }}>
            {children}

            {/* Toast Container */}
            <div className="fixed bottom-4 right-4 z-50 space-y-2">
                {toasts.map((toast) => (
                    <ToastItem key={toast.id} toast={toast} onClose={() => removeToast(toast.id)} />
                ))}
            </div>
        </ToastContext.Provider>
    );
}

function ToastItem({ toast, onClose }: { toast: Toast; onClose: () => void }) {
    const icons = {
        success: <CheckCircle className="w-5 h-5" />,
        error: <AlertCircle className="w-5 h-5" />,
        info: <Info className="w-5 h-5" />,
        warning: <AlertTriangle className="w-5 h-5" />,
    };

    const styles = {
        success: "bg-emerald-500/10 border-emerald-500/20 text-emerald-400",
        error: "bg-red-500/10 border-red-500/20 text-red-400",
        info: "bg-blue-500/10 border-blue-500/20 text-blue-400",
        warning: "bg-yellow-500/10 border-yellow-500/20 text-yellow-400",
    };

    return (
        <div
            className={cn(
                "flex items-center gap-3 px-4 py-3 rounded-lg border backdrop-blur-sm min-w-[300px] animate-in slide-in-from-bottom-5",
                styles[toast.type]
            )}
        >
            {icons[toast.type]}
            <p className="flex-1 text-sm font-medium">{toast.message}</p>
            <button
                onClick={onClose}
                className="opacity-70 hover:opacity-100 transition-opacity"
            >
                <X className="w-4 h-4" />
            </button>
        </div>
    );
}

export function useToast() {
    const context = useContext(ToastContext);
    if (!context) {
        throw new Error("useToast must be used within ToastProvider");
    }
    return context;
}
