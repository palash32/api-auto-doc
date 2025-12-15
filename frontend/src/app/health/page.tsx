"use client";

import React, { useState, useEffect } from "react";
import {
    Activity,
    CheckCircle,
    XCircle,
    AlertTriangle,
    Clock,
    TrendingUp,
    Bell,
    RefreshCw,
    Play,
    Settings,
    ChevronRight
} from "lucide-react";
import { cn } from "@/lib/utils";
import { API_BASE_URL } from "@/lib/api";
import { GlassCard } from "@/components/ui/glass-card";

interface HealthDashboard {
    total_endpoints: number;
    status_breakdown: {
        healthy: number;
        degraded: number;
        unhealthy: number;
        unknown: number;
    };
    avg_uptime_24h: number;
    avg_latency_ms: number | null;
    open_alerts: number;
}

interface HealthAlert {
    id: string;
    alert_type: string;
    severity: string;
    title: string;
    message: string | null;
    is_resolved: boolean;
    created_at: string;
}

const STATUS_COLORS: Record<string, { bg: string; text: string; icon: any }> = {
    healthy: { bg: "bg-emerald-500/10", text: "text-emerald-400", icon: CheckCircle },
    degraded: { bg: "bg-amber-500/10", text: "text-amber-400", icon: AlertTriangle },
    unhealthy: { bg: "bg-red-500/10", text: "text-red-400", icon: XCircle },
    unknown: { bg: "bg-gray-500/10", text: "text-gray-400", icon: Clock }
};

