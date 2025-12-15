"use client";

import React, { useState, useEffect } from "react";
import {
    Shield,
    Key,
    Users,
    Globe,
    Lock,
    FileText,
    Plus,
    Trash2,
    Copy,
    Check,
    AlertTriangle,
    Settings,
    RefreshCw
} from "lucide-react";
import { cn } from "@/lib/utils";
import { API_BASE_URL } from "@/lib/api";
import { GlassCard } from "@/components/ui/glass-card";

interface AuditLog {
    id: string;
    action: string;
    user_email: string | null;
    resource_type: string | null;
    resource_name: string | null;
    description: string | null;
    ip_address: string | null;
    created_at: string;
}

interface IPWhitelistEntry {
    id: string;
    ip_address: string | null;
    cidr_block: string | null;
    label: string | null;
    is_enabled: boolean;
    created_at: string;
}

interface APIKey {
    id: string;
    name: string;
    key_prefix: string;
    scopes: string[];
    expires_at: string | null;
    last_used_at: string | null;
    use_count: number;
    is_active: boolean;
    created_at: string;
}

interface SecuritySettings {
    min_password_length: number;
    require_uppercase: boolean;
    require_numbers: boolean;
    require_special_chars: boolean;
    session_timeout_minutes: number;
    mfa_required: boolean;
    ip_whitelist_enabled: boolean;
    api_rate_limit_per_minute: number;
    data_retention_days: number;
}

type TabType = "audit" | "sso" | "ip" | "api-keys" | "settings";

