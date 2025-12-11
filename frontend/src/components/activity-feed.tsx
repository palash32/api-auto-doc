"use client";

import React, { useState, useEffect } from "react";
import { GitBranch, Check, Clock, AlertCircle, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

export interface ActivityItem {
    id: string;
    type: "scan_started" | "scan_completed" | "scan_failed" | "repo_added" | "docs_generated";
    title: string;
    description: string;
    timestamp: Date;
    status?: "success" | "pending" | "failed";
    metadata?: {
        endpointCount?: number;
        repoName?: string;
    };
}

interface ActivityFeedProps {
    activities: ActivityItem[];
    className?: string;
    maxItems?: number;
}

const getActivityIcon = (type: ActivityItem["type"], status?: ActivityItem["status"]) => {
    switch (type) {
        case "scan_started":
            return <Loader2 size={14} className="text-blue-400 animate-spin" />;
        case "scan_completed":
            return <Check size={14} className="text-emerald-400" />;
        case "scan_failed":
            return <AlertCircle size={14} className="text-red-400" />;
        case "repo_added":
            return <GitBranch size={14} className="text-purple-400" />;
        case "docs_generated":
            return <Check size={14} className="text-cyan-400" />;
        default:
            return <Clock size={14} className="text-gray-400" />;
    }
};

const getStatusColor = (status?: ActivityItem["status"]) => {
    switch (status) {
        case "success":
            return "bg-emerald-500/20 border-emerald-500/30";
        case "pending":
            return "bg-blue-500/20 border-blue-500/30";
        case "failed":
            return "bg-red-500/20 border-red-500/30";
        default:
            return "bg-white/5 border-white/10";
    }
};

const formatTimeAgo = (date: Date): string => {
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return "Just now";
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
};

export const ActivityFeed: React.FC<ActivityFeedProps> = ({
    activities,
    className,
    maxItems = 5
}) => {
    const [mounted, setMounted] = useState(false);

    useEffect(() => {
        setMounted(true);
    }, []);

    const displayActivities = activities.slice(0, maxItems);

    if (displayActivities.length === 0) {
        return (
            <div className={cn("p-6 text-center", className)}>
                <div className="w-12 h-12 rounded-full bg-white/5 flex items-center justify-center mx-auto mb-3">
                    <Clock size={20} className="text-gray-500" />
                </div>
                <p className="text-sm text-gray-400">No recent activity</p>
                <p className="text-xs text-gray-500 mt-1">Add a repository to get started</p>
            </div>
        );
    }

    return (
        <div className={cn("space-y-3", className)}>
            <h3 className="text-sm font-medium text-white/80 flex items-center gap-2">
                <Clock size={14} className="text-blue-400" />
                Recent Activity
            </h3>
            <div className="space-y-2">
                {displayActivities.map((activity, idx) => (
                    <div
                        key={activity.id}
                        className={cn(
                            "p-3 rounded-lg border transition-all duration-300 hover:bg-white/5",
                            getStatusColor(activity.status),
                            "animate-fade-in-up"
                        )}
                        style={{ animationDelay: `${idx * 0.05}s` }}
                    >
                        <div className="flex items-start gap-3">
                            <div className={cn(
                                "w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0",
                                getStatusColor(activity.status)
                            )}>
                                {getActivityIcon(activity.type, activity.status)}
                            </div>
                            <div className="flex-1 min-w-0">
                                <div className="flex items-center justify-between gap-2">
                                    <p className="text-sm font-medium text-white truncate">
                                        {activity.title}
                                    </p>
                                    <span
                                        className="text-[10px] text-gray-500 whitespace-nowrap"
                                        suppressHydrationWarning
                                    >
                                        {mounted ? formatTimeAgo(activity.timestamp) : ''}
                                    </span>
                                </div>
                                <p className="text-xs text-gray-400 mt-0.5 truncate">
                                    {activity.description}
                                </p>
                                {activity.metadata?.endpointCount && (
                                    <div className="mt-2 flex items-center gap-1">
                                        <span className="px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400 text-[10px] font-medium">
                                            {activity.metadata.endpointCount} endpoints
                                        </span>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                ))}
            </div>
            {activities.length > maxItems && (
                <button className="w-full text-center text-xs text-blue-400 hover:text-blue-300 transition-colors py-2">
                    View all activity →
                </button>
            )}
        </div>
    );
};

// Demo data for testing - using fixed offsets for consistent timestamps
const createDemoTimestamp = (minutesAgo: number) => new Date(Date.now() - minutesAgo * 60000);

export const DEMO_ACTIVITIES: ActivityItem[] = [
    {
        id: "1",
        type: "scan_completed",
        title: "Scan completed",
        description: "api-autodoc-platform",
        timestamp: createDemoTimestamp(5),
        status: "success",
        metadata: { endpointCount: 12 }
    },
    {
        id: "2",
        type: "docs_generated",
        title: "Docs generated",
        description: "AI documentation ready for payment-service",
        timestamp: createDemoTimestamp(30),
        status: "success"
    },
    {
        id: "3",
        type: "scan_started",
        title: "Scanning...",
        description: "user-management-api",
        timestamp: createDemoTimestamp(2),
        status: "pending"
    },
    {
        id: "4",
        type: "repo_added",
        title: "Repository connected",
        description: "github.com/company/auth-service",
        timestamp: createDemoTimestamp(120),
        status: "success"
    },
    {
        id: "5",
        type: "scan_failed",
        title: "Scan failed",
        description: "Could not parse legacy-api",
        timestamp: createDemoTimestamp(1440),
        status: "failed"
    }
];
