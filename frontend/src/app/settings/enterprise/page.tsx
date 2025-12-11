"use client";

import React, { useState, useEffect } from "react";
import {
    Building,
    Shield,
    Headphones,
    Plug,
    BarChart3,
    Key,
    Plus,
    Trash2,
    CheckCircle,
    Clock,
    AlertTriangle,
    Send
} from "lucide-react";
import { cn } from "@/lib/utils";
import { GlassCard } from "@/components/ui/glass-card";

interface EnterpriseConfig {
    id: string;
    deployment_type: string;
    sla_tier: string;
    uptime_sla: number;
    response_time_sla: number;
    support_tier: string;
    dedicated_success_manager: string | null;
    volume_discount_percentage: number;
}

interface Integration {
    id: string;
    name: string;
    integration_type: string;
    description: string | null;
    webhook_url: string | null;
    is_enabled: boolean;
    error_count: number;
}

interface SupportTicket {
    id: string;
    ticket_number: string;
    subject: string;
    priority: string;
    status: string;
    created_at: string;
}

interface SLAMetric {
    period_start: string;
    uptime_percentage: number;
    avg_response_time_ms: number;
    sla_met: boolean;
}

type TabType = "overview" | "integrations" | "support" | "sla";

const STATUS_COLORS: Record<string, string> = {
    open: "bg-blue-500/10 text-blue-400",
    in_progress: "bg-amber-500/10 text-amber-400",
    resolved: "bg-emerald-500/10 text-emerald-400",
    closed: "bg-gray-500/10 text-gray-400"
};

const PRIORITY_COLORS: Record<string, string> = {
    critical: "bg-red-500/10 text-red-400",
    high: "bg-orange-500/10 text-orange-400",
    medium: "bg-amber-500/10 text-amber-400",
    low: "bg-gray-500/10 text-gray-400"
};