export default function SecurityPage() {
    const [activeTab, setActiveTab] = useState<TabType>("audit");
    const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
    const [ipWhitelist, setIpWhitelist] = useState<IPWhitelistEntry[]>([]);
    const [apiKeys, setApiKeys] = useState<APIKey[]>([]);
    const [settings, setSettings] = useState<SecuritySettings | null>(null);
    const [loading, setLoading] = useState(true);
    const [newKeyName, setNewKeyName] = useState("");
    const [newIp, setNewIp] = useState("");
    const [newIpLabel, setNewIpLabel] = useState("");
    const [copied, setCopied] = useState(false);

    useEffect(() => {
        fetchData();
    }, [activeTab]);

    const fetchData = async () => {
        setLoading(true);
        try {
            if (activeTab === "audit") {
                const res = await fetch(`${API_BASE_URL}/api/security/audit-logs?limit=50`);
                if (res.ok) setAuditLogs(await res.json());
            } else if (activeTab === "ip") {
                const res = await fetch(`${API_BASE_URL}/api/security/ip-whitelist`);
                if (res.ok) setIpWhitelist(await res.json());
            } else if (activeTab === "api-keys") {
                const res = await fetch(`${API_BASE_URL}/api/security/api-keys`);
                if (res.ok) setApiKeys(await res.json());
            } else if (activeTab === "settings") {
                const res = await fetch(`${API_BASE_URL}/api/security/settings`);
                if (res.ok) setSettings(await res.json());
            }
        } catch (e) {
            console.error("Failed to fetch security data:", e);
        } finally {
            setLoading(false);
        }
    };

    const createApiKey = async () => {
        if (!newKeyName) return;
        try {
            const res = await fetch(`${API_BASE_URL}/api/security/api-keys`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ name: newKeyName, scopes: ["read", "write"] })
            });
            if (res.ok) {
                const data = await res.json();
                alert(`API Key created!\n\nKey: ${data.key}\n\nSave this key securely - it won't be shown again.`);
                setNewKeyName("");
                fetchData();
            }
        } catch (e) {
            console.error("Failed to create API key:", e);
        }
    };

    const revokeApiKey = async (keyId: string) => {
        try {
            await fetch(`${API_BASE_URL}/api/security/api-keys/${keyId}`, {
                method: "DELETE"
            });
            fetchData();
        } catch (e) {
            console.error("Failed to revoke API key:", e);
        }
    };

    const addIp = async () => {
        if (!newIp) return;
        try {
            await fetch(`${API_BASE_URL}/api/security/ip-whitelist`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ ip_address: newIp, label: newIpLabel || null })
            });
            setNewIp("");
            setNewIpLabel("");
            fetchData();
        } catch (e) {
            console.error("Failed to add IP:", e);
        }
    };

    const removeIp = async (entryId: string) => {
        try {
            await fetch(`${API_BASE_URL}/api/security/ip-whitelist/${entryId}`, {
                method: "DELETE"
            });
            fetchData();
        } catch (e) {
            console.error("Failed to remove IP:", e);
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
        { id: "audit", icon: FileText, label: "Audit Logs" },
        { id: "sso", icon: Users, label: "SSO / SAML" },
        { id: "ip", icon: Globe, label: "IP Whitelist" },
        { id: "api-keys", icon: Key, label: "API Keys" },
        { id: "settings", icon: Settings, label: "Settings" }
    ];

    return (
        <div className="min-h-screen bg-[#0a0a0a] text-white">
            {/* Header */}
            <header className="border-b border-white/10 bg-black/50 backdrop-blur-sm sticky top-0 z-50">
                <div className="max-w-6xl mx-auto px-6 py-4">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-red-500 to-orange-600 flex items-center justify-center">
                            <Shield size={20} />
                        </div>
                        <div>
                            <h1 className="text-xl font-semibold">Security & Compliance</h1>
                            <p className="text-xs text-gray-500">SOC 2 ready security controls</p>
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
                                    ? "bg-red-500/20 text-red-300 border border-red-500/30"
                                    : "text-gray-400 hover:text-white hover:bg-white/5"
                            )}
                        >
                            <tab.icon size={14} />
                            {tab.label}
                        </button>
                    ))}
                </div>

                {/* Audit Logs */}
                {activeTab === "audit" && (
                    <GlassCard className="p-6">
                        <h3 className="text-sm font-medium mb-4 flex items-center gap-2">
                            <FileText size={14} className="text-blue-400" />
                            Audit Logs
                            <span className="ml-auto text-xs text-gray-500">Last 7 days</span>
                        </h3>

                        {auditLogs.length === 0 ? (
                            <p className="text-sm text-gray-500 text-center py-8">No audit logs yet</p>
                        ) : (
                            <div className="space-y-2 max-h-[500px] overflow-y-auto">
                                {auditLogs.map((log) => (
                                    <div
                                        key={log.id}
                                        className="p-3 rounded-lg bg-white/5 flex items-center gap-3"
                                    >
                                        <div className="flex-1">
                                            <div className="flex items-center gap-2">
                                                <span className="text-sm font-medium">{log.action}</span>
                                                {log.resource_name && (
                                                    <span className="text-xs text-gray-400">• {log.resource_name}</span>
                                                )}
                                            </div>
                                            {log.description && (
                                                <p className="text-xs text-gray-500">{log.description}</p>
                                            )}
                                        </div>
                                        <div className="text-right">
                                            <p className="text-xs text-gray-400">{log.user_email || "System"}</p>
                                            <p className="text-[10px] text-gray-600">{formatDate(log.created_at)}</p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </GlassCard>
                )}

                {/* SSO */}
                {activeTab === "sso" && (
                    <GlassCard className="p-6">
                        <h3 className="text-sm font-medium mb-4 flex items-center gap-2">
                            <Users size={14} className="text-purple-400" />
                            Single Sign-On (SSO)
                        </h3>

                        <div className="grid grid-cols-2 gap-4">
                            {["SAML 2.0", "OpenID Connect", "Azure AD", "Okta"].map((provider) => (
                                <button
                                    key={provider}
                                    className="p-4 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-left transition-colors"
                                >
                                    <p className="font-medium">{provider}</p>
                                    <p className="text-xs text-gray-500">Click to configure</p>
                                </button>
                            ))}
                        </div>

                        <p className="text-xs text-gray-500 mt-4">
                            Enterprise SSO enables your team to use existing identity providers.
                        </p>
                    </GlassCard>
                )}

                {/* IP Whitelist */}
                {activeTab === "ip" && (
                    <GlassCard className="p-6">
                        <h3 className="text-sm font-medium mb-4 flex items-center gap-2">
                            <Globe size={14} className="text-cyan-400" />
                            IP Whitelist
                        </h3>

                        <div className="flex gap-2 mb-4">
                            <input
                                type="text"
                                value={newIp}
                                onChange={(e) => setNewIp(e.target.value)}
                                placeholder="IP address (e.g., 192.168.1.1)"
                                className="flex-1 px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-sm focus:outline-none"
                            />
                            <input
                                type="text"
                                value={newIpLabel}
                                onChange={(e) => setNewIpLabel(e.target.value)}
                                placeholder="Label (optional)"
                                className="w-40 px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-sm focus:outline-none"
                            />
                            <button
                                onClick={addIp}
                                disabled={!newIp}
                                className="px-4 py-2 bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-300 rounded-lg text-sm disabled:opacity-50"
                            >
                                <Plus size={16} />
                            </button>
                        </div>

                        {ipWhitelist.length === 0 ? (
                            <p className="text-sm text-gray-500 text-center py-8">No IPs whitelisted</p>
                        ) : (
                            <div className="space-y-2">
                                {ipWhitelist.map((entry) => (
                                    <div
                                        key={entry.id}
                                        className="p-3 rounded-lg bg-white/5 flex items-center gap-3"
                                    >
                                        <code className="text-sm font-mono">{entry.ip_address || entry.cidr_block}</code>
                                        {entry.label && <span className="text-xs text-gray-400">{entry.label}</span>}
                                        <span className="ml-auto text-[10px] text-gray-600">
                                            {formatDate(entry.created_at)}
                                        </span>
                                        <button
                                            onClick={() => removeIp(entry.id)}
                                            className="p-1.5 hover:bg-red-500/20 text-gray-500 hover:text-red-400 rounded"
                                        >
                                            <Trash2 size={14} />
                                        </button>
                                    </div>
                                ))}
                            </div>
                        )}
                    </GlassCard>
                )}

                {/* API Keys */}
                {activeTab === "api-keys" && (
                    <GlassCard className="p-6">
                        <h3 className="text-sm font-medium mb-4 flex items-center gap-2">
                            <Key size={14} className="text-amber-400" />
                            API Keys
                        </h3>

                        <div className="flex gap-2 mb-4">
                            <input
                                type="text"
                                value={newKeyName}
                                onChange={(e) => setNewKeyName(e.target.value)}
                                placeholder="Key name (e.g., CI/CD Pipeline)"
                                className="flex-1 px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-sm focus:outline-none"
                            />
                            <button
                                onClick={createApiKey}
                                disabled={!newKeyName}
                                className="px-4 py-2 bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 rounded-lg text-sm disabled:opacity-50 flex items-center gap-2"
                            >
                                <Plus size={14} />
                                Create Key
                            </button>
                        </div>

                        {apiKeys.length === 0 ? (
                            <p className="text-sm text-gray-500 text-center py-8">No API keys created</p>
                        ) : (
                            <div className="space-y-2">
                                {apiKeys.map((key) => (
                                    <div
                                        key={key.id}
                                        className={cn(
                                            "p-3 rounded-lg flex items-center gap-3",
                                            key.is_active ? "bg-white/5" : "bg-red-500/10"
                                        )}
                                    >
                                        <div className="flex-1">
                                            <div className="flex items-center gap-2">
                                                <span className="font-medium">{key.name}</span>
                                                <code className="text-xs text-gray-500 bg-white/5 px-2 py-0.5 rounded">
                                                    {key.key_prefix}...
                                                </code>
                                                {!key.is_active && (
                                                    <span className="text-[10px] px-1.5 py-0.5 bg-red-500/20 text-red-400 rounded">
                                                        Revoked
                                                    </span>
                                                )}
                                            </div>
                                            <p className="text-xs text-gray-500">
                                                Used {key.use_count} times
                                                {key.last_used_at && ` • Last: ${formatDate(key.last_used_at)}`}
                                            </p>
                                        </div>
                                        {key.is_active && (
                                            <button
                                                onClick={() => revokeApiKey(key.id)}
                                                className="px-3 py-1 text-xs bg-red-500/10 hover:bg-red-500/20 text-red-400 rounded"
                                            >
                                                Revoke
                                            </button>
                                        )}
                                    </div>
                                ))}
                            </div>
                        )}
                    </GlassCard>
                )}

                {/* Settings */}
                {activeTab === "settings" && settings && (
                    <GlassCard className="p-6">
                        <h3 className="text-sm font-medium mb-4 flex items-center gap-2">
                            <Settings size={14} className="text-gray-400" />
                            Security Settings
                        </h3>

                        <div className="space-y-4">
                            <div className="flex items-center justify-between p-3 rounded-lg bg-white/5">
                                <div>
                                    <p className="text-sm font-medium">MFA Required</p>
                                    <p className="text-xs text-gray-500">Require multi-factor authentication</p>
                                </div>
                                <span className={cn(
                                    "text-xs px-2 py-1 rounded",
                                    settings.mfa_required ? "bg-emerald-500/10 text-emerald-400" : "bg-gray-500/10 text-gray-400"
                                )}>
                                    {settings.mfa_required ? "Enabled" : "Disabled"}
                                </span>
                            </div>

                            <div className="flex items-center justify-between p-3 rounded-lg bg-white/5">
                                <div>
                                    <p className="text-sm font-medium">Session Timeout</p>
                                    <p className="text-xs text-gray-500">Auto-logout after inactivity</p>
                                </div>
                                <span className="text-sm">{settings.session_timeout_minutes} min</span>
                            </div>

                            <div className="flex items-center justify-between p-3 rounded-lg bg-white/5">
                                <div>
                                    <p className="text-sm font-medium">Password Policy</p>
                                    <p className="text-xs text-gray-500">Minimum length & requirements</p>
                                </div>
                                <span className="text-sm">{settings.min_password_length}+ chars</span>
                            </div>

                            <div className="flex items-center justify-between p-3 rounded-lg bg-white/5">
                                <div>
                                    <p className="text-sm font-medium">Data Retention</p>
                                    <p className="text-xs text-gray-500">Keep data for compliance</p>
                                </div>
                                <span className="text-sm">{settings.data_retention_days} days</span>
                            </div>
                        </div>
                    </GlassCard>
                )}
            </div>
        </div>
    );
}
