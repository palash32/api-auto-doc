"use client";

import React, { useState, useEffect } from "react";
import {
    GitBranch,
    Play,
    Check,
    X,
    Clock,
    Plus,
    Trash2,
    Code,
    Copy,
    MessageSquare,
    Badge,
    Settings
} from "lucide-react";
import { cn } from "@/lib/utils";
import { GlassCard } from "@/components/ui/glass-card";

interface Pipeline {
    id: string;
    repository_id: string;
    provider: string;
    name: string;
    config_file: string | null;
    trigger_on_push: boolean;
    trigger_on_pr: boolean;
    pr_comments: boolean;
    is_enabled: boolean;
    last_run_at: string | null;
    last_run_status: string | null;
}

interface Build {
    id: string;
    build_number: number;
    commit_sha: string | null;
    branch: string | null;
    status: string;
    endpoints_found: number;
    endpoints_added: number;
    endpoints_modified: number;
    endpoints_removed: number;
    breaking_changes: number;
    started_at: string | null;
    duration_seconds: number | null;
}

const PROVIDER_ICONS: Record<string, string> = {
    github_actions: "🐙",
    gitlab_ci: "🦊",
    jenkins: "🔧",
    bitbucket: "🪣",
    circle_ci: "⭕"
};

const STATUS_COLORS: Record<string, { bg: string; icon: any }> = {
    success: { bg: "bg-emerald-500/10 text-emerald-400", icon: Check },
    failed: { bg: "bg-red-500/10 text-red-400", icon: X },
    running: { bg: "bg-blue-500/10 text-blue-400", icon: Clock },
    pending: { bg: "bg-amber-500/10 text-amber-400", icon: Clock }
};

type TabType = "pipelines" | "builds" | "config";

