"use client";

import React, { useRef, useEffect } from "react";
import gsap from "gsap";
import { cn } from "@/lib/utils";

interface GlassCardProps extends React.HTMLAttributes<HTMLDivElement> {
    children: React.ReactNode;
    hoverEffect?: boolean;
    tiltEffect?: boolean;
}

export const GlassCard = ({
    children,
    className,
    hoverEffect = true,
    tiltEffect = false,
    ...props
}: GlassCardProps) => {
    const cardRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (!tiltEffect || !cardRef.current) return;

        const card = cardRef.current;

        const handleMouseMove = (e: MouseEvent) => {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;

            const centerX = rect.width / 2;
            const centerY = rect.height / 2;

            const rotateX = ((y - centerY) / centerY) * -5; // Max 5deg rotation
            const rotateY = ((x - centerX) / centerX) * 5;

            gsap.to(card, {
                rotationX: rotateX,
                rotationY: rotateY,
                duration: 0.4,
                ease: "power2.out",
                transformPerspective: 1000,
            });
        };

        const handleMouseLeave = () => {
            gsap.to(card, {
                rotationX: 0,
                rotationY: 0,
                duration: 0.7,
                ease: "elastic.out(1, 0.5)",
            });
        };

        card.addEventListener("mousemove", handleMouseMove);
        card.addEventListener("mouseleave", handleMouseLeave);

        return () => {
            card.removeEventListener("mousemove", handleMouseMove);
            card.removeEventListener("mouseleave", handleMouseLeave);
        };
    }, [tiltEffect]);

    return (
        <div
            ref={cardRef}
            className={cn(
                "relative overflow-hidden rounded-2xl border border-white/10 bg-white/5 backdrop-blur-xl p-6 transition-all duration-300",
                hoverEffect && "hover:bg-white/10 hover:border-white/20 hover:shadow-[0_8px_32px_rgba(0,0,0,0.2)]",
                className
            )}
            {...props}
        >
            {/* Gradient Glow Effect */}
            <div className="pointer-events-none absolute -inset-px opacity-0 transition-opacity duration-300 group-hover:opacity-100"
                style={{
                    background: "radial-gradient(600px circle at var(--mouse-x) var(--mouse-y), rgba(255,255,255,0.06), transparent 40%)"
                }}
            />
            <div className="relative z-10">{children}</div>
        </div>
    );
};
