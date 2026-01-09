"use client";

import React, { useState, useEffect } from "react";
import {
    Shield,
    AlertTriangle,
    CheckCircle,
    XCircle,
    Lock,
    Unlock,
    RefreshCw,
    ChevronRight,
    Eye,
    TrendingUp
} from "lucide-react";
import { cn } from "@/lib/utils";
import { API_BASE_URL } from "@/lib/api";
import { GlassCard } from "@/components/ui/glass-card";

interface SecuritySummary {
    total_endpoints: number;
    auth_required: number;
    public: number;
    vulnerability_count: number;
    security_score: number;
}

interface Vulnerability {
    id: string;
    type: string;
    severity: "high" | "medium" | "low";
    endpoint_path: string;
    endpoint_method: string;
    repository_name: string;
    description: string;
    recommendation: string;
    detected_at: string;
}

const SEVERITY_COLORS = {
    high: { bg: "bg-red-500/10", text: "text-red-400", border: "border-red-500/20" },
    medium: { bg: "bg-amber-500/10", text: "text-amber-400", border: "border-amber-500/20" },
    low: { bg: "bg-blue-500/10", text: "text-blue-400", border: "border-blue-500/20" }
};

const METHOD_COLORS: Record<string, string> = {
    GET: "bg-emerald-500/20 text-emerald-400",
    POST: "bg-blue-500/20 text-blue-400",
    PUT: "bg-amber-500/20 text-amber-400",
    PATCH: "bg-purple-500/20 text-purple-400",
    DELETE: "bg-red-500/20 text-red-400"
};