export default function HealthDashboardPage() {
    const [dashboard, setDashboard] = useState<HealthDashboard | null>(null);
    const [alerts, setAlerts] = useState<HealthAlert[]>([]);
    const [loading, setLoading] = useState(true);
    const [checkUrl, setCheckUrl] = useState("");
    const [checkResult, setCheckResult] = useState<any>(null);
    const [checking, setChecking] = useState(false);

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        setLoading(true);
        try {
            const [dashRes, alertsRes] = await Promise.all([
                fetch(`${API_BASE_URL}/api/health/dashboard`),
                fetch(`${API_BASE_URL}/api/health/alerts?resolved=false&limit=10`)
            ]);

            if (dashRes.ok) {
                setDashboard(await dashRes.json());
            }
            if (alertsRes.ok) {
                setAlerts(await alertsRes.json());
            }
        } catch (e) {
            console.error("Failed to fetch health data:", e);
        } finally {
            setLoading(false);
        }
    };

    const runHealthCheck = async () => {
        if (!checkUrl) return;
        setChecking(true);
        setCheckResult(null);

        try {
            const res = await fetch(`${API_BASE_URL}/api/health/check`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ url: checkUrl, method: "GET" })
            });

            if (res.ok) {
                setCheckResult(await res.json());
            }
        } catch (e) {
            setCheckResult({ status: "error", error_message: "Failed to run check" });
        } finally {
            setChecking(false);
        }
    };

    const resolveAlert = async (alertId: string) => {
        try {
            await fetch(`${API_BASE_URL}/api/health/alerts/${alertId}/resolve`, {
                method: "POST"
            });
            fetchData();
        } catch (e) {
            console.error("Failed to resolve alert:", e);
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-[#0a0a0a] flex items-center justify-center">
                <div className="w-8 h-8 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin" />
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-[#0a0a0a] text-white">
            {/* Header */}
            <header className="border-b border-white/10 bg-black/50 backdrop-blur-sm sticky top-0 z-50">
                <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 to-green-600 flex items-center justify-center">
                            <Activity size={20} />
                        </div>
                        <div>
                            <h1 className="text-xl font-semibold">Health Monitoring</h1>
                            <p className="text-xs text-gray-500">Endpoint status & uptime tracking</p>
                        </div>
                    </div>

                    <button
                        onClick={fetchData}
                        className="p-2 hover:bg-white/10 rounded-lg transition-colors"
                    >
                        <RefreshCw size={18} className="text-gray-400" />
                    </button>
                </div>
            </header>

            <div className="max-w-7xl mx-auto p-6">
                {/* Overview Cards */}
                <div className="grid grid-cols-2 lg:grid-cols-5 gap-4 mb-8">
                    <GlassCard className="p-4 text-center">
                        <p className="text-3xl font-bold">{dashboard?.total_endpoints || 0}</p>
                        <p className="text-xs text-gray-400">Total Endpoints</p>
                    </GlassCard>

                    <GlassCard className="p-4 text-center bg-emerald-500/5">
                        <p className="text-3xl font-bold text-emerald-400">
                            {dashboard?.status_breakdown.healthy || 0}
                        </p>
                        <p className="text-xs text-gray-400">Healthy</p>
                    </GlassCard>

                    <GlassCard className="p-4 text-center bg-amber-500/5">
                        <p className="text-3xl font-bold text-amber-400">
                            {dashboard?.status_breakdown.degraded || 0}
                        </p>
                        <p className="text-xs text-gray-400">Degraded</p>
                    </GlassCard>

                    <GlassCard className="p-4 text-center bg-red-500/5">
                        <p className="text-3xl font-bold text-red-400">
                            {dashboard?.status_breakdown.unhealthy || 0}
                        </p>
                        <p className="text-xs text-gray-400">Unhealthy</p>
                    </GlassCard>

                    <GlassCard className="p-4 text-center">
                        <p className="text-3xl font-bold">
                            {dashboard?.avg_uptime_24h || 100}%
                        </p>
                        <p className="text-xs text-gray-400">24h Uptime</p>
                    </GlassCard>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Quick Health Check */}
                    <GlassCard className="p-6">
                        <h3 className="text-sm font-medium mb-4 flex items-center gap-2">
                            <Play size={14} className="text-blue-400" />
                            Quick Health Check
                        </h3>

                        <div className="flex gap-2 mb-4">
                            <input
                                type="url"
                                value={checkUrl}
                                onChange={(e) => setCheckUrl(e.target.value)}
                                placeholder="https://api.example.com/health"
                                className="flex-1 px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500/50"
                            />
                            <button
                                onClick={runHealthCheck}
                                disabled={checking || !checkUrl}
                                className="px-4 py-2 bg-blue-500/20 hover:bg-blue-500/30 text-blue-300 rounded-lg text-sm font-medium disabled:opacity-50 flex items-center gap-2"
                            >
                                {checking ? (
                                    <RefreshCw size={14} className="animate-spin" />
                                ) : (
                                    <Play size={14} />
                                )}
                                Check
                            </button>
                        </div>

                        {checkResult && (
                            <div className={cn(
                                "p-4 rounded-lg",
                                STATUS_COLORS[checkResult.status]?.bg || "bg-gray-500/10"
                            )}>
                                <div className="flex items-center gap-2 mb-2">
                                    {React.createElement(
                                        STATUS_COLORS[checkResult.status]?.icon || Clock,
                                        { size: 16, className: STATUS_COLORS[checkResult.status]?.text }
                                    )}
                                    <span className={cn(
                                        "font-medium capitalize",
                                        STATUS_COLORS[checkResult.status]?.text
                                    )}>
                                        {checkResult.status}
                                    </span>
                                    {checkResult.status_code && (
                                        <span className="text-xs text-gray-400">
                                            ({checkResult.status_code})
                                        </span>
                                    )}
                                </div>

                                <div className="flex gap-4 text-xs text-gray-400">
                                    {checkResult.latency_ms && (
                                        <span>Latency: {checkResult.latency_ms}ms</span>
                                    )}
                                    {checkResult.error_message && (
                                        <span className="text-red-400">{checkResult.error_message}</span>
                                    )}
                                </div>
                            </div>
                        )}
                    </GlassCard>

                    {/* Performance Stats */}
                    <GlassCard className="p-6">
                        <h3 className="text-sm font-medium mb-4 flex items-center gap-2">
                            <TrendingUp size={14} className="text-purple-400" />
                            Performance Overview
                        </h3>

                        <div className="space-y-4">
                            <div>
                                <div className="flex justify-between text-sm mb-1">
                                    <span className="text-gray-400">Average Latency</span>
                                    <span className="font-mono">
                                        {dashboard?.avg_latency_ms
                                            ? `${dashboard.avg_latency_ms}ms`
                                            : "N/A"
                                        }
                                    </span>
                                </div>
                                <div className="h-2 rounded-full bg-white/5 overflow-hidden">
                                    <div
                                        className="h-full bg-gradient-to-r from-purple-500 to-blue-500 rounded-full"
                                        style={{
                                            width: `${Math.min((dashboard?.avg_latency_ms || 0) / 10, 100)}%`
                                        }}
                                    />
                                </div>
                            </div>

                            <div>
                                <div className="flex justify-between text-sm mb-1">
                                    <span className="text-gray-400">24h Uptime</span>
                                    <span className="font-mono text-emerald-400">
                                        {dashboard?.avg_uptime_24h || 100}%
                                    </span>
                                </div>
                                <div className="h-2 rounded-full bg-white/5 overflow-hidden">
                                    <div
                                        className="h-full bg-gradient-to-r from-emerald-500 to-green-500 rounded-full"
                                        style={{ width: `${dashboard?.avg_uptime_24h || 100}%` }}
                                    />
                                </div>
                            </div>

                            <div className="pt-2 border-t border-white/5">
                                <p className="text-xs text-gray-500">
                                    {dashboard?.open_alerts || 0} open alerts
                                </p>
                            </div>
                        </div>
                    </GlassCard>
                </div>

                {/* Alerts Section */}
                <GlassCard className="mt-6 p-6">
                    <h3 className="text-sm font-medium mb-4 flex items-center gap-2">
                        <Bell size={14} className="text-amber-400" />
                        Recent Alerts
                        {alerts.length > 0 && (
                            <span className="ml-auto text-xs px-2 py-0.5 bg-red-500/10 text-red-400 rounded-full">
                                {alerts.length} open
                            </span>
                        )}
                    </h3>

                    {alerts.length === 0 ? (
                        <div className="text-center py-8 text-gray-500">
                            <CheckCircle size={32} className="mx-auto mb-2 text-emerald-500/50" />
                            <p className="text-sm">No open alerts</p>
                            <p className="text-xs">All systems operational</p>
                        </div>
                    ) : (
                        <div className="space-y-2">
                            {alerts.map((alert) => (
                                <div
                                    key={alert.id}
                                    className={cn(
                                        "p-3 rounded-lg flex items-center gap-3",
                                        alert.severity === "critical" && "bg-red-500/10",
                                        alert.severity === "warning" && "bg-amber-500/10",
                                        alert.severity === "info" && "bg-blue-500/10"
                                    )}
                                >
                                    <AlertTriangle size={16} className={cn(
                                        alert.severity === "critical" && "text-red-400",
                                        alert.severity === "warning" && "text-amber-400",
                                        alert.severity === "info" && "text-blue-400"
                                    )} />

                                    <div className="flex-1">
                                        <p className="text-sm font-medium">{alert.title}</p>
                                        {alert.message && (
                                            <p className="text-xs text-gray-400">{alert.message}</p>
                                        )}
                                    </div>

                                    <button
                                        onClick={() => resolveAlert(alert.id)}
                                        className="px-3 py-1 text-xs bg-white/5 hover:bg-white/10 rounded"
                                    >
                                        Resolve
                                    </button>
                                </div>
                            ))}
                        </div>
                    )}
                </GlassCard>
            </div>
        </div>
    );
}
