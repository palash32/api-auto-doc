"use client";

import React, { useState, useEffect } from "react";
import {
    Palette,
    Globe,
    Code,
    Image,
    Type,
    Save,
    RotateCcw,
    Plus,
    Trash2,
    Check,
    X,
    ExternalLink,
    Shield,
    Sparkles
} from "lucide-react";
import { cn } from "@/lib/utils";
import { API_BASE_URL } from "@/lib/api";
import { GlassCard } from "@/components/ui/glass-card";

interface BrandingSettings {
    id: string;
    logo_url: string | null;
    logo_dark_url: string | null;
    favicon_url: string | null;
    brand_name: string | null;
    tagline: string | null;
    primary_color: string;
    secondary_color: string | null;
    accent_color: string | null;
    background_color: string | null;
    text_color: string | null;
    theme_mode: string;
    font_family: string | null;
    border_radius: string;
    custom_css: string | null;
    footer_text: string | null;
    hide_powered_by: boolean;
    is_white_label: boolean;
}

interface CustomDomain {
    id: string;
    domain: string;
    ssl_status: string;
    is_verified: boolean;
    is_active: boolean;
    is_primary: boolean;
    verification_token: string | null;
}

const COLOR_PRESETS = [
    { name: "Blue", primary: "#3B82F6", accent: "#10B981" },
    { name: "Purple", primary: "#8B5CF6", accent: "#EC4899" },
    { name: "Green", primary: "#10B981", accent: "#3B82F6" },
    { name: "Orange", primary: "#F59E0B", accent: "#EF4444" },
    { name: "Red", primary: "#EF4444", accent: "#F59E0B" },
    { name: "Cyan", primary: "#06B6D4", accent: "#8B5CF6" },
];

const FONT_OPTIONS = [
    "Inter",
    "Roboto",
    "Open Sans",
    "Poppins",
    "Montserrat",
    "Space Grotesk",
    "JetBrains Mono"
];

