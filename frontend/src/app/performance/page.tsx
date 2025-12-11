"use client";

import React, { useState, useEffect } from "react";
import {
    Gauge,
    Database,
    Zap,
    Clock,
    Server,
    BarChart3,
    RefreshCw,
    Trash2,
    Shield
} from "lucide-react";
import { cn } from "@/lib/utils";
import { GlassCard } from "@/components/ui/glass-card";

interface PerformanceStats {
    avg_api_latency_ms: number;
    cache_hit_rate: number;
    queue_depth: number;
    active_workers: number;
}

interface RateLimitStatus {
    tier: string;
    minute_used: number;
    minute_limit: number;
    hour_used: number;
    hour_limit: number;
    day_used: number;
    day_limit: number;
}

interface QueueStats {
    pending: number;
    processing: number;
    completed: number;
    failed: number;
    total: number;
}

interface CacheStats {
    total_entries: number;
    total_size_mb: number;
    entries_by_type: Array<{
        type: string;
        count: number;
        total_size_mb: number;
        total_hits: number;
    }>;
}

export default function PerformancePage() {
    const [stats, setStats] = useState<PerformanceStats | null>(null);
    const [rateLimits, setRateLimits] = useState<RateLimitStatus | null>(null);
    const [queueStats, setQueueStats] = useState<QueueStats | null>(null);
    const [cacheStats, setCacheStats] = useState<CacheStats | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 30000);
        return () => clearInterval(interval);
    }, []);

    const fetchData = async () => {
        try {
            const [statsRes, rateRes, queueRes, cacheRes] = await Promise.all([
                fetch("http://localhost:8000/api/performance/dashboard"),
                fetch("http://localhost:8000/api/performance/rate-limits/status"),
                fetch("http://localhost:8000/api/performance/queue/stats"),
                fetch("http://localhost:8000/api/performance/cache/stats")
            ]);

            if (statsRes.ok) setStats(await statsRes.json());
            if (rateRes.ok) setRateLimits(await rateRes.json());
            if (queueRes.ok) setQueueStats(await queueRes.json());
            if (cacheRes.ok) setCacheStats(await cacheRes.json());
        } catch (e) {
            console.error("Failed to fetch performance data:", e);
        } finally {
            setLoading(false);
        }
    };

    const clearCache = async () => {
        try {
            await fetch("http://localhost:8000/api/performance/cache/clear", {
                method: "POST"
            });
            fetchData();
        } catch (e) {
            console.error("Failed to clear cache:", e);
        }
    };

    const getPercentage = (used: number, limit: number) => {
        return Math.min((used / limit) * 100, 100);
    };

    const getColorClass = (percentage: number) => {
        if (percentage >= 90) return "bg-red-500";
        if (percentage >= 70) return "bg-amber-500";
        return "bg-emerald-500";
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-[#0a0a0a] flex items-center justify-center">
                <div className="w-8 h-8 border-4 border-cyan-500 border-t-transparent rounded-full animate-spin" />
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-[#0a0a0a] text-white">
            <header className="border-b border-white/10 bg-black/50 backdrop-blur-sm sticky top-0 z-50">
                <div className="max-w-6xl mx-auto px-6 py-4">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-teal-600 flex items-center justify-center">
                                <Gauge size={20} />
                            </div>
                            <div>
                                <h1 className="text-xl font-semibold">Performance</h1>
                                <p className="text-xs text-gray-500">CDN, caching, rate limits, queue</p>
                            </div>
                        </div>
                        <button
                            onClick={fetchData}
                            className="p-2 hover:bg-white/10 rounded-lg text-gray-400 hover:text-white"
                        >
                            <RefreshCw size={18} />
                        </button>
                    </div>
                </div>
            </header>

            <div className="max-w-6xl mx-auto p-6 space-y-6">
                {/* Main Stats */}
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                    <GlassCard className="p-4">
                        <div className="flex items-center gap-2 text-gray-400 mb-2">
                            <Zap size={14} />
                            <span className="text-xs">API Latency</span>
                        </div>
                        <p className="text-2xl font-bold">
                            {stats?.avg_api_latency_ms.toFixed(0)}
                            <span className="text-sm font-normal text-gray-500 ml-1">ms</span>
                        </p>
                    </GlassCard>

                    <GlassCard className="p-4">
                        <div className="flex items-center gap-2 text-gray-400 mb-2">
                            <Database size={14} />
                            <span className="text-xs">Cache Hit Rate</span>
                        </div>
                        <p className="text-2xl font-bold">
                            {stats?.cache_hit_rate.toFixed(1)}
                            <span className="text-sm font-normal text-gray-500 ml-1">%</span>
                        </p>
                    </GlassCard>

                    <GlassCard className="p-4">
                        <div className="flex items-center gap-2 text-gray-400 mb-2">
                            <Clock size={14} />
                            <span className="text-xs">Queue Depth</span>
                        </div>
                        <p className="text-2xl font-bold">{stats?.queue_depth}</p>
                    </GlassCard>

                    <GlassCard className="p-4">
                        <div className="flex items-center gap-2 text-gray-400 mb-2">
                            <Server size={14} />
                            <span className="text-xs">Active Workers</span>
                        </div>
                        <p className="text-2xl font-bold">{stats?.active_workers}</p>
                    </GlassCard>
                </div>

                {/* Rate Limits */}
                <GlassCard className="p-6">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="text-sm font-medium flex items-center gap-2">
                            <Shield size={14} className="text-blue-400" />
                            Rate Limits
                        </h3>
                        <span className="text-xs px-2 py-1 bg-blue-500/10 text-blue-400 rounded capitalize">
                            {rateLimits?.tier || "free"} tier
                        </span>
                    </div>

                    <div className="grid grid-cols-3 gap-4">
                        {[
                            { label: "Per Minute", used: rateLimits?.minute_used || 0, limit: rateLimits?.minute_limit || 60 },
                            { label: "Per Hour", used: rateLimits?.hour_used || 0, limit: rateLimits?.hour_limit || 1000 },
                            { label: "Per Day", used: rateLimits?.day_used || 0, limit: rateLimits?.day_limit || 10000 }
                        ].map((item) => {
                            const pct = getPercentage(item.used, item.limit);
                            return (
                                <div key={item.label}>
                                    <div className="flex justify-between text-xs mb-1">
                                        <span className="text-gray-400">{item.label}</span>
                                        <span>{item.used} / {item.limit}</span>
                                    </div>
                                    <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                                        <div
                                            className={cn("h-full transition-all", getColorClass(pct))}
                                            style={{ width: `${pct}%` }}
                                        />
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </GlassCard>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Queue Stats */}
                    <GlassCard className="p-6">
                        <h3 className="text-sm font-medium mb-4 flex items-center gap-2">
                            <BarChart3 size={14} className="text-purple-400" />
                            Build Queue
                        </h3>

                        <div className="grid grid-cols-2 gap-3">
                            {[
                                { label: "Pending", value: queueStats?.pending || 0, color: "text-amber-400" },
                                { label: "Processing", value: queueStats?.processing || 0, color: "text-blue-400" },
                                { label: "Completed", value: queueStats?.completed || 0, color: "text-emerald-400" },
                                { label: "Failed", value: queueStats?.failed || 0, color: "text-red-400" }
                            ].map((item) => (
                                <div key={item.label} className="p-3 rounded-lg bg-white/5">
                                    <p className="text-xs text-gray-400">{item.label}</p>
                                    <p className={cn("text-xl font-bold", item.color)}>{item.value}</p>
                                </div>
                            ))}
                        </div>
                    </GlassCard>

                    {/* Cache Stats */}
                    <GlassCard className="p-6">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-sm font-medium flex items-center gap-2">
                                <Database size={14} className="text-cyan-400" />
                                Cache
                            </h3>
                            <button
                                onClick={clearCache}
                                className="text-xs px-2 py-1 bg-red-500/10 hover:bg-red-500/20 text-red-400 rounded flex items-center gap-1"
                            >
                                <Trash2 size={12} />
                                Clear
                            </button>
                        </div>

                        <div className="flex items-center gap-4 mb-4">
                            <div>
                                <p className="text-xs text-gray-400">Entries</p>
                                <p className="text-xl font-bold">{cacheStats?.total_entries || 0}</p>
                            </div>
                            <div>
                                <p className="text-xs text-gray-400">Size</p>
                                <p className="text-xl font-bold">{cacheStats?.total_size_mb || 0} MB</p>
                            </div>
                        </div>

                        {cacheStats?.entries_by_type && cacheStats.entries_by_type.length > 0 ? (
                            <div className="space-y-2">
                                {cacheStats.entries_by_type.map((entry) => (
                                    <div key={entry.type} className="p-2 rounded bg-white/5 flex justify-between text-sm">
                                        <span className="text-gray-400">{entry.type}</span>
                                        <span>{entry.count} entries • {entry.total_hits} hits</span>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <p className="text-sm text-gray-500 text-center py-2">No cache entries</p>
                        )}
                    </GlassCard>
                </div>
            </div>
        </div>
    );
}