export default function EnterprisePage() {
    const [activeTab, setActiveTab] = useState<TabType>("overview");
    const [config, setConfig] = useState<EnterpriseConfig | null>(null);
    const [integrations, setIntegrations] = useState<Integration[]>([]);
    const [tickets, setTickets] = useState<SupportTicket[]>([]);
    const [slaMetrics, setSlaMetrics] = useState<SLAMetric[]>([]);
    const [loading, setLoading] = useState(true);
    const [newTicketSubject, setNewTicketSubject] = useState("");

    useEffect(() => {
        fetchData();
    }, [activeTab]);

    const fetchData = async () => {
        setLoading(true);
        try {
            if (activeTab === "overview") {
                const res = await fetch("http://localhost:8000/api/enterprise/config");
                if (res.ok) {
                    const data = await res.json();
                    if (data) setConfig(data);
                }
            } else if (activeTab === "integrations") {
                const res = await fetch("http://localhost:8000/api/enterprise/integrations");
                if (res.ok) setIntegrations(await res.json());
            } else if (activeTab === "support") {
                const res = await fetch("http://localhost:8000/api/enterprise/tickets");
                if (res.ok) setTickets(await res.json());
            } else if (activeTab === "sla") {
                const res = await fetch("http://localhost:8000/api/enterprise/sla");
                if (res.ok) setSlaMetrics(await res.json());
            }
        } catch (e) {
            console.error("Failed to fetch enterprise data:", e);
        } finally {
            setLoading(false);
        }
    };

    const createTicket = async () => {
        if (!newTicketSubject) return;
        try {
            await fetch("http://localhost:8000/api/enterprise/tickets", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ subject: newTicketSubject, priority: "medium" })
            });
            setNewTicketSubject("");
            fetchData();
        } catch (e) {
            console.error("Failed to create ticket:", e);
        }
    };

    const deleteIntegration = async (id: string) => {
        try {
            await fetch(`http://localhost:8000/api/enterprise/integrations/${id}`, {
                method: "DELETE"
            });
            fetchData();
        } catch (e) {
            console.error("Failed to delete integration:", e);
        }
    };

    const formatDate = (dateStr: string) => {
        return new Date(dateStr).toLocaleDateString("en-US", {
            month: "short",
            day: "numeric",
            year: "numeric"
        });
    };

    const tabs = [
        { id: "overview", icon: Building, label: "Overview" },
        { id: "integrations", icon: Plug, label: "Integrations" },
        { id: "support", icon: Headphones, label: "Support" },
        { id: "sla", icon: BarChart3, label: "SLA Metrics" }
    ];

    return (
        <div className="min-h-screen bg-[#0a0a0a] text-white">
            {/* Header */}
            <header className="border-b border-white/10 bg-black/50 backdrop-blur-sm sticky top-0 z-50">
                <div className="max-w-6xl mx-auto px-6 py-4">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center">
                            <Building size={20} />
                        </div>
                        <div>
                            <h1 className="text-xl font-semibold">Enterprise</h1>
                            <p className="text-xs text-gray-500">Self-hosted, SLA, and dedicated support</p>
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
                                    ? "bg-amber-500/20 text-amber-300 border border-amber-500/30"
                                    : "text-gray-400 hover:text-white hover:bg-white/5"
                            )}
                        >
                            <tab.icon size={14} />
                            {tab.label}
                        </button>
                    ))}
                </div>

                {/* Overview */}
                {activeTab === "overview" && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <GlassCard className="p-6">
                            <h3 className="text-sm font-medium mb-4 flex items-center gap-2">
                                <Shield size={14} className="text-blue-400" />
                                Deployment
                            </h3>
                            <div className="space-y-3">
                                <div className="flex justify-between">
                                    <span className="text-gray-400">Type</span>
                                    <span className="capitalize">{config?.deployment_type || "Cloud"}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-gray-400">SLA Tier</span>
                                    <span className="capitalize">{config?.sla_tier || "Standard"}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-gray-400">Uptime SLA</span>
                                    <span>{config?.uptime_sla || 99.9}%</span>
                                </div>
                            </div>
                        </GlassCard>

                        <GlassCard className="p-6">
                            <h3 className="text-sm font-medium mb-4 flex items-center gap-2">
                                <Headphones size={14} className="text-purple-400" />
                                Support
                            </h3>
                            <div className="space-y-3">
                                <div className="flex justify-between">
                                    <span className="text-gray-400">Support Tier</span>
                                    <span className="capitalize">{config?.support_tier || "Standard"}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-gray-400">Response Time</span>
                                    <span>{config?.response_time_sla || 24}h</span>
                                </div>
                                {config?.dedicated_success_manager && (
                                    <div className="flex justify-between">
                                        <span className="text-gray-400">Success Manager</span>
                                        <span>{config.dedicated_success_manager}</span>
                                    </div>
                                )}
                            </div>
                        </GlassCard>

                        <GlassCard className="p-6 md:col-span-2">
                            <h3 className="text-sm font-medium mb-4 flex items-center gap-2">
                                <Key size={14} className="text-amber-400" />
                                Self-Hosted License
                            </h3>
                            <p className="text-sm text-gray-400 mb-4">
                                Deploy API Doc on your own infrastructure with a self-hosted license.
                            </p>
                            <button className="px-4 py-2 bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 rounded-lg text-sm">
                                Request License Key
                            </button>
                        </GlassCard>
                    </div>
                )}

                {/* Integrations */}
                {activeTab === "integrations" && (
                    <GlassCard className="p-6">
                        <h3 className="text-sm font-medium mb-4 flex items-center gap-2">
                            <Plug size={14} className="text-cyan-400" />
                            Custom Integrations
                        </h3>

                        {integrations.length === 0 ? (
                            <div className="text-center py-8 text-gray-500">
                                <Plug size={32} className="mx-auto mb-2 opacity-50" />
                                <p className="text-sm">No integrations configured</p>
                                <p className="text-xs">Add webhooks to receive real-time updates</p>
                            </div>
                        ) : (
                            <div className="space-y-2">
                                {integrations.map((integration) => (
                                    <div
                                        key={integration.id}
                                        className="p-3 rounded-lg bg-white/5 flex items-center gap-3"
                                    >
                                        <Plug size={16} className="text-gray-400" />
                                        <div className="flex-1">
                                            <p className="font-medium">{integration.name}</p>
                                            <p className="text-xs text-gray-500">{integration.integration_type}</p>
                                        </div>
                                        <span className={cn(
                                            "text-xs px-2 py-0.5 rounded",
                                            integration.is_enabled
                                                ? "bg-emerald-500/10 text-emerald-400"
                                                : "bg-gray-500/10 text-gray-400"
                                        )}>
                                            {integration.is_enabled ? "Active" : "Disabled"}
                                        </span>
                                        <button
                                            onClick={() => deleteIntegration(integration.id)}
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

                {/* Support Tickets */}
                {activeTab === "support" && (
                    <GlassCard className="p-6">
                        <h3 className="text-sm font-medium mb-4 flex items-center gap-2">
                            <Headphones size={14} className="text-purple-400" />
                            Support Tickets
                        </h3>

                        <div className="flex gap-2 mb-4">
                            <input
                                type="text"
                                value={newTicketSubject}
                                onChange={(e) => setNewTicketSubject(e.target.value)}
                                placeholder="Describe your issue..."
                                className="flex-1 px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-sm focus:outline-none"
                            />
                            <button
                                onClick={createTicket}
                                disabled={!newTicketSubject}
                                className="px-4 py-2 bg-purple-500/20 hover:bg-purple-500/30 text-purple-300 rounded-lg text-sm disabled:opacity-50 flex items-center gap-2"
                            >
                                <Send size={14} />
                                Submit
                            </button>
                        </div>

                        {tickets.length === 0 ? (
                            <p className="text-sm text-gray-500 text-center py-4">No tickets yet</p>
                        ) : (
                            <div className="space-y-2">
                                {tickets.map((ticket) => (
                                    <div
                                        key={ticket.id}
                                        className="p-3 rounded-lg bg-white/5 flex items-center gap-3"
                                    >
                                        <div className="flex-1">
                                            <div className="flex items-center gap-2">
                                                <code className="text-xs text-gray-500">{ticket.ticket_number}</code>
                                                <span className="font-medium">{ticket.subject}</span>
                                            </div>
                                            <p className="text-xs text-gray-500">{formatDate(ticket.created_at)}</p>
                                        </div>
                                        <span className={cn(
                                            "text-xs px-2 py-0.5 rounded capitalize",
                                            PRIORITY_COLORS[ticket.priority]
                                        )}>
                                            {ticket.priority}
                                        </span>
                                        <span className={cn(
                                            "text-xs px-2 py-0.5 rounded capitalize",
                                            STATUS_COLORS[ticket.status]
                                        )}>
                                            {ticket.status.replace("_", " ")}
                                        </span>
                                    </div>
                                ))}
                            </div>
                        )}
                    </GlassCard>
                )}

                {/* SLA Metrics */}
                {activeTab === "sla" && (
                    <GlassCard className="p-6">
                        <h3 className="text-sm font-medium mb-4 flex items-center gap-2">
                            <BarChart3 size={14} className="text-emerald-400" />
                            SLA Performance
                        </h3>

                        {slaMetrics.length === 0 ? (
                            <p className="text-sm text-gray-500 text-center py-8">No SLA data available yet</p>
                        ) : (
                            <div className="space-y-3">
                                {slaMetrics.map((metric, idx) => (
                                    <div
                                        key={idx}
                                        className="p-4 rounded-lg bg-white/5"
                                    >
                                        <div className="flex items-center justify-between mb-2">
                                            <span className="font-medium">{formatDate(metric.period_start)}</span>
                                            <span className={cn(
                                                "text-xs px-2 py-0.5 rounded",
                                                metric.sla_met
                                                    ? "bg-emerald-500/10 text-emerald-400"
                                                    : "bg-red-500/10 text-red-400"
                                            )}>
                                                {metric.sla_met ? "SLA Met" : "SLA Breached"}
                                            </span>
                                        </div>
                                        <div className="grid grid-cols-2 gap-4 text-sm">
                                            <div>
                                                <span className="text-gray-500">Uptime</span>
                                                <p className="font-mono">{metric.uptime_percentage?.toFixed(2)}%</p>
                                            </div>
                                            <div>
                                                <span className="text-gray-500">Avg Response</span>
                                                <p className="font-mono">{metric.avg_response_time_ms?.toFixed(0)}ms</p>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </GlassCard>
                )}
            </div>
        </div>
    );
}
