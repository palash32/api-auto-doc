"use client";

import React, { useState, useEffect } from "react";
import {
    Database,
    Table,
    ArrowRight,
    RefreshCw,
    Layers,
    GitBranch,
    Zap,
    HardDrive,
    Activity
} from "lucide-react";
import { cn } from "@/lib/utils";
import { API_BASE_URL } from "@/lib/api";
import { GlassCard } from "@/components/ui/glass-card";

interface TableInfo {
    name: string;
    total_reads: number;
    total_writes: number;
    related_endpoints: string[];
    estimated_size: string;
}

interface Relationship {
    from: string;
    to: string;
    type: string;
}

interface DatabaseOverview {
    total_tables: number;
    tables: TableInfo[];
    relationships: Relationship[];
}

interface QueryInsight {
    query: string;
    avg_time_ms: number;
    call_count: number;
    suggestion: string;
}

interface Insights {
    slow_queries: QueryInsight[];
    optimization_suggestions: Array<{
        table: string;
        type: string;
        description: string;
        impact: string;
    }>;
    connection_pool: {
        active: number;
        idle: number;
        max: number;
        waiting: number;
    };
}

const TABLE_COLORS = [
    "from-blue-500/20 to-cyan-500/20 border-blue-500/20",
    "from-purple-500/20 to-pink-500/20 border-purple-500/20",
    "from-emerald-500/20 to-teal-500/20 border-emerald-500/20",
    "from-amber-500/20 to-orange-500/20 border-amber-500/20",
    "from-red-500/20 to-pink-500/20 border-red-500/20",
];

