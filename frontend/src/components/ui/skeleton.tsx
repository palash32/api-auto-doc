"use client";

import React from "react";
import { cn } from "@/lib/utils";

/**
 * Base Skeleton component with shimmer animation
 */
export const Skeleton = React.forwardRef<
    HTMLDivElement,
    React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => {
    return (
        <div
            ref={ref}
            className={cn(
                "relative overflow-hidden rounded-md bg-white/10",
                "before:absolute before:inset-0 before:-translate-x-full",
                "before:animate-shimmer before:bg-gradient-to-r",
                "before:from-transparent before:via-white/10 before:to-transparent",
                className
            )}
            {...props}
        />
    );
});
Skeleton.displayName = "Skeleton";

/**
 * Skeleton for text lines
 */
export const SkeletonText = ({
    lines = 1,
    className,
}: {
    lines?: number;
    className?: string;
}) => {
    return (
        <div className={cn("space-y-2", className)}>
            {Array.from({ length: lines }).map((_, i) => (
                <Skeleton
                    key={i}
                    className={cn(
                        "h-4",
                        i === lines - 1 && lines > 1 ? "w-3/4" : "w-full"
                    )}
                />
            ))}
        </div>
    );
};

/**
 * Skeleton for repository cards on dashboard
 */
export const SkeletonCard = ({ className }: { className?: string }) => {
    return (
        <div
            className={cn(
                "p-5 rounded-xl border border-white/10 bg-white/5 backdrop-blur-sm",
                className
            )}
        >
            {/* Header */}
            <div className="flex justify-between items-start mb-4">
                <div className="flex items-center gap-3">
                    <Skeleton className="w-10 h-10 rounded-lg" />
                    <div className="space-y-2">
                        <Skeleton className="h-4 w-32" />
                        <Skeleton className="h-3 w-24" />
                    </div>
                </div>
                <Skeleton className="h-6 w-16 rounded-full" />
            </div>

            {/* Stats */}
            <div className="flex gap-4 mb-4">
                <Skeleton className="h-4 w-20" />
                <Skeleton className="h-4 w-24" />
            </div>

            {/* Progress bar */}
            <Skeleton className="h-1.5 w-full rounded-full" />
        </div>
    );
};

/**
 * Skeleton for stat cards
 */
export const SkeletonStatCard = ({ className }: { className?: string }) => {
    return (
        <div
            className={cn(
                "p-6 rounded-xl border border-white/10 bg-white/5 backdrop-blur-sm",
                className
            )}
        >
            <Skeleton className="h-4 w-24 mb-3" />
            <div className="flex items-end justify-between">
                <Skeleton className="h-8 w-16" />
                <Skeleton className="h-6 w-12 rounded-full" />
            </div>
            <Skeleton className="h-1 w-full mt-4 rounded-full" />
        </div>
    );
};

/**
 * Skeleton for endpoint table rows
 */
export const SkeletonTableRow = ({ className }: { className?: string }) => {
    return (
        <div
            className={cn(
                "flex items-center gap-4 p-4 border-b border-white/5",
                className
            )}
        >
            <Skeleton className="h-6 w-16 rounded" />
            <Skeleton className="h-4 w-48 flex-1" />
            <Skeleton className="h-4 w-32" />
            <Skeleton className="h-6 w-20 rounded-full" />
        </div>
    );
};

/**
 * Skeleton for endpoint table
 */
export const SkeletonTable = ({
    rows = 5,
    className,
}: {
    rows?: number;
    className?: string;
}) => {
    return (
        <div className={cn("rounded-xl border border-white/10 bg-white/5 overflow-hidden", className)}>
            {/* Table header */}
            <div className="flex items-center gap-4 p-4 border-b border-white/10 bg-white/5">
                <Skeleton className="h-4 w-16" />
                <Skeleton className="h-4 w-24" />
                <Skeleton className="h-4 w-32 flex-1" />
                <Skeleton className="h-4 w-20" />
            </div>
            {/* Table rows */}
            {Array.from({ length: rows }).map((_, i) => (
                <SkeletonTableRow key={i} />
            ))}
        </div>
    );
};

/**
 * Skeleton for activity feed items
 */
export const SkeletonActivityItem = ({ className }: { className?: string }) => {
    return (
        <div
            className={cn(
                "flex items-start gap-3 p-3 rounded-lg border border-white/5 bg-white/5",
                className
            )}
        >
            <Skeleton className="w-7 h-7 rounded-full flex-shrink-0" />
            <div className="flex-1 space-y-2">
                <div className="flex justify-between">
                    <Skeleton className="h-4 w-24" />
                    <Skeleton className="h-3 w-12" />
                </div>
                <Skeleton className="h-3 w-32" />
            </div>
        </div>
    );
};

/**
 * Skeleton for activity feed
 */
export const SkeletonActivityFeed = ({
    items = 4,
    className,
}: {
    items?: number;
    className?: string;
}) => {
    return (
        <div className={cn("space-y-3", className)}>
            <div className="flex items-center gap-2 mb-2">
                <Skeleton className="h-4 w-4 rounded" />
                <Skeleton className="h-4 w-24" />
            </div>
            {Array.from({ length: items }).map((_, i) => (
                <SkeletonActivityItem key={i} />
            ))}
        </div>
    );
};

// Legacy exports for backward compatibility
export function SkeletonRow() {
    return <SkeletonTableRow />;
}

