"use client";

import React from "react";
import { cn } from "@/lib/utils";

interface MagneticButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
    children: React.ReactNode;
    strength?: number; // Kept for API compatibility, but no longer used
    variant?: "primary" | "secondary" | "ghost" | "glass";
}

export const MagneticButton = ({
    children,
    className,
    strength: _strength = 0.3, // Unused - kept for backwards compatibility
    variant = "primary",
    ...props
}: MagneticButtonProps) => {
    const variants = {
        primary: "bg-[#0071E3] text-white hover:shadow-[0_0_20px_rgba(0,113,227,0.4)] border-transparent hover:bg-[#0077ED]",
        secondary: "bg-white/10 text-white hover:bg-white/20 border-white/10 backdrop-blur-md",
        ghost: "bg-transparent text-white hover:bg-white/5 border-transparent",
        glass: "bg-white/5 text-white border border-white/10 backdrop-blur-xl hover:bg-white/10 shadow-lg",
    };

    return (
        <button
            className={cn(
                "relative px-6 py-3 rounded-full font-medium transition-all duration-200 border flex items-center",
                variants[variant],
                className
            )}
            {...props}
        >
            <span className="relative z-10 flex items-center justify-center gap-2 w-full">{children}</span>
        </button>
    );
};