export default function DatabasePage() {
    const [overview, setOverview] = useState<DatabaseOverview | null>(null);
    const [insights, setInsights] = useState<Insights | null>(null);
    const [loading, setLoading] = useState(true);
    const [selectedTable, setSelectedTable] = useState<string | null>(null);

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        setLoading(true);
        try {
            const [overviewRes, insightsRes] = await Promise.all([
                fetch(`${API_BASE_URL}/api/database/overview`),
                fetch(`${API_BASE_URL}/api/database/insights`)
            ]);

            if (overviewRes.ok) {
                setOverview(await overviewRes.json());
            }
            if (insightsRes.ok) {
                setInsights(await insightsRes.json());
            }
        } catch (e) {
            console.error("Failed to fetch database data:", e);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-[#0a0a0a] text-white">
            {/* Header */}
            <div className="border-b border-white/5 bg-[#0a0a0a]/80 backdrop-blur-xl sticky top-0 z-50">
                <div className="container mx-auto px-6 py-4">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <div className="p-2 rounded-lg bg-gradient-to-br from-purple-500/20 to-blue-500/20 border border-purple-500/20">
                                <Database className="w-6 h-6 text-purple-400" />
                            </div>
                            <div>
                                <h1 className="text-xl font-bold">Database Insights</h1>
                                <p className="text-sm text-gray-400">Table relationships and API mappings</p>
                            </div>
                        </div>
                        <button
                            onClick={fetchData}
                            disabled={loading}
                            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 transition-colors"
                        >
                            <RefreshCw className={cn("w-4 h-4", loading && "animate-spin")} />
                            Refresh
                        </button>
                    </div>
                </div>
            </div>

            <div className="container mx-auto px-6 py-8">
                {/* Stats Grid */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
                    <GlassCard className="p-6">
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-gray-400 text-sm">Tables Detected</span>
                            <Table className="w-5 h-5 text-purple-500" />
                        </div>
                        <div className="text-3xl font-bold text-purple-400">
                            {overview?.total_tables || 0}
                        </div>
                    </GlassCard>

                    <GlassCard className="p-6">
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-gray-400 text-sm">Relationships</span>
                            <GitBranch className="w-5 h-5 text-blue-500" />
                        </div>
                        <div className="text-3xl font-bold text-blue-400">
                            {overview?.relationships?.length || 0}
                        </div>
                    </GlassCard>

                    <GlassCard className="p-6">
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-gray-400 text-sm">Active Connections</span>
                            <Activity className="w-5 h-5 text-emerald-500" />
                        </div>
                        <div className="text-3xl font-bold text-emerald-400">
                            {insights?.connection_pool?.active || 0}
                            <span className="text-lg text-gray-500">/{insights?.connection_pool?.max || 20}</span>
                        </div>
                    </GlassCard>

                    <GlassCard className="p-6">
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-gray-400 text-sm">Optimizations</span>
                            <Zap className="w-5 h-5 text-amber-500" />
                        </div>
                        <div className="text-3xl font-bold text-amber-400">
                            {insights?.optimization_suggestions?.length || 0}
                        </div>
                        <p className="text-xs text-gray-500 mt-1">Suggestions available</p>
                    </GlassCard>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Tables */}
                    <GlassCard className="p-6">
                        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                            <Layers className="w-5 h-5 text-purple-400" />
                            Detected Tables
                        </h2>

                        {loading ? (
                            <div className="flex items-center justify-center py-12">
                                <RefreshCw className="w-8 h-8 animate-spin text-gray-500" />
                            </div>
                        ) : overview?.tables?.length === 0 ? (
                            <div className="text-center py-12 text-gray-400">
                                <Database className="w-12 h-12 mx-auto mb-3 opacity-50" />
                                <p>No tables detected yet</p>
                                <p className="text-sm">Add repositories to detect database tables</p>
                            </div>
                        ) : (
                            <div className="space-y-3">
                                {overview?.tables?.map((table, idx) => (
                                    <div
                                        key={table.name}
                                        onClick={() => setSelectedTable(table.name === selectedTable ? null : table.name)}
                                        className={cn(
                                            "p-4 rounded-lg border cursor-pointer transition-all",
                                            `bg-gradient-to-r ${TABLE_COLORS[idx % TABLE_COLORS.length]}`,
                                            selectedTable === table.name ? "ring-2 ring-white/20" : "hover:bg-white/5"
                                        )}
                                    >
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center gap-3">
                                                <Table className="w-5 h-5" />
                                                <div>
                                                    <h3 className="font-medium">{table.name}</h3>
                                                    <p className="text-xs text-gray-400">
                                                        {table.total_reads} reads • {table.total_writes} writes
                                                    </p>
                                                </div>
                                            </div>
                                            <span className="text-xs text-gray-500">{table.estimated_size}</span>
                                        </div>

                                        {selectedTable === table.name && table.related_endpoints?.length > 0 && (
                                            <div className="mt-3 pt-3 border-t border-white/10">
                                                <p className="text-xs text-gray-400 mb-2">Related endpoints:</p>
                                                <div className="space-y-1">
                                                    {table.related_endpoints.slice(0, 3).map((ep, i) => (
                                                        <div key={i} className="text-xs font-mono text-gray-300">{ep}</div>
                                                    ))}
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                ))}
                            </div>
                        )}
                    </GlassCard>

                    {/* Relationships */}
                    <div className="space-y-6">
                        <GlassCard className="p-6">
                            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                                <GitBranch className="w-5 h-5 text-blue-400" />
                                Table Relationships
                            </h2>

                            {overview?.relationships?.length === 0 ? (
                                <p className="text-gray-400 text-center py-8">No relationships detected</p>
                            ) : (
                                <div className="space-y-2">
                                    {overview?.relationships?.map((rel, idx) => (
                                        <div
                                            key={idx}
                                            className="flex items-center gap-3 p-3 rounded-lg bg-white/5 border border-white/5"
                                        >
                                            <span className="px-2 py-1 rounded bg-purple-500/20 text-purple-300 text-sm font-mono">
                                                {rel.from}
                                            </span>
                                            <ArrowRight className="w-4 h-4 text-gray-500" />
                                            <span className="px-2 py-1 rounded bg-blue-500/20 text-blue-300 text-sm font-mono">
                                                {rel.to}
                                            </span>
                                            <span className="ml-auto text-xs text-gray-500">{rel.type}</span>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </GlassCard>

                        {/* Optimization Suggestions */}
                        <GlassCard className="p-6">
                            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                                <Zap className="w-5 h-5 text-amber-400" />
                                Optimization Suggestions
                            </h2>

                            {insights?.optimization_suggestions?.length === 0 ? (
                                <p className="text-gray-400 text-center py-8">No suggestions at this time</p>
                            ) : (
                                <div className="space-y-3">
                                    {insights?.optimization_suggestions?.map((sug, idx) => (
                                        <div
                                            key={idx}
                                            className={cn(
                                                "p-3 rounded-lg border",
                                                sug.impact === "high" ? "bg-red-500/5 border-red-500/20" :
                                                    sug.impact === "medium" ? "bg-amber-500/5 border-amber-500/20" :
                                                        "bg-blue-500/5 border-blue-500/20"
                                            )}
                                        >
                                            <div className="flex items-start gap-2">
                                                <Zap className={cn(
                                                    "w-4 h-4 mt-0.5",
                                                    sug.impact === "high" ? "text-red-400" :
                                                        sug.impact === "medium" ? "text-amber-400" : "text-blue-400"
                                                )} />
                                                <div>
                                                    <p className="text-sm">{sug.description}</p>
                                                    <p className="text-xs text-gray-500 mt-1">
                                                        Table: {sug.table} • Type: {sug.type}
                                                    </p>
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </GlassCard>
                    </div>
                </div>
            </div>
        </div>
    );
}
