"use client";

import React, { useState, useEffect } from "react";
import {
    History,
    GitCommit,
    Tag,
    ArrowRight,
    ChevronDown,
    ChevronUp,
    Plus,
    Minus,
    Edit,
    FileText,
    Clock,
    Check,
    AlertTriangle,
    Eye,
    ArrowLeftRight
} from "lucide-react";
import { cn } from "@/lib/utils";
import { GlassCard } from "@/components/ui/glass-card";

interface APIVersion {
    id: string;
    repository_id: string;
    version: string;
    version_number: number;
    commit_hash: string | null;
    commit_message: string | null;
    branch: string | null;
    title: string | null;
    total_endpoints: number;
    added_endpoints: number;
    modified_endpoints: number;
    removed_endpoints: number;
    is_published: boolean;
    is_latest: boolean;
    created_at: string;
}

interface EndpointChange {
    id: string;
    change_type: string;
    path: string;
    method: string;
    is_breaking: boolean;
    description: string | null;
}

const METHOD_COLORS: Record<string, string> = {
    GET: "bg-emerald-500/10 text-emerald-400",
    POST: "bg-blue-500/10 text-blue-400",
    PUT: "bg-amber-500/10 text-amber-400",
    PATCH: "bg-purple-500/10 text-purple-400",
    DELETE: "bg-red-500/10 text-red-400"
};

