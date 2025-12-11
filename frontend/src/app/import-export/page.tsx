"use client";

import React, { useState, useEffect } from "react";
import {
    Upload,
    Download,
    FileJson,
    FileText,
    FileCode,
    Check,
    Clock,
    X,
    ChevronRight,
    ExternalLink
} from "lucide-react";
import { cn } from "@/lib/utils";
import { GlassCard } from "@/components/ui/glass-card";

interface Job {
    id: string;
    format: string;
    status: string;
    created_at: string;
}

const IMPORT_FORMATS = [
    { id: "openapi_3.0", name: "OpenAPI 3.0", icon: FileJson, color: "text-green-400" },
    { id: "swagger_2.0", name: "Swagger 2.0", icon: FileJson, color: "text-amber-400" },
    { id: "postman_2.1", name: "Postman Collection", icon: FileCode, color: "text-orange-400" }
];

const EXPORT_FORMATS = [
    { id: "openapi_3.0", name: "OpenAPI 3.0", icon: FileJson, ext: "json" },
    { id: "postman_2.1", name: "Postman Collection", icon: FileCode, ext: "json" },
    { id: "markdown", name: "Markdown", icon: FileText, ext: "md" },
    { id: "html", name: "HTML", icon: FileCode, ext: "html" }
];

const STATUS_ICONS: Record<string, { icon: any; class: string }> = {
    completed: { icon: Check, class: "text-emerald-400" },
    processing: { icon: Clock, class: "text-blue-400 animate-spin" },
    pending: { icon: Clock, class: "text-amber-400" },
    failed: { icon: X, class: "text-red-400" }
};

type TabType = "import" | "export" | "history";

