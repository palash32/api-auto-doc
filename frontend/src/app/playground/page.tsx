"use client";

import React, { useState, useEffect } from "react";
import { useSearchParams } from "next/navigation";
import {
    Play,
    Save,
    Clock,
    Key,
    Settings,
    Copy,
    Check,
    ChevronDown,
    Trash2,
    Plus,
    Download,
    History,
    Lock,
    Unlock
} from "lucide-react";
import { cn } from "@/lib/utils";
import { API_BASE_URL } from "@/lib/api";
import { GlassCard } from "@/components/ui/glass-card";

// HTTP method colors
const METHOD_COLORS: Record<string, string> = {
    GET: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
    POST: "bg-blue-500/20 text-blue-400 border-blue-500/30",
    PUT: "bg-amber-500/20 text-amber-400 border-amber-500/30",
    PATCH: "bg-purple-500/20 text-purple-400 border-purple-500/30",
    DELETE: "bg-red-500/20 text-red-400 border-red-500/30",
};

const METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE"];

interface Header {
    key: string;
    value: string;
    enabled: boolean;
}

interface RequestHistory {
    id: string;
    method: string;
    url: string;
    response_status?: string;
    response_time_ms?: string;
    created_at: string;
    is_saved: boolean;
    name?: string;
}

interface SavedToken {
    id: string;
    name: string;
    prefix?: string;
    token_type: string;
}