export default function CICDPage() {
    const [activeTab, setActiveTab] = useState<TabType>("pipelines");
    const [pipelines, setPipelines] = useState<Pipeline[]>([]);
    const [builds, setBuilds] = useState<Build[]>([]);
    const [selectedPipeline, setSelectedPipeline] = useState<Pipeline | null>(null);
    const [configContent, setConfigContent] = useState("");
    const [loading, setLoading] = useState(true);
    const [copied, setCopied] = useState(false);

    useEffect(() => {
        fetchData();
    }, [activeTab]);

    const fetchData = async () => {
        setLoading(true);
        try {
            if (activeTab === "pipelines") {
                const res = await fetch("http://localhost:8000/api/cicd/pipelines");
                if (res.ok) setPipelines(await res.json());
            } else if (activeTab === "builds") {
                const res = await fetch("http://localhost:8000/api/cicd/builds?limit=20");
                if (res.ok) setBuilds(await res.json());
            }
        } catch (e) {
            console.error("Failed to fetch CI/CD data:", e);
        } finally {
            setLoading(false);
        }
    };

    const loadConfig = async (pipeline: Pipeline) => {
        setSelectedPipeline(pipeline);
        setActiveTab("config");
        try {
            const res = await fetch(`http://localhost:8000/api/cicd/pipelines/${pipeline.id}/config`);
            if (res.ok) {
                const data = await res.json();
                setConfigContent(data.content);
            }
        } catch (e) {
            console.error("Failed to load config:", e);
        }
    };

    const triggerBuild = async (pipelineId: string) => {
        try {
            await fetch(`http://localhost:8000/api/cicd/pipelines/${pipelineId}/trigger`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ branch: "main" })
            });
            setActiveTab("builds");
            fetchData();
        } catch (e) {
            console.error("Failed to trigger build:", e);
        }
    };

    const copyConfig = () => {
        navigator.clipboard.writeText(configContent);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    const formatDate = (dateStr: string | null) => {
        if (!dateStr) return "Never";
        return new Date(dateStr).toLocaleString("en-US", {
            month: "short",
            day: "numeric",
            hour: "2-digit",
            minute: "2-digit"
        });
    };

    const tabs = [
        { id: "pipelines", icon: GitBranch, label: "Pipelines" },
        { id: "builds", icon: Play, label: "Builds" },
        { id: "config", icon: Code, label: "Config" }
    ];

    return (
        <div className="min-h-screen bg-[#0a0a0a] text-white">
            {/* Header */}
            <header className="border-b border-white/10 bg-black/50 backdrop-blur-sm sticky top-0 z-50">
                <div className="max-w-6xl mx-auto px-6 py-4">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center">
                            <GitBranch size={20} />
                        </div>
                        <div>
                            <h1 className="text-xl font-semibold">CI/CD Integrations</h1>
                            <p className="text-xs text-gray-500">GitHub Actions, GitLab CI, Jenkins</p>
                        </div>
                    </div>
                </div>
            </header>

            <div className="max-w-6xl mx-auto p-6">
                {/* Tabs */}
                <div className="flex flex-wrap gap-2 mb-6">
                    {tabs.map((tab) => (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id as TabType)}
                            className={cn(
                                "px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 transition-colors",
                                activeTab === tab.id
                                    ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/30"
                                    : "text-gray-400 hover:text-white hover:bg-white/5"
                            )}
                        >
                            <tab.icon size={14} />
                            {tab.label}
                        </button>
                    ))}
                </div>

                {/* Pipelines */}
                {activeTab === "pipelines" && (
                    <GlassCard className="p-6">
                        <h3 className="text-sm font-medium mb-4 flex items-center gap-2">
                            <GitBranch size={14} className="text-cyan-400" />
                            CI/CD Pipelines
                        </h3>

                        {pipelines.length === 0 ? (
                            <div className="text-center py-8 text-gray-500">
                                <GitBranch size={32} className="mx-auto mb-2 opacity-50" />
                                <p className="text-sm">No pipelines configured</p>
                                <p className="text-xs">Add a CI/CD integration to automate API scanning</p>
                            </div>
                        ) : (
                            <div className="space-y-3">
                                {pipelines.map((pipeline) => (
                                    <div
                                        key={pipeline.id}
                                        className="p-4 rounded-lg bg-white/5 flex items-center gap-4"
                                    >
                                        <span className="text-2xl">{PROVIDER_ICONS[pipeline.provider]}</span>

                                        <div className="flex-1">
                                            <div className="flex items-center gap-2">
                                                <p className="font-medium">{pipeline.name}</p>
                                                <span className={cn(
                                                    "text-xs px-2 py-0.5 rounded",
                                                    pipeline.is_enabled
                                                        ? "bg-emerald-500/10 text-emerald-400"
                                                        : "bg-gray-500/10 text-gray-400"
                                                )}>
                                                    {pipeline.is_enabled ? "Active" : "Disabled"}
                                                </span>
                                            </div>
                                            <p className="text-xs text-gray-500">
                                                {pipeline.config_file} • Last run: {formatDate(pipeline.last_run_at)}
                                            </p>
                                        </div>

                                        <div className="flex items-center gap-2">
                                            {pipeline.pr_comments && (
                                                <span className="text-xs px-2 py-0.5 bg-purple-500/10 text-purple-400 rounded flex items-center gap-1">
                                                    <MessageSquare size={10} />
                                                    PR Bot
                                                </span>
                                            )}

                                            <button
                                                onClick={() => loadConfig(pipeline)}
                                                className="p-2 hover:bg-white/10 rounded text-gray-400"
                                                title="View Config"
                                            >
                                                <Code size={16} />
                                            </button>

                                            <button
                                                onClick={() => triggerBuild(pipeline.id)}
                                                className="px-3 py-1.5 bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-300 rounded text-sm flex items-center gap-1"
                                            >
                                                <Play size={14} />
                                                Run
                                            </button>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </GlassCard>
                )}

                {/* Builds */}
                {activeTab === "builds" && (
                    <GlassCard className="p-6">
                        <h3 className="text-sm font-medium mb-4 flex items-center gap-2">
                            <Play size={14} className="text-blue-400" />
                            Recent Builds
                        </h3>

                        {builds.length === 0 ? (
                            <p className="text-sm text-gray-500 text-center py-8">No builds yet</p>
                        ) : (
                            <div className="space-y-2">
                                {builds.map((build) => {
                                    const StatusIcon = STATUS_COLORS[build.status]?.icon || Clock;
                                    return (
                                        <div
                                            key={build.id}
                                            className="p-3 rounded-lg bg-white/5 flex items-center gap-3"
                                        >
                                            <div className={cn(
                                                "w-8 h-8 rounded-lg flex items-center justify-center",
                                                STATUS_COLORS[build.status]?.bg
                                            )}>
                                                <StatusIcon size={16} />
                                            </div>

                                            <div className="flex-1">
                                                <div className="flex items-center gap-2">
                                                    <span className="font-mono text-sm">#{build.build_number}</span>
                                                    {build.branch && (
                                                        <span className="text-xs text-gray-500">{build.branch}</span>
                                                    )}
                                                    {build.commit_sha && (
                                                        <code className="text-xs text-gray-500">{build.commit_sha.slice(0, 7)}</code>
                                                    )}
                                                </div>
                                                <p className="text-xs text-gray-500">
                                                    {build.endpoints_found} endpoints • +{build.endpoints_added} -{build.endpoints_removed}
                                                    {build.breaking_changes > 0 && (
                                                        <span className="text-red-400 ml-2">⚠️ {build.breaking_changes} breaking</span>
                                                    )}
                                                </p>
                                            </div>

                                            <div className="text-right text-xs text-gray-500">
                                                <p>{formatDate(build.started_at)}</p>
                                                {build.duration_seconds && (
                                                    <p>{build.duration_seconds}s</p>
                                                )}
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        )}
                    </GlassCard>
                )}

                {/* Config */}
                {activeTab === "config" && (
                    <GlassCard className="p-6">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-sm font-medium flex items-center gap-2">
                                <Code size={14} className="text-amber-400" />
                                {selectedPipeline ? `${selectedPipeline.name} Config` : "Pipeline Configuration"}
                            </h3>

                            {configContent && (
                                <button
                                    onClick={copyConfig}
                                    className="px-3 py-1.5 bg-white/5 hover:bg-white/10 rounded text-sm flex items-center gap-2"
                                >
                                    {copied ? <Check size={14} className="text-emerald-400" /> : <Copy size={14} />}
                                    {copied ? "Copied!" : "Copy"}
                                </button>
                            )}
                        </div>

                        {configContent ? (
                            <pre className="p-4 rounded-lg bg-black/50 overflow-x-auto text-sm font-mono">
                                <code>{configContent}</code>
                            </pre>
                        ) : (
                            <p className="text-sm text-gray-500 text-center py-8">
                                Select a pipeline to view its configuration
                            </p>
                        )}

                        {selectedPipeline && (
                            <div className="mt-4 p-4 rounded-lg bg-blue-500/10 border border-blue-500/20">
                                <p className="text-sm text-blue-300 flex items-center gap-2">
                                    <Badge size={14} />
                                    Add this file to your repository: <code className="bg-black/30 px-2 py-0.5 rounded">{selectedPipeline.config_file}</code>
                                </p>
                            </div>
                        )}
                    </GlassCard>
                )}
            </div>
        </div>
    );
}