export default function ImportExportPage() {
    const [activeTab, setActiveTab] = useState<TabType>("import");
    const [importContent, setImportContent] = useState("");
    const [selectedFormat, setSelectedFormat] = useState("openapi_3.0");
    const [repositoryId, setRepositoryId] = useState("");
    const [exportTitle, setExportTitle] = useState("");
    const [importJobs, setImportJobs] = useState<Job[]>([]);
    const [exportJobs, setExportJobs] = useState<Job[]>([]);
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<any>(null);

    useEffect(() => {
        if (activeTab === "history") {
            fetchJobs();
        }
    }, [activeTab]);

    const fetchJobs = async () => {
        try {
            const [importRes, exportRes] = await Promise.all([
                fetch("http://localhost:8000/api/import/jobs"),
                fetch("http://localhost:8000/api/export/jobs")
            ]);
            if (importRes.ok) setImportJobs(await importRes.json());
            if (exportRes.ok) setExportJobs(await exportRes.json());
        } catch (e) {
            console.error("Failed to fetch jobs:", e);
        }
    };

    const handleImport = async () => {
        if (!importContent || !repositoryId) return;
        setLoading(true);
        setResult(null);

        try {
            const res = await fetch("http://localhost:8000/api/import", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    repository_id: repositoryId,
                    format: selectedFormat,
                    content: importContent
                })
            });

            if (res.ok) {
                setResult(await res.json());
            }
        } catch (e) {
            console.error("Import failed:", e);
        } finally {
            setLoading(false);
        }
    };

    const handleExport = async (format: string) => {
        if (!repositoryId) {
            alert("Please enter a repository ID");
            return;
        }
        setLoading(true);

        try {
            const res = await fetch("http://localhost:8000/api/export", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    repository_id: repositoryId,
                    format: format,
                    title: exportTitle || "API Documentation"
                })
            });

            if (res.ok) {
                const data = await res.json();
                if (data.output_url) {
                    window.open(`http://localhost:8000${data.output_url}`, "_blank");
                }
            }
        } catch (e) {
            console.error("Export failed:", e);
        } finally {
            setLoading(false);
        }
    };

    const formatDate = (dateStr: string) => {
        return new Date(dateStr).toLocaleString("en-US", {
            month: "short",
            day: "numeric",
            hour: "2-digit",
            minute: "2-digit"
        });
    };

    const tabs = [
        { id: "import", icon: Upload, label: "Import" },
        { id: "export", icon: Download, label: "Export" },
        { id: "history", icon: Clock, label: "History" }
    ];

    return (
        <div className="min-h-screen bg-[#0a0a0a] text-white">
            <header className="border-b border-white/10 bg-black/50 backdrop-blur-sm sticky top-0 z-50">
                <div className="max-w-6xl mx-auto px-6 py-4">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center">
                            <FileJson size={20} />
                        </div>
                        <div>
                            <h1 className="text-xl font-semibold">Import / Export</h1>
                            <p className="text-xs text-gray-500">OpenAPI, Postman, Markdown, PDF</p>
                        </div>
                    </div>
                </div>
            </header>

            <div className="max-w-6xl mx-auto p-6">
                {/* Tabs */}
                <div className="flex gap-2 mb-6">
                    {tabs.map((tab) => (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id as TabType)}
                            className={cn(
                                "px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 transition-colors",
                                activeTab === tab.id
                                    ? "bg-violet-500/20 text-violet-300 border border-violet-500/30"
                                    : "text-gray-400 hover:text-white hover:bg-white/5"
                            )}
                        >
                            <tab.icon size={14} />
                            {tab.label}
                        </button>
                    ))}
                </div>

                {/* Repository ID Input */}
                <GlassCard className="p-4 mb-6">
                    <label className="text-xs text-gray-400">Repository ID</label>
                    <input
                        type="text"
                        value={repositoryId}
                        onChange={(e) => setRepositoryId(e.target.value)}
                        placeholder="Enter repository ID to import/export"
                        className="w-full mt-1 px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-sm focus:outline-none"
                    />
                </GlassCard>

                {/* Import Tab */}
                {activeTab === "import" && (
                    <div className="space-y-6">
                        <GlassCard className="p-6">
                            <h3 className="text-sm font-medium mb-4 flex items-center gap-2">
                                <Upload size={14} className="text-violet-400" />
                                Import API Specification
                            </h3>

                            <div className="flex gap-2 mb-4">
                                {IMPORT_FORMATS.map((fmt) => (
                                    <button
                                        key={fmt.id}
                                        onClick={() => setSelectedFormat(fmt.id)}
                                        className={cn(
                                            "px-3 py-2 rounded-lg text-sm flex items-center gap-2 transition-colors",
                                            selectedFormat === fmt.id
                                                ? "bg-violet-500/20 text-violet-300 border border-violet-500/30"
                                                : "bg-white/5 text-gray-400 hover:bg-white/10"
                                        )}
                                    >
                                        <fmt.icon size={14} className={fmt.color} />
                                        {fmt.name}
                                    </button>
                                ))}
                            </div>

                            <textarea
                                value={importContent}
                                onChange={(e) => setImportContent(e.target.value)}
                                placeholder="Paste your OpenAPI/Swagger/Postman JSON here..."
                                className="w-full h-64 px-4 py-3 rounded-lg bg-black/50 border border-white/10 text-sm font-mono focus:outline-none resize-none"
                            />

                            <button
                                onClick={handleImport}
                                disabled={loading || !importContent || !repositoryId}
                                className="mt-4 px-6 py-2 bg-violet-500/20 hover:bg-violet-500/30 text-violet-300 rounded-lg text-sm disabled:opacity-50 flex items-center gap-2"
                            >
                                {loading ? <Clock size={14} className="animate-spin" /> : <Upload size={14} />}
                                Import
                            </button>

                            {result && (
                                <div className="mt-4 p-4 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
                                    <p className="text-emerald-400 font-medium">Import Complete!</p>
                                    <p className="text-sm text-gray-400">
                                        {result.endpoints_imported} imported, {result.endpoints_updated} updated, {result.endpoints_skipped} skipped
                                    </p>
                                </div>
                            )}
                        </GlassCard>
                    </div>
                )}

                {/* Export Tab */}
                {activeTab === "export" && (
                    <div className="space-y-6">
                        <GlassCard className="p-4 mb-4">
                            <label className="text-xs text-gray-400">Export Title (optional)</label>
                            <input
                                type="text"
                                value={exportTitle}
                                onChange={(e) => setExportTitle(e.target.value)}
                                placeholder="API Documentation"
                                className="w-full mt-1 px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-sm focus:outline-none"
                            />
                        </GlassCard>

                        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                            {EXPORT_FORMATS.map((fmt) => (
                                <GlassCard
                                    key={fmt.id}
                                    className="p-6 hover:bg-white/5 cursor-pointer transition-colors"
                                    onClick={() => handleExport(fmt.id)}
                                >
                                    <fmt.icon size={32} className="text-violet-400 mb-3" />
                                    <p className="font-medium">{fmt.name}</p>
                                    <p className="text-xs text-gray-500">.{fmt.ext}</p>
                                    <div className="mt-3 flex items-center gap-1 text-xs text-violet-400">
                                        <Download size={12} />
                                        Export
                                    </div>
                                </GlassCard>
                            ))}
                        </div>
                    </div>
                )}

                {/* History Tab */}
                {activeTab === "history" && (
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        <GlassCard className="p-6">
                            <h3 className="text-sm font-medium mb-4 flex items-center gap-2">
                                <Upload size={14} className="text-green-400" />
                                Import History
                            </h3>
                            {importJobs.length === 0 ? (
                                <p className="text-sm text-gray-500 text-center py-4">No imports yet</p>
                            ) : (
                                <div className="space-y-2">
                                    {importJobs.map((job) => {
                                        const StatusIcon = STATUS_ICONS[job.status]?.icon || Clock;
                                        return (
                                            <div key={job.id} className="p-3 rounded-lg bg-white/5 flex items-center gap-3">
                                                <StatusIcon size={16} className={STATUS_ICONS[job.status]?.class} />
                                                <div className="flex-1">
                                                    <p className="text-sm">{job.format}</p>
                                                    <p className="text-xs text-gray-500">{formatDate(job.created_at)}</p>
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>
                            )}
                        </GlassCard>

                        <GlassCard className="p-6">
                            <h3 className="text-sm font-medium mb-4 flex items-center gap-2">
                                <Download size={14} className="text-blue-400" />
                                Export History
                            </h3>
                            {exportJobs.length === 0 ? (
                                <p className="text-sm text-gray-500 text-center py-4">No exports yet</p>
                            ) : (
                                <div className="space-y-2">
                                    {exportJobs.map((job) => {
                                        const StatusIcon = STATUS_ICONS[job.status]?.icon || Clock;
                                        return (
                                            <div key={job.id} className="p-3 rounded-lg bg-white/5 flex items-center gap-3">
                                                <StatusIcon size={16} className={STATUS_ICONS[job.status]?.class} />
                                                <div className="flex-1">
                                                    <p className="text-sm">{job.format}</p>
                                                    <p className="text-xs text-gray-500">{formatDate(job.created_at)}</p>
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>
                            )}
                        </GlassCard>
                    </div>
                )}
            </div>
        </div>
    );
}
