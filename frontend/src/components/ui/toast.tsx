"use client";

import React, { useEffect, useRef } from "react";
import { useToastStore, Toast } from "@/lib/store";
import { X, CheckCircle2, AlertCircle, Info, AlertTriangle } from "lucide-react";
import { cn } from "@/lib/utils";
import gsap from "gsap";
import { useGSAP } from "@gsap/react";

const ToastItem = ({ toast }: { toast: Toast }) => {
    const removeToast = useToastStore((state) => state.removeToast);
    const elRef = useRef<HTMLDivElement>(null);

    useGSAP(() => {
        // Entry animation
        gsap.fromTo(elRef.current,
            { x: 100, opacity: 0, scale: 0.9 },
            { x: 0, opacity: 1, scale: 1, duration: 0.4, ease: "back.out(1.7)" }
        );
    }, { scope: elRef });

    const handleRemove = () => {
        // Exit animation
        gsap.to(elRef.current, {
            x: 50,
            opacity: 0,
            scale: 0.9,
            duration: 0.3,
            onComplete: () => removeToast(toast.id)
        });
    };

    const icons = {
        success: <CheckCircle2 size={18} className="text-emerald-400" />,
        error: <AlertCircle size={18} className="text-red-400" />,
        warning: <AlertTriangle size={18} className="text-yellow-400" />,
        info: <Info size={18} className="text-blue-400" />,
    };

    const borders = {
        success: "border-emerald-500/20 bg-emerald-500/10",
        error: "border-red-500/20 bg-red-500/10",
        warning: "border-yellow-500/20 bg-yellow-500/10",
        info: "border-blue-500/20 bg-blue-500/10",
    };

    return (
        <div
            ref={elRef}
            className={cn(
                "pointer-events-auto flex w-full max-w-md items-center gap-3 rounded-xl border p-4 shadow-lg backdrop-blur-xl transition-all",
                borders[toast.type]
            )}
        >
            <div className="flex-shrink-0">{icons[toast.type]}</div>
            <p className="flex-1 text-sm font-medium text-white">{toast.message}</p>
            <button
                onClick={handleRemove}
                className="flex-shrink-0 rounded-lg p-1 text-white/50 hover:bg-white/10 hover:text-white transition-colors"
            >
                <X size={16} />
            </button>
        </div>
    );
};

export const ToastContainer = () => {
    const toasts = useToastStore((state) => state.toasts);

    return (
        <div className="fixed bottom-6 right-6 z-[100] flex flex-col gap-3 pointer-events-none">
            {toasts.map((toast) => (
                <ToastItem key={toast.id} toast={toast} />
            ))}
        </div>
    );
};