export default function VersionHistoryPage() {
    const [versions, setVersions] = useState<APIVersion[]>([]);
    const [selectedVersion, setSelectedVersion] = useState<APIVersion | null>(null);
    const [changes, setChanges] = useState<EndpointChange[]>([]);
    const [changelog, setChangelog] = useState<string>("");
    const [loading, setLoading] = useState(true);
    const [compareMode, setCompareMode] = useState(false);
    const [compareFrom, setCompareFrom] = useState<string>("");
    const [compareTo, setCompareTo] = useState<string>("");

    // Demo repository ID (in real app, get from route params)
    const repositoryId = "demo-repo-id";

    useEffect(() => {
        fetchVersions();
    }, []);

    const fetchVersions = async () => {
        setLoading(true);
        try {
            const res = await fetch(`http://localhost:8000/api/repositories/${repositoryId}/versions`);
            if (res.ok) {
                setVersions(await res.json());
            }
        } catch (e) {
            console.error("Failed to fetch versions:", e);
        } finally {
            setLoading(false);
        }
    };

    const selectVersion = async (version: APIVersion) => {
        setSelectedVersion(version);

        // Fetch changes
        try {
            const [changesRes, changelogRes] = await Promise.all([
                fetch(`http://localhost:8000/api/versions/${version.id}/changes`),
                fetch(`http://localhost:8000/api/versions/${version.id}/changelog`)
            ]);

            if (changesRes.ok) {
                setChanges(await changesRes.json());
            }
            if (changelogRes.ok) {
                const cl = await changelogRes.json();
                setChangelog(cl.content_markdown || "");
            }
        } catch (e) {
            console.error("Failed to fetch version details:", e);
        }
    };

    const formatDate = (dateStr: string) => {
        return new Date(dateStr).toLocaleDateString("en-US", {
            month: "short",
            day: "numeric",
            year: "numeric",
            hour: "2-digit",
            minute: "2-digit"
        });
    };

    return (
        <div className="min-h-screen bg-[#0a0a0a] text-white">
            {/* Header */}
            <header className="border-b border-white/10 bg-black/50 backdrop-blur-sm sticky top-0 z-50">
                <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center">
                            <History size={20} />
                        </div>
                        <div>
                            <h1 className="text-xl font-semibold">Version History</h1>
                            <p className="text-xs text-gray-500">Track API changes and changelogs</p>
                        </div>
                    </div>

                    <button
                        onClick={() => setCompareMode(!compareMode)}
                        className={cn(
                            "px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2",
                            compareMode
                                ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/30"
                                : "bg-white/5 text-gray-400 hover:text-white"
                        )}
                    >
                        <ArrowLeftRight size={14} />
                        Compare Versions
                    </button>
                </div>
            </header>

            <div className="max-w-7xl mx-auto p-6">
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Version Timeline */}
                    <div className="lg:col-span-1">
                        <GlassCard className="p-4">
                            <h3 className="text-sm font-medium mb-4 flex items-center gap-2">
                                <Clock size={14} className="text-gray-400" />
                                Version Timeline
                            </h3>

                            {versions.length === 0 ? (
                                <div className="text-center py-8 text-gray-500">
                                    <History size={32} className="mx-auto mb-2 opacity-50" />
                                    <p className="text-sm">No versions yet</p>
                                    <p className="text-xs">Versions are created on each scan</p>
                                </div>
                            ) : (
                                <div className="space-y-2">
                                    {versions.map((version, idx) => (
                                        <button
                                            key={version.id}
                                            onClick={() => selectVersion(version)}
                                            className={cn(
                                                "w-full p-3 rounded-lg text-left transition-colors relative",
                                                selectedVersion?.id === version.id
                                                    ? "bg-cyan-500/20 border border-cyan-500/30"
                                                    : "bg-white/5 hover:bg-white/10"
                                            )}
                                        >
                                            {/* Timeline connector */}
                                            {idx < versions.length - 1 && (
                                                <div className="absolute left-6 top-full w-0.5 h-2 bg-white/10" />
                                            )}

                                            <div className="flex items-start gap-3">
                                                <div className={cn(
                                                    "w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0",
                                                    version.is_latest
                                                        ? "bg-emerald-500/20 text-emerald-400"
                                                        : "bg-white/10 text-gray-400"
                                                )}>
                                                    <Tag size={14} />
                                                </div>

                                                <div className="flex-1 min-w-0">
                                                    <div className="flex items-center gap-2">
                                                        <span className="font-medium text-sm">{version.version}</span>
                                                        {version.is_latest && (
                                                            <span className="text-[10px] px-1.5 py-0.5 bg-emerald-500/10 text-emerald-400 rounded">
                                                                Latest
                                                            </span>
                                                        )}
                                                    </div>

                                                    {version.title && (
                                                        <p className="text-xs text-gray-400 truncate">{version.title}</p>
                                                    )}

                                                    <div className="flex items-center gap-3 mt-1 text-[11px] text-gray-500">
                                                        {version.added_endpoints > 0 && (
                                                            <span className="text-emerald-400 flex items-center gap-0.5">
                                                                <Plus size={10} />
                                                                {version.added_endpoints}
                                                            </span>
                                                        )}
                                                        {version.modified_endpoints > 0 && (
                                                            <span className="text-amber-400 flex items-center gap-0.5">
                                                                <Edit size={10} />
                                                                {version.modified_endpoints}
                                                            </span>
                                                        )}
                                                        {version.removed_endpoints > 0 && (
                                                            <span className="text-red-400 flex items-center gap-0.5">
                                                                <Minus size={10} />
                                                                {version.removed_endpoints}
                                                            </span>
                                                        )}
                                                        <span className="text-gray-500">
                                                            {version.total_endpoints} total
                                                        </span>
                                                    </div>

                                                    <p className="text-[10px] text-gray-600 mt-1">
                                                        {formatDate(version.created_at)}
                                                    </p>
                                                </div>
                                            </div>
                                        </button>
                                    ))}
                                </div>
                            )}
                        </GlassCard>
                    </div>

                    {/* Version Details */}
                    <div className="lg:col-span-2 space-y-6">
                        {selectedVersion ? (
                            <>
                                {/* Version Header */}
                                <GlassCard className="p-6">
                                    <div className="flex items-start justify-between">
                                        <div>
                                            <h2 className="text-2xl font-bold flex items-center gap-3">
                                                {selectedVersion.version}
                                                {selectedVersion.is_latest && (
                                                    <span className="text-xs px-2 py-1 bg-emerald-500/10 text-emerald-400 rounded-full">
                                                        Latest
                                                    </span>
                                                )}
                                            </h2>
                                            {selectedVersion.title && (
                                                <p className="text-gray-400 mt-1">{selectedVersion.title}</p>
                                            )}
                                        </div>

                                        <button className="px-4 py-2 bg-white/5 hover:bg-white/10 rounded-lg text-sm flex items-center gap-2">
                                            <Eye size={14} />
                                            View Snapshot
                                        </button>
                                    </div>

                                    {selectedVersion.commit_hash && (
                                        <div className="flex items-center gap-2 mt-4 text-sm text-gray-400">
                                            <GitCommit size={14} />
                                            <code className="font-mono text-xs bg-white/5 px-2 py-1 rounded">
                                                {selectedVersion.commit_hash.slice(0, 7)}
                                            </code>
                                            {selectedVersion.commit_message && (
                                                <span className="truncate">{selectedVersion.commit_message}</span>
                                            )}
                                        </div>
                                    )}

                                    {/* Stats */}
                                    <div className="grid grid-cols-4 gap-4 mt-6">
                                        <div className="text-center p-3 rounded-lg bg-white/5">
                                            <p className="text-2xl font-bold">{selectedVersion.total_endpoints}</p>
                                            <p className="text-xs text-gray-400">Total</p>
                                        </div>
                                        <div className="text-center p-3 rounded-lg bg-emerald-500/10">
                                            <p className="text-2xl font-bold text-emerald-400">+{selectedVersion.added_endpoints}</p>
                                            <p className="text-xs text-gray-400">Added</p>
                                        </div>
                                        <div className="text-center p-3 rounded-lg bg-amber-500/10">
                                            <p className="text-2xl font-bold text-amber-400">{selectedVersion.modified_endpoints}</p>
                                            <p className="text-xs text-gray-400">Modified</p>
                                        </div>
                                        <div className="text-center p-3 rounded-lg bg-red-500/10">
                                            <p className="text-2xl font-bold text-red-400">-{selectedVersion.removed_endpoints}</p>
                                            <p className="text-xs text-gray-400">Removed</p>
                                        </div>
                                    </div>
                                </GlassCard>

                                {/* Changes */}
                                <GlassCard className="p-6">
                                    <h3 className="text-sm font-medium mb-4 flex items-center gap-2">
                                        <FileText size={14} className="text-gray-400" />
                                        Changes in this version
                                    </h3>

                                    {changes.length === 0 ? (
                                        <p className="text-sm text-gray-500 text-center py-4">
                                            No changes recorded for this version
                                        </p>
                                    ) : (
                                        <div className="space-y-2">
                                            {changes.map((change) => (
                                                <div
                                                    key={change.id}
                                                    className={cn(
                                                        "p-3 rounded-lg flex items-center gap-3",
                                                        change.change_type === "added" && "bg-emerald-500/10",
                                                        change.change_type === "modified" && "bg-amber-500/10",
                                                        change.change_type === "removed" && "bg-red-500/10"
                                                    )}
                                                >
                                                    {change.change_type === "added" && <Plus size={14} className="text-emerald-400" />}
                                                    {change.change_type === "modified" && <Edit size={14} className="text-amber-400" />}
                                                    {change.change_type === "removed" && <Minus size={14} className="text-red-400" />}

                                                    <span className={cn(
                                                        "text-[10px] font-bold px-1.5 py-0.5 rounded",
                                                        METHOD_COLORS[change.method]
                                                    )}>
                                                        {change.method}
                                                    </span>

                                                    <span className="font-mono text-sm flex-1">{change.path}</span>

                                                    {change.is_breaking && (
                                                        <span className="text-[10px] px-2 py-0.5 bg-red-500/20 text-red-400 rounded flex items-center gap-1">
                                                            <AlertTriangle size={10} />
                                                            Breaking
                                                        </span>
                                                    )}
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </GlassCard>

                                {/* Changelog */}
                                {changelog && (
                                    <GlassCard className="p-6">
                                        <h3 className="text-sm font-medium mb-4 flex items-center gap-2">
                                            <FileText size={14} className="text-gray-400" />
                                            Changelog
                                        </h3>

                                        <div className="prose prose-invert prose-sm max-w-none">
                                            <pre className="whitespace-pre-wrap text-sm text-gray-300 bg-black/30 p-4 rounded-lg">
                                                {changelog}
                                            </pre>
                                        </div>
                                    </GlassCard>
                                )}
                            </>
                        ) : (
                            <GlassCard className="p-16 text-center">
                                <History size={48} className="mx-auto text-gray-600 mb-4" />
                                <p className="text-gray-400">Select a version to view details</p>
                                <p className="text-xs text-gray-600 mt-1">
                                    Or compare two versions to see the diff
                                </p>
                            </GlassCard>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
