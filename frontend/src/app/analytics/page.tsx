"use client";

import React, { useState, useEffect } from "react";
import {
    BarChart3,
    TrendingUp,
    TrendingDown,
    Eye,
    Users,
    Activity,
    Heart,
    Clock,
    AlertTriangle,
    RefreshCw,
    Calendar
} from "lucide-react";
import { cn } from "@/lib/utils";
import { API_BASE_URL } from "@/lib/api";
import { GlassCard } from "@/components/ui/glass-card";

interface DashboardSummary {
    total_views: number;
    unique_visitors: number;
    total_endpoints: number;
    avg_health_score: number;
    playground_requests: number;
    avg_latency_ms: number | null;
    views_trend: number;
    top_endpoints: TopEndpoint[];
}

interface TopEndpoint {
    endpoint_id: string;
    path: string;
    method: string;
    view_count: number;
    repository_name: string | null;
}

interface HealthScore {
    repository_id: string;
    repository_name: string;
    health_score: number;
    description_coverage: number;
    parameter_coverage: number;
    example_coverage: number;
    total_endpoints: number;
    undocumented_endpoints: number;
}

const METHOD_COLORS: Record<string, string> = {
    GET: "bg-emerald-500/10 text-emerald-400",
    POST: "bg-blue-500/10 text-blue-400",
    PUT: "bg-amber-500/10 text-amber-400",
    PATCH: "bg-purple-500/10 text-purple-400",
    DELETE: "bg-red-500/10 text-red-400"
};