export default function PlaygroundPage() {
    const searchParams = useSearchParams();

    // Get URL parameters for pre-filling
    const paramMethod = searchParams.get('method');
    const paramPath = searchParams.get('path');
    const paramBody = searchParams.get('body');

    // Request state
    const [method, setMethod] = useState(paramMethod?.toUpperCase() || "GET");
    const [url, setUrl] = useState(paramPath ? `${API_BASE_URL}${paramPath}` : "");
    const [headers, setHeaders] = useState<Header[]>([
        { key: "Content-Type", value: "application/json", enabled: true }
    ]);
    const [body, setBody] = useState(paramBody || "");
    const [activeTab, setActiveTab] = useState<"headers" | "body" | "auth">("headers");

    // Response state
    const [response, setResponse] = useState<{
        status: number;
        headers: Record<string, string>;
        body: string;
        time_ms: number;
    } | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // History & Auth state
    const [history, setHistory] = useState<RequestHistory[]>([]);
    const [tokens, setTokens] = useState<SavedToken[]>([]);
    const [selectedTokenId, setSelectedTokenId] = useState<string | null>(null);
    const [copied, setCopied] = useState(false);

    // Sidebar state
    const [showHistory, setShowHistory] = useState(true);
    const [showTokenModal, setShowTokenModal] = useState(false);
    const [newTokenName, setNewTokenName] = useState("");
    const [newTokenValue, setNewTokenValue] = useState("");
    const [newTokenType, setNewTokenType] = useState("Bearer");

    // Fetch history and tokens on mount
    useEffect(() => {
        fetchHistory();
        fetchTokens();
    }, []);

    const fetchHistory = async () => {
        try {
            const res = await fetch("/api/playground/history?limit=20");
            if (res.ok) {
                const data = await res.json();
                setHistory(data);
            }
        } catch (e) {
            console.error("Failed to fetch history:", e);
        }
    };

    const fetchTokens = async () => {
        try {
            const res = await fetch("/api/playground/tokens");
            if (res.ok) {
                const data = await res.json();
                setTokens(data);
            }
        } catch (e) {
            console.error("Failed to fetch tokens:", e);
        }
    };

    const sendRequest = async () => {
        if (!url) {
            setError("Please enter a URL");
            return;
        }

        setLoading(true);
        setError(null);
        setResponse(null);

        try {
            // Build headers object from enabled headers
            const headersObj: Record<string, string> = {};
            headers.filter(h => h.enabled && h.key).forEach(h => {
                headersObj[h.key] = h.value;
            });

            const token = localStorage.getItem('token');
            const res = await fetch(`${API_BASE_URL}/api/playground/proxy`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    ...(token ? { "Authorization": `Bearer ${token}` } : {})
                },
                body: JSON.stringify({
                    method,
                    url,
                    headers: headersObj,
                    body: body || null,
                    token_id: selectedTokenId
                })
            });

            if (!res.ok) {
                const errData = await res.json();
                throw new Error(errData.detail || "Request failed");
            }

            const data = await res.json();
            setResponse(data);
            fetchHistory(); // Refresh history

        } catch (e: any) {
            setError(e.message || "Request failed");
        } finally {
            setLoading(false);
        }
    };

    const addHeader = () => {
        setHeaders([...headers, { key: "", value: "", enabled: true }]);
    };

    const removeHeader = (index: number) => {
        setHeaders(headers.filter((_, i) => i !== index));
    };

    const updateHeader = (index: number, field: "key" | "value" | "enabled", value: string | boolean) => {
        const newHeaders = [...headers];
        newHeaders[index] = { ...newHeaders[index], [field]: value };
        setHeaders(newHeaders);
    };

    const loadFromHistory = (item: RequestHistory) => {
        setMethod(item.method);
        setUrl(item.url);
    };

    const copyResponse = () => {
        if (response?.body) {
            navigator.clipboard.writeText(response.body);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        }
    };

    const exportAsCurl = () => {
        let curl = `curl -X ${method} "${url}"`;
        headers.filter(h => h.enabled && h.key).forEach(h => {
            curl += ` \\\n  -H "${h.key}: ${h.value}"`;
        });
        if (body && method !== "GET") {
            curl += ` \\\n  -d '${body}'`;
        }
        navigator.clipboard.writeText(curl);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    const getStatusColor = (status: number) => {
        if (status >= 200 && status < 300) return "text-emerald-400";
        if (status >= 300 && status < 400) return "text-blue-400";
        if (status >= 400 && status < 500) return "text-amber-400";
        return "text-red-400";
    };

    const formatJson = (str: string) => {
        try {
            return JSON.stringify(JSON.parse(str), null, 2);
        } catch {
            return str;
        }
    };

    const clearHistory = async () => {
        try {
            await fetch("/api/playground/history", { method: "DELETE" });
            setHistory([]);
        } catch (e) {
            console.error("Failed to clear history:", e);
            // Clear locally anyway
            setHistory([]);
        }
    };

    const addToken = async () => {
        if (!newTokenName || !newTokenValue) return;

        try {
            const res = await fetch("/api/playground/tokens", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    name: newTokenName,
                    token: newTokenValue,
                    token_type: newTokenType
                })
            });

            if (res.ok) {
                fetchTokens();
                setNewTokenName("");
                setNewTokenValue("");
                setShowTokenModal(false);
            }
        } catch (e) {
            console.error("Failed to add token:", e);
        }
    };

    return (
        <div className="min-h-screen bg-[#0a0a0a] text-white">
            {/* Header */}
            <header className="border-b border-white/10 bg-black/50 backdrop-blur-sm sticky top-0 z-50">
                <div className="max-w-[1800px] mx-auto px-6 py-4 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
                            <Play size={20} />
                        </div>
                        <div>
                            <h1 className="text-xl font-semibold">API Playground</h1>
                            <p className="text-xs text-gray-500">Test your APIs in real-time</p>
                        </div>
                    </div>

                    <div className="flex items-center gap-3">
                        <button
                            onClick={() => setShowHistory(!showHistory)}
                            className={cn(
                                "px-3 py-2 rounded-lg text-sm flex items-center gap-2 transition-colors",
                                showHistory ? "bg-white/10 text-white" : "text-gray-400 hover:text-white"
                            )}
                        >
                            <History size={16} />
                            History
                        </button>
                        <button
                            onClick={() => setShowTokenModal(true)}
                            className="px-3 py-2 rounded-lg text-sm flex items-center gap-2 text-gray-400 hover:text-white transition-colors"
                        >
                            <Key size={16} />
                            Token Vault
                        </button>
                    </div>
                </div>
            </header>

            {/* Token Modal */}
            {showTokenModal && (
                <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-[100]">
                    <div className="bg-gray-900 border border-white/10 rounded-2xl p-6 w-full max-w-md">
                        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                            <Key className="text-purple-400" size={20} />
                            Add New Token
                        </h3>
                        <div className="space-y-4">
                            <input
                                type="text"
                                placeholder="Token Name (e.g., Production API Key)"
                                value={newTokenName}
                                onChange={(e) => setNewTokenName(e.target.value)}
                                className="w-full px-4 py-3 rounded-lg bg-white/5 border border-white/10 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500/50"
                            />
                            <select
                                value={newTokenType}
                                onChange={(e) => setNewTokenType(e.target.value)}
                                className="w-full px-4 py-3 rounded-lg bg-white/5 border border-white/10 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500/50"
                            >
                                <option value="Bearer">Bearer Token</option>
                                <option value="API Key">API Key</option>
                                <option value="Basic">Basic Auth</option>
                            </select>
                            <input
                                type="password"
                                placeholder="Token Value"
                                value={newTokenValue}
                                onChange={(e) => setNewTokenValue(e.target.value)}
                                className="w-full px-4 py-3 rounded-lg bg-white/5 border border-white/10 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-purple-500/50"
                            />
                            <div className="flex gap-3">
                                <button
                                    onClick={() => setShowTokenModal(false)}
                                    className="flex-1 px-4 py-2 rounded-lg bg-white/5 hover:bg-white/10 text-sm transition-colors"
                                >
                                    Cancel
                                </button>
                                <button
                                    onClick={addToken}
                                    className="flex-1 px-4 py-2 rounded-lg bg-purple-500 hover:bg-purple-600 text-sm font-medium transition-colors"
                                >
                                    Save Token
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            <div className="max-w-[1800px] mx-auto p-6">
                <div className="grid grid-cols-12 gap-6">

                    {/* History Sidebar */}
                    {showHistory && (
                        <aside className="col-span-3 space-y-4">
                            <GlassCard className="p-4">
                                <div className="flex items-center justify-between mb-4">
                                    <h3 className="text-sm font-medium flex items-center gap-2">
                                        <Clock size={14} className="text-blue-400" />
                                        Recent Requests
                                    </h3>
                                    <button
                                        onClick={clearHistory}
                                        className="text-xs text-gray-500 hover:text-red-400 transition-colors"
                                    >
                                        Clear
                                    </button>
                                </div>

                                <div className="space-y-2 max-h-[600px] overflow-y-auto">
                                    {history.length === 0 ? (
                                        <p className="text-xs text-gray-500 text-center py-4">
                                            No requests yet
                                        </p>
                                    ) : (
                                        history.map((item) => (
                                            <button
                                                key={item.id}
                                                onClick={() => loadFromHistory(item)}
                                                className="w-full text-left p-3 rounded-lg bg-white/5 hover:bg-white/10 transition-colors group"
                                            >
                                                <div className="flex items-center gap-2 mb-1">
                                                    <span className={cn(
                                                        "text-[10px] font-mono px-1.5 py-0.5 rounded",
                                                        METHOD_COLORS[item.method]
                                                    )}>
                                                        {item.method}
                                                    </span>
                                                    {item.response_status && (
                                                        <span className={cn(
                                                            "text-[10px]",
                                                            getStatusColor(parseInt(item.response_status))
                                                        )}>
                                                            {item.response_status}
                                                        </span>
                                                    )}
                                                    {item.is_saved && (
                                                        <Save size={10} className="text-amber-400" />
                                                    )}
                                                </div>
                                                <p className="text-xs text-gray-400 truncate">
                                                    {item.url}
                                                </p>
                                                {item.response_time_ms && (
                                                    <p className="text-[10px] text-gray-600 mt-1">
                                                        {item.response_time_ms}ms
                                                    </p>
                                                )}
                                            </button>
                                        ))
                                    )}
                                </div>
                            </GlassCard>

                            {/* Saved Tokens Summary */}
                            <GlassCard className="p-4">
                                <h3 className="text-sm font-medium flex items-center gap-2 mb-3">
                                    <Key size={14} className="text-purple-400" />
                                    Auth Tokens
                                </h3>
                                <div className="space-y-2">
                                    {tokens.length === 0 ? (
                                        <p className="text-xs text-gray-500">No tokens saved</p>
                                    ) : (
                                        tokens.map((token) => (
                                            <button
                                                key={token.id}
                                                onClick={() => setSelectedTokenId(
                                                    selectedTokenId === token.id ? null : token.id
                                                )}
                                                className={cn(
                                                    "w-full text-left p-2 rounded-lg text-xs transition-colors flex items-center gap-2",
                                                    selectedTokenId === token.id
                                                        ? "bg-purple-500/20 border border-purple-500/30"
                                                        : "bg-white/5 hover:bg-white/10"
                                                )}
                                            >
                                                {selectedTokenId === token.id ? (
                                                    <Unlock size={12} className="text-purple-400" />
                                                ) : (
                                                    <Lock size={12} className="text-gray-500" />
                                                )}
                                                <span>{token.name}</span>
                                                <span className="text-gray-500 ml-auto">{token.prefix}</span>
                                            </button>
                                        ))
                                    )}
                                    <button className="w-full py-2 text-xs text-gray-500 hover:text-white flex items-center justify-center gap-1">
                                        <Plus size={12} /> Add Token
                                    </button>
                                </div>
                            </GlassCard>
                        </aside>
                    )}

                    {/* Main Content */}
                    <main className={cn(
                        "space-y-6",
                        showHistory ? "col-span-9" : "col-span-12"
                    )}>
                        {/* Request Builder */}
                        <GlassCard className="p-6">
                            {/* URL Bar */}
                            <div className="flex gap-3 mb-6">
                                {/* Method Selector */}
                                <div className="relative">
                                    <select
                                        value={method}
                                        onChange={(e) => setMethod(e.target.value)}
                                        className={cn(
                                            "appearance-none px-4 py-3 pr-10 rounded-lg font-mono text-sm font-medium cursor-pointer border",
                                            METHOD_COLORS[method],
                                            "bg-transparent focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                                        )}
                                    >
                                        {METHODS.map((m) => (
                                            <option key={m} value={m} className="bg-gray-900">
                                                {m}
                                            </option>
                                        ))}
                                    </select>
                                    <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none opacity-50" />
                                </div>

                                {/* URL Input */}
                                <input
                                    type="text"
                                    value={url}
                                    onChange={(e) => setUrl(e.target.value)}
                                    placeholder="Enter request URL..."
                                    className="flex-1 px-4 py-3 rounded-lg bg-white/5 border border-white/10 text-white placeholder-gray-500 font-mono text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50"
                                />

                                {/* Send Button */}
                                <button
                                    onClick={sendRequest}
                                    disabled={loading}
                                    className={cn(
                                        "px-6 py-3 rounded-lg font-medium text-sm flex items-center gap-2 transition-all btn-press",
                                        "bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700",
                                        loading && "opacity-50 cursor-not-allowed"
                                    )}
                                >
                                    {loading ? (
                                        <>
                                            <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                            Sending...
                                        </>
                                    ) : (
                                        <>
                                            <Play size={16} />
                                            Send
                                        </>
                                    )}
                                </button>
                            </div>

                            {/* Tabs */}
                            <div className="flex gap-1 mb-4 border-b border-white/10 pb-2">
                                {(["headers", "body", "auth"] as const).map((tab) => (
                                    <button
                                        key={tab}
                                        onClick={() => setActiveTab(tab)}
                                        className={cn(
                                            "px-4 py-2 text-sm capitalize rounded-lg transition-colors",
                                            activeTab === tab
                                                ? "bg-white/10 text-white"
                                                : "text-gray-500 hover:text-white"
                                        )}
                                    >
                                        {tab}
                                        {tab === "headers" && headers.filter(h => h.enabled).length > 0 && (
                                            <span className="ml-2 px-1.5 py-0.5 text-[10px] bg-blue-500/20 text-blue-400 rounded">
                                                {headers.filter(h => h.enabled).length}
                                            </span>
                                        )}
                                    </button>
                                ))}
                            </div>

                            {/* Tab Content */}
                            <div className="min-h-[200px]">
                                {activeTab === "headers" && (
                                    <div className="space-y-2">
                                        {headers.map((header, i) => (
                                            <div key={i} className="flex gap-2 items-center">
                                                <input
                                                    type="checkbox"
                                                    checked={header.enabled}
                                                    onChange={(e) => updateHeader(i, "enabled", e.target.checked)}
                                                    className="w-4 h-4 rounded bg-white/10 border-white/20"
                                                />
                                                <input
                                                    type="text"
                                                    value={header.key}
                                                    onChange={(e) => updateHeader(i, "key", e.target.value)}
                                                    placeholder="Header name"
                                                    className="flex-1 px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-sm font-mono placeholder-gray-600 focus:outline-none focus:ring-1 focus:ring-blue-500/50"
                                                />
                                                <input
                                                    type="text"
                                                    value={header.value}
                                                    onChange={(e) => updateHeader(i, "value", e.target.value)}
                                                    placeholder="Value"
                                                    className="flex-1 px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-sm font-mono placeholder-gray-600 focus:outline-none focus:ring-1 focus:ring-blue-500/50"
                                                />
                                                <button
                                                    onClick={() => removeHeader(i)}
                                                    className="p-2 text-gray-500 hover:text-red-400 transition-colors"
                                                >
                                                    <Trash2 size={14} />
                                                </button>
                                            </div>
                                        ))}
                                        <button
                                            onClick={addHeader}
                                            className="text-sm text-gray-500 hover:text-white flex items-center gap-1 py-2"
                                        >
                                            <Plus size={14} /> Add header
                                        </button>
                                    </div>
                                )}

                                {activeTab === "body" && (
                                    <textarea
                                        value={body}
                                        onChange={(e) => setBody(e.target.value)}
                                        placeholder='{"key": "value"}'
                                        className="w-full h-48 px-4 py-3 rounded-lg bg-white/5 border border-white/10 text-sm font-mono placeholder-gray-600 focus:outline-none focus:ring-1 focus:ring-blue-500/50 resize-none"
                                    />
                                )}

                                {activeTab === "auth" && (
                                    <div className="space-y-4">
                                        <p className="text-sm text-gray-400">
                                            Select a saved token from the sidebar or configure authentication manually.
                                        </p>
                                        {selectedTokenId && (
                                            <div className="p-3 rounded-lg bg-purple-500/10 border border-purple-500/30 text-sm">
                                                <p className="text-purple-400 flex items-center gap-2">
                                                    <Unlock size={14} />
                                                    Token selected - will be injected on send
                                                </p>
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        </GlassCard>

                        {/* Response Section */}
                        <GlassCard className="p-6">
                            <div className="flex items-center justify-between mb-4">
                                <h3 className="text-sm font-medium">Response</h3>
                                {response && (
                                    <div className="flex items-center gap-4">
                                        <span className={cn("text-sm font-mono", getStatusColor(response.status))}>
                                            {response.status}
                                        </span>
                                        <span className="text-xs text-gray-500">
                                            {response.time_ms}ms
                                        </span>
                                        <button
                                            onClick={copyResponse}
                                            className="p-2 rounded-lg hover:bg-white/10 transition-colors text-gray-400 hover:text-white"
                                        >
                                            {copied ? <Check size={14} className="text-emerald-400" /> : <Copy size={14} />}
                                        </button>
                                        <button
                                            onClick={exportAsCurl}
                                            className="p-2 rounded-lg hover:bg-white/10 transition-colors text-gray-400 hover:text-white"
                                            title="Export as cURL"
                                        >
                                            <Download size={14} />
                                        </button>
                                    </div>
                                )}
                            </div>

                            {error && (
                                <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
                                    {error}
                                </div>
                            )}

                            {!response && !error && (
                                <div className="h-48 flex items-center justify-center text-gray-500 text-sm">
                                    Send a request to see the response
                                </div>
                            )}

                            {response && (
                                <pre className="p-4 rounded-lg bg-black/50 border border-white/10 text-sm font-mono overflow-auto max-h-[400px] text-gray-300">
                                    {formatJson(response.body)}
                                </pre>
                            )}
                        </GlassCard>
                    </main>
                </div>
            </div>
        </div>
    );
}
