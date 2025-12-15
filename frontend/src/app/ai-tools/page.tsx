"use client";

import React, { useState } from "react";
import {
    Sparkles,
    Wand2,
    Code,
    FileCode,
    AlertTriangle,
    BarChart3,
    RefreshCw,
    Copy,
    Check,
    ChevronDown,
    Zap
} from "lucide-react";
import { cn } from "@/lib/utils";
import { API_BASE_URL } from "@/lib/api";
import { GlassCard } from "@/components/ui/glass-card";

export default function AIToolsPage() {
    const [activeTab, setActiveTab] = useState<"enhance" | "examples" | "types" | "quality">("enhance");
    const [loading, setLoading] = useState(false);
    const [copied, setCopied] = useState(false);

    // Enhance Description State
    const [description, setDescription] = useState("");
    const [enhancedResult, setEnhancedResult] = useState<{
        original: string;
        enhanced: string;
        summary: string;
        improvements: string[];
    } | null>(null);

    // Generate Examples State
    const [exampleMethod, setExampleMethod] = useState("GET");
    const [examplePath, setExamplePath] = useState("/api/users/{id}");
    const [examples, setExamples] = useState<Array<{
        language: string;
        code: string;
        description: string;
    }>>([]);

    // Type Inference State
    const [codeInput, setCodeInput] = useState(`def get_user(user_id: int):
    return User.query.get(user_id)`);
    const [language, setLanguage] = useState("python");
    const [typeResults, setTypeResults] = useState<Array<{
        param_name: string;
        inferred_type: string;
        confidence: number;
        reason: string;
    }>>([]);

    // Quality Score State
    const [qualityScore, setQualityScore] = useState<{
        overall_score: number;
        categories: Record<string, number>;
        issues: string[];
        suggestions: string[];
    } | null>(null);

    const enhanceDescription = async () => {
        setLoading(true);
        try {
            const res = await fetch(`${API_BASE_URL}/api/ai/enhance-description`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    description,
                    context: { method: "GET", path: "/api/example" }
                })
            });
            if (res.ok) {
                setEnhancedResult(await res.json());
            }
        } catch (e) {
            console.error("Enhancement failed:", e);
        } finally {
            setLoading(false);
        }
    };

    const generateExamples = async () => {
        setLoading(true);
        try {
            const res = await fetch(`${API_BASE_URL}/api/ai/generate-examples`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    method: exampleMethod,
                    path: examplePath,
                    languages: ["curl", "python", "javascript"]
                })
            });
            if (res.ok) {
                setExamples(await res.json());
            }
        } catch (e) {
            console.error("Example generation failed:", e);
        } finally {
            setLoading(false);
        }
    };

    const inferTypes = async () => {
        setLoading(true);
        try {
            const res = await fetch(`${API_BASE_URL}/api/ai/infer-types`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ code: codeInput, language })
            });
            if (res.ok) {
                setTypeResults(await res.json());
            }
        } catch (e) {
            console.error("Type inference failed:", e);
        } finally {
            setLoading(false);
        }
    };

    const copyToClipboard = (text: string) => {
        navigator.clipboard.writeText(text);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    return (
        <div className="min-h-screen bg-[#0a0a0a] text-white">
            {/* Header */}
            <header className="border-b border-white/10 bg-black/50 backdrop-blur-sm sticky top-0 z-50">
                <div className="max-w-5xl mx-auto px-6 py-4">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center">
                            <Sparkles size={20} />
                        </div>
                        <div>
                            <h1 className="text-xl font-semibold">AI Tools</h1>
                            <p className="text-xs text-gray-500">Enhance your API documentation with AI</p>
                        </div>
                    </div>
                </div>
            </header>

            <div className="max-w-5xl mx-auto p-6">
                {/* Tabs */}
                <div className="flex flex-wrap gap-2 mb-6">
                    {[
                        { id: "enhance", icon: Wand2, label: "Enhance Descriptions" },
                        { id: "examples", icon: Code, label: "Generate Examples" },
                        { id: "types", icon: FileCode, label: "Infer Types" },
                        { id: "quality", icon: BarChart3, label: "Quality Score" }
                    ].map((tab) => (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id as any)}
                            className={cn(
                                "px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 transition-colors",
                                activeTab === tab.id
                                    ? "bg-violet-500/20 text-violet-300 border border-violet-500/30"
                                    : "text-gray-400 hover:text-white bg-white/5"
                            )}
                        >
                            <tab.icon size={16} />
                            {tab.label}
                        </button>
                    ))}
                </div>

                {/* Enhance Descriptions Tab */}
                {activeTab === "enhance" && (
                    <div className="space-y-6">
                        <GlassCard className="p-6">
                            <h3 className="text-sm font-medium mb-4 flex items-center gap-2">
                                <Wand2 size={14} className="text-violet-400" />
                                Enhance API Description
                            </h3>

                            <textarea
                                value={description}
                                onChange={(e) => setDescription(e.target.value)}
                                placeholder="Enter a brief or unclear API description to enhance...

Example: 'get user'"
                                className="w-full h-32 px-4 py-3 rounded-lg bg-white/5 border border-white/10 text-sm placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-violet-500/50 resize-none"
                            />

                            <button
                                onClick={enhanceDescription}
                                disabled={loading || !description}
                                className="mt-4 px-4 py-2 bg-gradient-to-r from-violet-500 to-purple-600 rounded-lg text-sm font-medium flex items-center gap-2 disabled:opacity-50"
                            >
                                {loading ? (
                                    <RefreshCw size={14} className="animate-spin" />
                                ) : (
                                    <Zap size={14} />
                                )}
                                Enhance with AI
                            </button>
                        </GlassCard>

                        {enhancedResult && (
                            <GlassCard className="p-6">
                                <h3 className="text-sm font-medium mb-4 text-emerald-400">Enhanced Result</h3>

                                <div className="space-y-4">
                                    <div>
                                        <p className="text-xs text-gray-400 mb-1">Summary</p>
                                        <p className="text-sm bg-white/5 p-3 rounded-lg">{enhancedResult.summary}</p>
                                    </div>

                                    <div>
                                        <p className="text-xs text-gray-400 mb-1">Enhanced Description</p>
                                        <div className="text-sm bg-white/5 p-3 rounded-lg relative">
                                            {enhancedResult.enhanced}
                                            <button
                                                onClick={() => copyToClipboard(enhancedResult.enhanced)}
                                                className="absolute top-2 right-2 p-1.5 hover:bg-white/10 rounded"
                                            >
                                                {copied ? <Check size={14} className="text-emerald-400" /> : <Copy size={14} className="text-gray-500" />}
                                            </button>
                                        </div>
                                    </div>

                                    {enhancedResult.improvements.length > 0 && (
                                        <div>
                                            <p className="text-xs text-gray-400 mb-1">Improvements Made</p>
                                            <ul className="text-xs space-y-1">
                                                {enhancedResult.improvements.map((imp, i) => (
                                                    <li key={i} className="text-gray-300">• {imp}</li>
                                                ))}
                                            </ul>
                                        </div>
                                    )}
                                </div>
                            </GlassCard>
                        )}
                    </div>
                )}

                {/* Generate Examples Tab */}
                {activeTab === "examples" && (
                    <div className="space-y-6">
                        <GlassCard className="p-6">
                            <h3 className="text-sm font-medium mb-4 flex items-center gap-2">
                                <Code size={14} className="text-blue-400" />
                                Generate Code Examples
                            </h3>

                            <div className="flex gap-4 mb-4">
                                <select
                                    value={exampleMethod}
                                    onChange={(e) => setExampleMethod(e.target.value)}
                                    className="px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-sm"
                                >
                                    {["GET", "POST", "PUT", "PATCH", "DELETE"].map(m => (
                                        <option key={m} value={m}>{m}</option>
                                    ))}
                                </select>

                                <input
                                    type="text"
                                    value={examplePath}
                                    onChange={(e) => setExamplePath(e.target.value)}
                                    placeholder="/api/endpoint"
                                    className="flex-1 px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-sm font-mono"
                                />
                            </div>

                            <button
                                onClick={generateExamples}
                                disabled={loading}
                                className="px-4 py-2 bg-gradient-to-r from-blue-500 to-cyan-600 rounded-lg text-sm font-medium flex items-center gap-2 disabled:opacity-50"
                            >
                                {loading ? (
                                    <RefreshCw size={14} className="animate-spin" />
                                ) : (
                                    <Code size={14} />
                                )}
                                Generate Examples
                            </button>
                        </GlassCard>

                        {examples.length > 0 && (
                            <div className="space-y-4">
                                {examples.map((ex, i) => (
                                    <GlassCard key={i} className="p-4">
                                        <div className="flex items-center justify-between mb-2">
                                            <span className="text-xs font-medium text-gray-400 uppercase">{ex.language}</span>
                                            <button
                                                onClick={() => copyToClipboard(ex.code)}
                                                className="p-1.5 hover:bg-white/10 rounded text-gray-500 hover:text-white"
                                            >
                                                <Copy size={14} />
                                            </button>
                                        </div>
                                        <pre className="text-sm bg-black/30 p-3 rounded-lg overflow-x-auto">
                                            <code>{ex.code}</code>
                                        </pre>
                                    </GlassCard>
                                ))}
                            </div>
                        )}
                    </div>
                )}

                {/* Infer Types Tab */}
                {activeTab === "types" && (
                    <div className="space-y-6">
                        <GlassCard className="p-6">
                            <h3 className="text-sm font-medium mb-4 flex items-center gap-2">
                                <FileCode size={14} className="text-amber-400" />
                                Infer Parameter Types
                            </h3>

                            <div className="flex gap-2 mb-4">
                                <select
                                    value={language}
                                    onChange={(e) => setLanguage(e.target.value)}
                                    className="px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-sm"
                                >
                                    {["python", "javascript", "typescript", "java", "go"].map(l => (
                                        <option key={l} value={l}>{l}</option>
                                    ))}
                                </select>
                            </div>

                            <textarea
                                value={codeInput}
                                onChange={(e) => setCodeInput(e.target.value)}
                                className="w-full h-40 px-4 py-3 rounded-lg bg-black/30 border border-white/10 text-sm font-mono placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-amber-500/50 resize-none"
                            />

                            <button
                                onClick={inferTypes}
                                disabled={loading || !codeInput}
                                className="mt-4 px-4 py-2 bg-gradient-to-r from-amber-500 to-orange-600 rounded-lg text-sm font-medium flex items-center gap-2 disabled:opacity-50"
                            >
                                {loading ? (
                                    <RefreshCw size={14} className="animate-spin" />
                                ) : (
                                    <FileCode size={14} />
                                )}
                                Analyze Types
                            </button>
                        </GlassCard>

                        {typeResults.length > 0 && (
                            <GlassCard className="p-6">
                                <h3 className="text-sm font-medium mb-4 text-emerald-400">Inferred Types</h3>

                                <div className="space-y-3">
                                    {typeResults.map((tr, i) => (
                                        <div key={i} className="p-3 rounded-lg bg-white/5">
                                            <div className="flex items-center justify-between mb-1">
                                                <code className="text-sm font-mono text-blue-300">{tr.param_name}</code>
                                                <span className="text-xs text-gray-400">
                                                    {Math.round(tr.confidence * 100)}% confident
                                                </span>
                                            </div>
                                            <p className="text-sm">
                                                Type: <code className="text-amber-300">{tr.inferred_type}</code>
                                            </p>
                                            <p className="text-xs text-gray-500 mt-1">{tr.reason}</p>
                                        </div>
                                    ))}
                                </div>
                            </GlassCard>
                        )}
                    </div>
                )}

                {/* Quality Score Tab */}
                {activeTab === "quality" && (
                    <GlassCard className="p-6">
                        <h3 className="text-sm font-medium mb-4 flex items-center gap-2">
                            <BarChart3 size={14} className="text-pink-400" />
                            API Quality Score
                        </h3>

                        <p className="text-sm text-gray-400 mb-4">
                            Select a repository from the dashboard to analyze its API quality.
                        </p>

                        <div className="p-8 border-2 border-dashed border-white/10 rounded-lg text-center">
                            <BarChart3 size={32} className="mx-auto text-gray-600 mb-3" />
                            <p className="text-gray-500 text-sm">Quality analysis available from repository page</p>
                        </div>
                    </GlassCard>
                )}
            </div>
        </div>
    );
}