export default function AnalyticsDashboard() {
    const [summary, setSummary] = useState<DashboardSummary | null>(null);
    const [healthScores, setHealthScores] = useState<HealthScore[]>([]);
    const [loading, setLoading] = useState(true);
    const [timeRange, setTimeRange] = useState(7);

    useEffect(() => {
        fetchData();
    }, [timeRange]);

    const fetchData = async () => {
        setLoading(true);
        try {
            const [summaryRes, healthRes] = await Promise.all([
                fetch(`${API_BASE_URL}/api/analytics/dashboard?days=${timeRange}`),
                fetch(`${API_BASE_URL}/api/analytics/health`)
            ]);

            if (summaryRes.ok) {
                setSummary(await summaryRes.json());
            }
            if (healthRes.ok) {
                setHealthScores(await healthRes.json());
            }
        } catch (e) {
            console.error("Failed to fetch analytics:", e);
        } finally {
            setLoading(false);
        }
    };

    const getHealthColor = (score: number) => {
        if (score >= 80) return "text-emerald-400";
        if (score >= 60) return "text-amber-400";
        return "text-red-400";
    };

    const getHealthBg = (score: number) => {
        if (score >= 80) return "bg-emerald-500/10";
        if (score >= 60) return "bg-amber-500/10";
        return "bg-red-500/10";
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-[#0a0a0a] flex items-center justify-center">
                <div className="w-8 h-8 border-4 border-purple-500 border-t-transparent rounded-full animate-spin" />
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-[#0a0a0a] text-white">
            {/* Header */}
            <header className="border-b border-white/10 bg-black/50 backdrop-blur-sm sticky top-0 z-50">
                <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-cyan-600 flex items-center justify-center">
                            <BarChart3 size={20} />
                        </div>
                        <div>
                            <h1 className="text-xl font-semibold">Analytics</h1>
                            <p className="text-xs text-gray-500">Documentation insights & metrics</p>
                        </div>
                    </div>

                    <div className="flex items-center gap-3">
                        <select
                            value={timeRange}
                            onChange={(e) => setTimeRange(Number(e.target.value))}
                            className="px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-sm focus:outline-none"
                        >
                            <option value={7}>Last 7 days</option>
                            <option value={14}>Last 14 days</option>
                            <option value={30}>Last 30 days</option>
                            <option value={90}>Last 90 days</option>
                        </select>
                        <button
                            onClick={fetchData}
                            className="p-2 hover:bg-white/10 rounded-lg transition-colors"
                        >
                            <RefreshCw size={18} className="text-gray-400" />
                        </button>
                    </div>
                </div>
            </header>

            <div className="max-w-7xl mx-auto p-6">
                {/* Summary Cards */}
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
                    <StatCard
                        icon={Eye}
                        label="Total Views"
                        value={summary?.total_views.toLocaleString() || "0"}
                        trend={summary?.views_trend}
                        color="blue"
                    />
                    <StatCard
                        icon={Users}
                        label="Unique Visitors"
                        value={summary?.unique_visitors.toLocaleString() || "0"}
                        color="purple"
                    />
                    <StatCard
                        icon={Activity}
                        label="API Endpoints"
                        value={summary?.total_endpoints.toLocaleString() || "0"}
                        color="emerald"
                    />
                    <StatCard
                        icon={Heart}
                        label="Avg Health Score"
                        value={`${summary?.avg_health_score || 0}%`}
                        color="pink"
                    />
                </div>

                {/* Secondary Stats */}
                <div className="grid grid-cols-2 gap-4 mb-8">
                    <StatCard
                        icon={Activity}
                        label="Playground Requests"
                        value={summary?.playground_requests.toLocaleString() || "0"}
                        color="cyan"
                        small
                    />
                    <StatCard
                        icon={Clock}
                        label="Avg API Latency"
                        value={summary?.avg_latency_ms ? `${summary.avg_latency_ms}ms` : "N/A"}
                        color="amber"
                        small
                    />
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Top Endpoints */}
                    <GlassCard className="p-6">
                        <h3 className="text-sm font-medium mb-4 flex items-center gap-2">
                            <TrendingUp size={14} className="text-emerald-400" />
                            Most Viewed Endpoints
                        </h3>

                        <div className="space-y-2">
                            {summary?.top_endpoints.length === 0 ? (
                                <p className="text-sm text-gray-500 text-center py-4">
                                    No data yet. Views will appear here.
                                </p>
                            ) : (
                                summary?.top_endpoints.map((ep, idx) => (
                                    <div
                                        key={ep.endpoint_id}
                                        className="flex items-center gap-3 p-3 rounded-lg bg-white/5 hover:bg-white/10 transition-colors"
                                    >
                                        <span className="text-xs text-gray-500 w-5">#{idx + 1}</span>
                                        <span className={cn(
                                            "text-[10px] font-bold px-1.5 py-0.5 rounded",
                                            METHOD_COLORS[ep.method] || "bg-gray-500/10 text-gray-400"
                                        )}>
                                            {ep.method}
                                        </span>
                                        <span className="flex-1 font-mono text-sm truncate">{ep.path}</span>
                                        <span className="text-xs text-gray-400">{ep.view_count} views</span>
                                    </div>
                                ))
                            )}
                        </div>
                    </GlassCard>

                    {/* Health Scores */}
                    <GlassCard className="p-6">
                        <h3 className="text-sm font-medium mb-4 flex items-center gap-2">
                            <Heart size={14} className="text-pink-400" />
                            Documentation Health
                        </h3>

                        <div className="space-y-3">
                            {healthScores.length === 0 ? (
                                <p className="text-sm text-gray-500 text-center py-4">
                                    No health scores calculated yet.
                                </p>
                            ) : (
                                healthScores.map((repo) => (
                                    <div key={repo.repository_id} className="p-3 rounded-lg bg-white/5">
                                        <div className="flex items-center justify-between mb-2">
                                            <span className="font-medium text-sm">{repo.repository_name}</span>
                                            <span className={cn(
                                                "text-lg font-bold",
                                                getHealthColor(repo.health_score)
                                            )}>
                                                {repo.health_score}%
                                            </span>
                                        </div>

                                        {/* Health bar */}
                                        <div className="h-2 rounded-full bg-white/5 overflow-hidden mb-2">
                                            <div
                                                className={cn(
                                                    "h-full rounded-full transition-all duration-500",
                                                    repo.health_score >= 80 ? "bg-emerald-500" :
                                                        repo.health_score >= 60 ? "bg-amber-500" : "bg-red-500"
                                                )}
                                                style={{ width: `${repo.health_score}%` }}
                                            />
                                        </div>

                                        <div className="flex gap-4 text-[11px] text-gray-400">
                                            <span>Descriptions: {repo.description_coverage}%</span>
                                            <span>Params: {repo.parameter_coverage}%</span>
                                            <span>Examples: {repo.example_coverage}%</span>
                                        </div>

                                        {repo.undocumented_endpoints > 0 && (
                                            <div className="mt-2 flex items-center gap-1.5 text-[11px] text-amber-400">
                                                <AlertTriangle size={12} />
                                                {repo.undocumented_endpoints} undocumented endpoints
                                            </div>
                                        )}
                                    </div>
                                ))
                            )}
                        </div>
                    </GlassCard>
                </div>
            </div>
        </div>
    );
}

// Stat Card Component
function StatCard({
    icon: Icon,
    label,
    value,
    trend,
    color,
    small = false
}: {
    icon: React.ElementType;
    label: string;
    value: string;
    trend?: number;
    color: string;
    small?: boolean;
}) {
    const colorClasses: Record<string, string> = {
        blue: "from-blue-500 to-blue-600",
        purple: "from-purple-500 to-purple-600",
        emerald: "from-emerald-500 to-emerald-600",
        pink: "from-pink-500 to-pink-600",
        cyan: "from-cyan-500 to-cyan-600",
        amber: "from-amber-500 to-amber-600"
    };

    return (
        <GlassCard className={cn("p-4", small && "py-3")}>
            <div className="flex items-center gap-3">
                <div className={cn(
                    "rounded-lg bg-gradient-to-br flex items-center justify-center",
                    colorClasses[color],
                    small ? "w-8 h-8" : "w-10 h-10"
                )}>
                    <Icon size={small ? 14 : 18} />
                </div>
                <div>
                    <p className="text-xs text-gray-400">{label}</p>
                    <div className="flex items-center gap-2">
                        <p className={cn("font-semibold", small ? "text-lg" : "text-2xl")}>{value}</p>
                        {trend !== undefined && (
                            <span className={cn(
                                "text-xs flex items-center gap-0.5",
                                trend >= 0 ? "text-emerald-400" : "text-red-400"
                            )}>
                                {trend >= 0 ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
                                {Math.abs(trend)}%
                            </span>
                        )}
                    </div>
                </div>
            </div>
        </GlassCard>
    );
}
