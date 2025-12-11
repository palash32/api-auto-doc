"use client";

import React, { useRef, useEffect } from "react";
import gsap from "gsap";
import { cn } from "@/lib/utils";

interface MagneticButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
    children: React.ReactNode;
    strength?: number; // How strong the magnetic pull is (default: 0.3)
    variant?: "primary" | "secondary" | "ghost" | "glass";
}

export const MagneticButton = ({
    children,
    className,
    strength = 0.3,
    variant = "primary",
    ...props
}: MagneticButtonProps) => {
    const buttonRef = useRef<HTMLButtonElement>(null);

    useEffect(() => {
        const button = buttonRef.current;
        if (!button) return;

        const handleMouseMove = (e: MouseEvent) => {
            const { clientX, clientY } = e;
            const { left, top, width, height } = button.getBoundingClientRect();

            const x = clientX - (left + width / 2);
            const y = clientY - (top + height / 2);

            gsap.to(button, {
                x: x * strength,
                y: y * strength,
                duration: 0.6,
                ease: "power3.out",
            });
        };

        const handleMouseLeave = () => {
            gsap.to(button, {
                x: 0,
                y: 0,
                duration: 0.8,
                ease: "elastic.out(1, 0.3)",
            });
        };

        button.addEventListener("mousemove", handleMouseMove);
        button.addEventListener("mouseleave", handleMouseLeave);

        return () => {
            button.removeEventListener("mousemove", handleMouseMove);
            button.removeEventListener("mouseleave", handleMouseLeave);
        };
    }, [strength]);

    const variants = {
        primary: "bg-[#0071E3] text-white hover:shadow-[0_0_20px_rgba(0,113,227,0.4)] border-transparent",
        secondary: "bg-white/10 text-white hover:bg-white/20 border-white/10 backdrop-blur-md",
        ghost: "bg-transparent text-white hover:bg-white/5 border-transparent",
        glass: "bg-white/5 text-white border border-white/10 backdrop-blur-xl hover:bg-white/10 shadow-lg",
    };

    return (
        <button
            ref={buttonRef}
            className={cn(
                "relative px-6 py-3 rounded-full font-medium transition-colors border flex items-center",
                variants[variant],
                className
            )}
            {...props}
        >
            <span className="relative z-10 flex items-center justify-center gap-2 w-full">{children}</span>
        </button>
    );
};