export default function BrandingSettingsPage() {
    const [activeTab, setActiveTab] = useState<"appearance" | "domains" | "advanced">("appearance");
    const [branding, setBranding] = useState<BrandingSettings | null>(null);
    const [domains, setDomains] = useState<CustomDomain[]>([]);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [newDomain, setNewDomain] = useState("");

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        setLoading(true);
        try {
            const [brandingRes, domainsRes] = await Promise.all([
                fetch(`${API_BASE_URL}/api/branding/branding`),
                fetch(`${API_BASE_URL}/api/branding/domains`)
            ]);

            if (brandingRes.ok) {
                setBranding(await brandingRes.json());
            }
            if (domainsRes.ok) {
                setDomains(await domainsRes.json());
            }
        } catch (e) {
            console.error("Failed to fetch branding:", e);
        } finally {
            setLoading(false);
        }
    };

    const saveBranding = async () => {
        if (!branding) return;
        setSaving(true);

        try {
            await fetch(`${API_BASE_URL}/api/branding/branding`, {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(branding)
            });
        } catch (e) {
            console.error("Failed to save:", e);
        } finally {
            setSaving(false);
        }
    };

    const resetBranding = async () => {
        if (!confirm("Reset all branding to defaults?")) return;

        try {
            await fetch(`${API_BASE_URL}/api/branding/branding/reset`, {
                method: "POST"
            });
            fetchData();
        } catch (e) {
            console.error("Failed to reset:", e);
        }
    };

    const addDomain = async () => {
        if (!newDomain) return;

        try {
            const res = await fetch(`${API_BASE_URL}/api/branding/domains`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ domain: newDomain })
            });

            if (res.ok) {
                setNewDomain("");
                fetchData();
            }
        } catch (e) {
            console.error("Failed to add domain:", e);
        }
    };

    const verifyDomain = async (domainId: string) => {
        try {
            await fetch(`${API_BASE_URL}/api/branding/domains/${domainId}/verify`, {
                method: "POST"
            });
            fetchData();
        } catch (e) {
            console.error("Failed to verify:", e);
        }
    };

    const deleteDomain = async (domainId: string) => {
        if (!confirm("Remove this domain?")) return;

        try {
            await fetch(`${API_BASE_URL}/api/branding/domains/${domainId}`, {
                method: "DELETE"
            });
            fetchData();
        } catch (e) {
            console.error("Failed to delete:", e);
        }
    };

    const updateBranding = (field: keyof BrandingSettings, value: any) => {
        if (branding) {
            setBranding({ ...branding, [field]: value });
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-[#0a0a0a] flex items-center justify-center">
                <div className="w-8 h-8 border-4 border-purple-500 border-t-transparent rounded-full animate-spin" />
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-[#0a0a0a] text-white">
            {/* Header */}
            <header className="border-b border-white/10 bg-black/50 backdrop-blur-sm sticky top-0 z-50">
                <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-pink-500 to-purple-600 flex items-center justify-center">
                            <Palette size={20} />
                        </div>
                        <div>
                            <h1 className="text-xl font-semibold">Custom Branding</h1>
                            <p className="text-xs text-gray-500">Customize your documentation portal</p>
                        </div>
                    </div>

                    <div className="flex items-center gap-3">
                        <button
                            onClick={resetBranding}
                            className="px-4 py-2 text-sm text-gray-400 hover:text-white flex items-center gap-2"
                        >
                            <RotateCcw size={14} />
                            Reset
                        </button>
                        <button
                            onClick={saveBranding}
                            disabled={saving}
                            className="px-4 py-2 bg-gradient-to-r from-purple-500 to-pink-600 rounded-lg text-sm font-medium flex items-center gap-2 disabled:opacity-50"
                        >
                            {saving ? (
                                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                            ) : (
                                <Save size={14} />
                            )}
                            Save Changes
                        </button>
                    </div>
                </div>
            </header>

            <div className="max-w-6xl mx-auto p-6">
                {/* Tabs */}
                <div className="flex gap-2 mb-6">
                    {[
                        { id: "appearance", icon: Palette, label: "Appearance" },
                        { id: "domains", icon: Globe, label: "Custom Domains" },
                        { id: "advanced", icon: Code, label: "Advanced" }
                    ].map((tab) => (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id as any)}
                            className={cn(
                                "px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 transition-colors",
                                activeTab === tab.id
                                    ? "bg-white/10 text-white"
                                    : "text-gray-400 hover:text-white"
                            )}
                        >
                            <tab.icon size={16} />
                            {tab.label}
                        </button>
                    ))}
                </div>

                {/* Appearance Tab */}
                {activeTab === "appearance" && branding && (
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        {/* Brand Identity */}
                        <GlassCard className="p-6">
                            <h3 className="text-sm font-medium mb-4 flex items-center gap-2">
                                <Sparkles size={14} className="text-purple-400" />
                                Brand Identity
                            </h3>

                            <div className="space-y-4">
                                <div>
                                    <label className="block text-xs text-gray-400 mb-2">Brand Name</label>
                                    <input
                                        type="text"
                                        value={branding.brand_name || ""}
                                        onChange={(e) => updateBranding("brand_name", e.target.value)}
                                        placeholder="Your Company Name"
                                        className="w-full px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-sm placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-purple-500/50"
                                    />
                                </div>

                                <div>
                                    <label className="block text-xs text-gray-400 mb-2">Tagline</label>
                                    <input
                                        type="text"
                                        value={branding.tagline || ""}
                                        onChange={(e) => updateBranding("tagline", e.target.value)}
                                        placeholder="Developer Portal"
                                        className="w-full px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-sm placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-purple-500/50"
                                    />
                                </div>

                                <div>
                                    <label className="block text-xs text-gray-400 mb-2">Logo URL</label>
                                    <input
                                        type="text"
                                        value={branding.logo_url || ""}
                                        onChange={(e) => updateBranding("logo_url", e.target.value)}
                                        placeholder="https://..."
                                        className="w-full px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-sm placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-purple-500/50"
                                    />
                                </div>
                            </div>
                        </GlassCard>

                        {/* Colors */}
                        <GlassCard className="p-6">
                            <h3 className="text-sm font-medium mb-4 flex items-center gap-2">
                                <Palette size={14} className="text-pink-400" />
                                Color Scheme
                            </h3>

                            {/* Presets */}
                            <div className="flex flex-wrap gap-2 mb-4">
                                {COLOR_PRESETS.map((preset) => (
                                    <button
                                        key={preset.name}
                                        onClick={() => {
                                            updateBranding("primary_color", preset.primary);
                                            updateBranding("accent_color", preset.accent);
                                        }}
                                        className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 transition-colors text-xs"
                                    >
                                        <div
                                            className="w-4 h-4 rounded-full"
                                            style={{ background: preset.primary }}
                                        />
                                        {preset.name}
                                    </button>
                                ))}
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-xs text-gray-400 mb-2">Primary</label>
                                    <div className="flex items-center gap-2">
                                        <input
                                            type="color"
                                            value={branding.primary_color}
                                            onChange={(e) => updateBranding("primary_color", e.target.value)}
                                            className="w-10 h-10 rounded-lg cursor-pointer bg-transparent border-0"
                                        />
                                        <input
                                            type="text"
                                            value={branding.primary_color}
                                            onChange={(e) => updateBranding("primary_color", e.target.value)}
                                            className="flex-1 px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-xs font-mono"
                                        />
                                    </div>
                                </div>

                                <div>
                                    <label className="block text-xs text-gray-400 mb-2">Accent</label>
                                    <div className="flex items-center gap-2">
                                        <input
                                            type="color"
                                            value={branding.accent_color || "#10B981"}
                                            onChange={(e) => updateBranding("accent_color", e.target.value)}
                                            className="w-10 h-10 rounded-lg cursor-pointer bg-transparent border-0"
                                        />
                                        <input
                                            type="text"
                                            value={branding.accent_color || ""}
                                            onChange={(e) => updateBranding("accent_color", e.target.value)}
                                            className="flex-1 px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-xs font-mono"
                                        />
                                    </div>
                                </div>
                            </div>
                        </GlassCard>

                        {/* Typography */}
                        <GlassCard className="p-6">
                            <h3 className="text-sm font-medium mb-4 flex items-center gap-2">
                                <Type size={14} className="text-blue-400" />
                                Typography
                            </h3>

                            <div className="space-y-4">
                                <div>
                                    <label className="block text-xs text-gray-400 mb-2">Font Family</label>
                                    <select
                                        value={branding.font_family || "Inter"}
                                        onChange={(e) => updateBranding("font_family", e.target.value)}
                                        className="w-full px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-sm focus:outline-none"
                                    >
                                        {FONT_OPTIONS.map((font) => (
                                            <option key={font} value={font}>{font}</option>
                                        ))}
                                    </select>
                                </div>

                                <div>
                                    <label className="block text-xs text-gray-400 mb-2">Border Radius</label>
                                    <select
                                        value={branding.border_radius}
                                        onChange={(e) => updateBranding("border_radius", e.target.value)}
                                        className="w-full px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-sm focus:outline-none"
                                    >
                                        <option value="0px">None (0px)</option>
                                        <option value="4px">Small (4px)</option>
                                        <option value="8px">Medium (8px)</option>
                                        <option value="12px">Large (12px)</option>
                                        <option value="16px">XL (16px)</option>
                                    </select>
                                </div>
                            </div>
                        </GlassCard>

                        {/* White-label */}
                        <GlassCard className="p-6">
                            <h3 className="text-sm font-medium mb-4 flex items-center gap-2">
                                <Shield size={14} className="text-amber-400" />
                                White-Label Options
                            </h3>

                            <div className="space-y-3">
                                <label className="flex items-center gap-3 p-3 rounded-lg bg-white/5 cursor-pointer hover:bg-white/10 transition-colors">
                                    <input
                                        type="checkbox"
                                        checked={branding.hide_powered_by}
                                        onChange={(e) => updateBranding("hide_powered_by", e.target.checked)}
                                        className="w-4 h-4 rounded"
                                    />
                                    <div>
                                        <p className="text-sm font-medium">Hide "Powered by" badge</p>
                                        <p className="text-xs text-gray-500">Remove platform branding</p>
                                    </div>
                                </label>

                                <label className="flex items-center gap-3 p-3 rounded-lg bg-white/5 cursor-pointer hover:bg-white/10 transition-colors">
                                    <input
                                        type="checkbox"
                                        checked={branding.is_white_label}
                                        onChange={(e) => updateBranding("is_white_label", e.target.checked)}
                                        className="w-4 h-4 rounded"
                                    />
                                    <div>
                                        <p className="text-sm font-medium">Full white-label mode</p>
                                        <p className="text-xs text-gray-500">Complete brand customization</p>
                                    </div>
                                </label>
                            </div>
                        </GlassCard>
                    </div>
                )}

                {/* Domains Tab */}
                {activeTab === "domains" && (
                    <div className="space-y-6">
                        {/* Add Domain */}
                        <GlassCard className="p-6">
                            <h3 className="text-sm font-medium mb-4 flex items-center gap-2">
                                <Globe size={14} className="text-blue-400" />
                                Add Custom Domain
                            </h3>

                            <div className="flex gap-3">
                                <input
                                    type="text"
                                    value={newDomain}
                                    onChange={(e) => setNewDomain(e.target.value)}
                                    placeholder="docs.yourcompany.com"
                                    className="flex-1 px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-sm placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-blue-500/50"
                                />
                                <button
                                    onClick={addDomain}
                                    className="px-4 py-2 bg-blue-500 rounded-lg text-sm font-medium flex items-center gap-2"
                                >
                                    <Plus size={14} />
                                    Add Domain
                                </button>
                            </div>
                        </GlassCard>

                        {/* Domain List */}
                        <GlassCard className="overflow-hidden">
                            <table className="w-full">
                                <thead>
                                    <tr className="border-b border-white/10">
                                        <th className="text-left p-4 text-xs font-medium text-gray-400">DOMAIN</th>
                                        <th className="text-left p-4 text-xs font-medium text-gray-400">STATUS</th>
                                        <th className="text-left p-4 text-xs font-medium text-gray-400">SSL</th>
                                        <th className="text-right p-4 text-xs font-medium text-gray-400">ACTIONS</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {domains.map((domain) => (
                                        <tr key={domain.id} className="border-b border-white/5">
                                            <td className="p-4">
                                                <div className="flex items-center gap-2">
                                                    <Globe size={14} className="text-gray-500" />
                                                    <span className="font-mono text-sm">{domain.domain}</span>
                                                    {domain.is_primary && (
                                                        <span className="text-[10px] px-2 py-0.5 bg-blue-500/10 text-blue-400 rounded">Primary</span>
                                                    )}
                                                </div>
                                            </td>
                                            <td className="p-4">
                                                {domain.is_verified ? (
                                                    <span className="text-xs text-emerald-400 flex items-center gap-1">
                                                        <Check size={12} />
                                                        Verified
                                                    </span>
                                                ) : (
                                                    <span className="text-xs text-amber-400">Pending verification</span>
                                                )}
                                            </td>
                                            <td className="p-4">
                                                <span className={cn(
                                                    "text-xs px-2 py-0.5 rounded",
                                                    domain.ssl_status === "active"
                                                        ? "bg-emerald-500/10 text-emerald-400"
                                                        : "bg-gray-500/10 text-gray-400"
                                                )}>
                                                    {domain.ssl_status}
                                                </span>
                                            </td>
                                            <td className="p-4 text-right">
                                                <div className="flex items-center justify-end gap-2">
                                                    {!domain.is_verified && (
                                                        <button
                                                            onClick={() => verifyDomain(domain.id)}
                                                            className="px-3 py-1 text-xs bg-blue-500/10 text-blue-400 rounded hover:bg-blue-500/20"
                                                        >
                                                            Verify
                                                        </button>
                                                    )}
                                                    <button
                                                        onClick={() => deleteDomain(domain.id)}
                                                        className="p-1.5 text-gray-500 hover:text-red-400"
                                                    >
                                                        <Trash2 size={14} />
                                                    </button>
                                                </div>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>

                            {domains.length === 0 && (
                                <div className="p-8 text-center text-gray-500">
                                    No custom domains configured
                                </div>
                            )}
                        </GlassCard>
                    </div>
                )}

                {/* Advanced Tab */}
                {activeTab === "advanced" && branding && (
                    <GlassCard className="p-6">
                        <h3 className="text-sm font-medium mb-4 flex items-center gap-2">
                            <Code size={14} className="text-green-400" />
                            Custom CSS
                        </h3>

                        <p className="text-xs text-gray-400 mb-4">
                            Add custom CSS to further customize the appearance. This is applied after the default styles.
                        </p>

                        <textarea
                            value={branding.custom_css || ""}
                            onChange={(e) => updateBranding("custom_css", e.target.value)}
                            placeholder={`/* Custom styles */
.header {
  background: linear-gradient(...)
}`}
                            className="w-full h-64 px-4 py-3 rounded-lg bg-black/50 border border-white/10 text-sm font-mono placeholder-gray-600 focus:outline-none focus:ring-1 focus:ring-green-500/50 resize-none"
                        />
                    </GlassCard>
                )}
            </div>
        </div>
    );
}