export default function SecurityPage() {
    const [summary, setSummary] = useState<SecuritySummary | null>(null);
    const [vulnerabilities, setVulnerabilities] = useState<Vulnerability[]>([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState<string>("all");

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        setLoading(true);
        try {
            const [summaryRes, vulnRes] = await Promise.all([
                fetch(`${API_BASE_URL}/api/security/scan-results`),
                fetch(`${API_BASE_URL}/api/security/vulnerabilities`)
            ]);

            if (summaryRes.ok) {
                const data = await summaryRes.json();
                setSummary(data.summary);
                if (data.vulnerabilities) {
                    setVulnerabilities(data.vulnerabilities);
                }
            }
            if (vulnRes.ok) {
                const vulns = await vulnRes.json();
                if (Array.isArray(vulns) && vulns.length > 0) {
                    setVulnerabilities(vulns);
                }
            }
        } catch (e) {
            console.error("Failed to fetch security data:", e);
        } finally {
            setLoading(false);
        }
    };

    const filteredVulns = filter === "all"
        ? vulnerabilities
        : vulnerabilities.filter(v => v.severity === filter);

    const getScoreColor = (score: number) => {
        if (score >= 90) return "text-emerald-400";
        if (score >= 70) return "text-amber-400";
        return "text-red-400";
    };

    return (
        <div className="min-h-screen bg-[#0a0a0a] text-white">
            {/* Header */}
            <div className="border-b border-white/5 bg-[#0a0a0a]/80 backdrop-blur-xl sticky top-0 z-50">
                <div className="container mx-auto px-6 py-4">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <div className="p-2 rounded-lg bg-gradient-to-br from-red-500/20 to-orange-500/20 border border-red-500/20">
                                <Shield className="w-6 h-6 text-red-400" />
                            </div>
                            <div>
                                <h1 className="text-xl font-bold">Security Scanning</h1>
                                <p className="text-sm text-gray-400">Detect authentication gaps and vulnerabilities</p>
                            </div>
                        </div>
                        <button
                            onClick={fetchData}
                            disabled={loading}
                            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 transition-colors"
                        >
                            <RefreshCw className={cn("w-4 h-4", loading && "animate-spin")} />
                            Rescan
                        </button>
                    </div>
                </div>
            </div>

            <div className="container mx-auto px-6 py-8">
                {/* Stats Grid */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
                    <GlassCard className="p-6">
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-gray-400 text-sm">Security Score</span>
                            <Shield className="w-5 h-5 text-gray-500" />
                        </div>
                        <div className={cn("text-3xl font-bold", getScoreColor(summary?.security_score || 0))}>
                            {summary?.security_score || 0}%
                        </div>
                        <div className="mt-2 h-2 bg-white/5 rounded-full overflow-hidden">
                            <div
                                className={cn(
                                    "h-full rounded-full transition-all",
                                    (summary?.security_score || 0) >= 90 ? "bg-emerald-500" :
                                        (summary?.security_score || 0) >= 70 ? "bg-amber-500" : "bg-red-500"
                                )}
                                style={{ width: `${summary?.security_score || 0}%` }}
                            />
                        </div>
                    </GlassCard>

                    <GlassCard className="p-6">
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-gray-400 text-sm">Protected</span>
                            <Lock className="w-5 h-5 text-emerald-500" />
                        </div>
                        <div className="text-3xl font-bold text-emerald-400">
                            {summary?.auth_required || 0}
                        </div>
                        <p className="text-xs text-gray-500 mt-1">Endpoints with auth</p>
                    </GlassCard>

                    <GlassCard className="p-6">
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-gray-400 text-sm">Public</span>
                            <Unlock className="w-5 h-5 text-amber-500" />
                        </div>
                        <div className="text-3xl font-bold text-amber-400">
                            {summary?.public || 0}
                        </div>
                        <p className="text-xs text-gray-500 mt-1">No authentication</p>
                    </GlassCard>

                    <GlassCard className="p-6">
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-gray-400 text-sm">Vulnerabilities</span>
                            <AlertTriangle className="w-5 h-5 text-red-500" />
                        </div>
                        <div className="text-3xl font-bold text-red-400">
                            {summary?.vulnerability_count || 0}
                        </div>
                        <p className="text-xs text-gray-500 mt-1">Issues detected</p>
                    </GlassCard>
                </div>

                {/* Vulnerabilities Section */}
                <GlassCard className="p-6">
                    <div className="flex items-center justify-between mb-6">
                        <h2 className="text-lg font-semibold">Detected Vulnerabilities</h2>
                        <div className="flex gap-2">
                            {["all", "high", "medium", "low"].map((f) => (
                                <button
                                    key={f}
                                    onClick={() => setFilter(f)}
                                    className={cn(
                                        "px-3 py-1 rounded-full text-xs font-medium transition-colors",
                                        filter === f
                                            ? "bg-white/10 text-white"
                                            : "text-gray-400 hover:text-white"
                                    )}
                                >
                                    {f.charAt(0).toUpperCase() + f.slice(1)}
                                </button>
                            ))}
                        </div>
                    </div>

                    {loading ? (
                        <div className="flex items-center justify-center py-12">
                            <RefreshCw className="w-8 h-8 animate-spin text-gray-500" />
                        </div>
                    ) : filteredVulns.length === 0 ? (
                        <div className="flex flex-col items-center justify-center py-12 text-center">
                            <CheckCircle className="w-16 h-16 text-emerald-500 mb-4" />
                            <h3 className="text-lg font-medium text-emerald-400">All Clear!</h3>
                            <p className="text-gray-400 mt-1">No vulnerabilities detected</p>
                        </div>
                    ) : (
                        <div className="space-y-3">
                            {filteredVulns.map((vuln) => (
                                <div
                                    key={vuln.id}
                                    className={cn(
                                        "p-4 rounded-lg border transition-colors hover:bg-white/5",
                                        SEVERITY_COLORS[vuln.severity].bg,
                                        SEVERITY_COLORS[vuln.severity].border
                                    )}
                                >
                                    <div className="flex items-start justify-between">
                                        <div className="flex items-start gap-3">
                                            <AlertTriangle className={cn("w-5 h-5 mt-0.5", SEVERITY_COLORS[vuln.severity].text)} />
                                            <div>
                                                <div className="flex items-center gap-2 mb-1">
                                                    <span className={cn(
                                                        "px-2 py-0.5 rounded text-xs font-mono",
                                                        METHOD_COLORS[vuln.endpoint_method] || "bg-gray-500/20 text-gray-400"
                                                    )}>
                                                        {vuln.endpoint_method}
                                                    </span>
                                                    <span className="font-mono text-sm">{vuln.endpoint_path}</span>
                                                </div>
                                                <p className="text-sm text-gray-400">{vuln.description}</p>
                                                <p className="text-xs text-gray-500 mt-1">
                                                    {vuln.repository_name} • {vuln.recommendation}
                                                </p>
                                            </div>
                                        </div>
                                        <span className={cn(
                                            "px-2 py-1 rounded text-xs font-medium uppercase",
                                            SEVERITY_COLORS[vuln.severity].bg,
                                            SEVERITY_COLORS[vuln.severity].text
                                        )}>
                                            {vuln.severity}
                                        </span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </GlassCard>
            </div>
        </div>
    );
}
