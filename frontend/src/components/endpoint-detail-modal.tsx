"use client";

import React, { useState, useEffect } from "react";
import { X, Save, Lock, FileText, Tag, Code, Play } from "lucide-react";
import { useRouter } from "next/navigation";
import { api, EndpointDetail } from "@/lib/api";
import { cn } from "@/lib/utils";
import { useToast } from "@/components/toast-provider";
import { CodeBlock, generateCodeExamples } from "@/components/ui/code-block";

interface EndpointDetailModalProps {
    endpointId: string;
    onClose: () => void;
    onSave?: () => void;
}

const MethodBadge = ({ method }: { method: string }) => {
    const colors = {
        GET: "bg-blue-500/10 text-blue-400 border-blue-500/20",
        POST: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
        PUT: "bg-orange-500/10 text-orange-400 border-orange-500/20",
        DELETE: "bg-red-500/10 text-red-400 border-red-500/20",
        PATCH: "bg-yellow-500/10 text-yellow-400 border-yellow-500/20",
    };

    return (
        <span className={cn(
            "px-2.5 py-1 rounded-md text-xs font-bold border font-mono",
            colors[method as keyof typeof colors] || "bg-gray-500/10 text-gray-400"
        )}>
            {method}
        </span>
    );
};

export function EndpointDetailModal({ endpointId, onClose, onSave }: EndpointDetailModalProps) {
    const [endpoint, setEndpoint] = useState<EndpointDetail | null>(null);
    const [loading, setLoading] = useState(true);
    const [editing, setEditing] = useState(false);
    const [saving, setSaving] = useState(false);
    const toast = useToast();
    const router = useRouter();

    // Editable fields
    const [summary, setSummary] = useState("");
    const [description, setDescription] = useState("");
    const [tags, setTags] = useState<string[]>([]);
    const [newTag, setNewTag] = useState("");

    useEffect(() => {
        fetchEndpoint();
    }, [endpointId]);

    const fetchEndpoint = async () => {
        setLoading(true);
        const data = await api.getEndpointDetail(endpointId);
        if (data) {
            setEndpoint(data);
            setSummary(data.summary);
            setDescription(data.description);
            setTags(data.tags);
        }
        setLoading(false);
    };

    const handleSave = async () => {
        if (!endpoint) return;

        setSaving(true);
        try {
            const updated = await api.updateEndpoint(endpointId, {
                summary,
                description,
                tags
            });

            if (updated) {
                setEndpoint(updated);
                setEditing(false);
                toast.success("Documentation updated successfully!");
                onSave?.();
            } else {
                toast.error("Failed to save changes. Please try again.");
            }
        } catch (error) {
            toast.error("An error occurred while saving.");
        }
        setSaving(false);
    };

    const addTag = () => {
        if (newTag && !tags.includes(newTag)) {
            setTags([...tags, newTag]);
            setNewTag("");
        }
    };

    const removeTag = (tagToRemove: string) => {
        setTags(tags.filter(t => t !== tagToRemove));
    };

    if (loading) {
        return (
            <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
                <div className="bg-gray-900 rounded-xl p-8">
                    <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto" />
                    <p className="mt-4 text-gray-400">Loading...</p>
                </div>
            </div>
        );
    }

    if (!endpoint) {
        return null;
    }

    return (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <div className="bg-gradient-to-br from-gray-900 to-gray-950 border border-gray-800 rounded-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
                {/* Header */}
                <div className="p-6 border-b border-gray-800 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <MethodBadge method={endpoint.method} />
                        <code className="text-xl font-mono text-blue-400">{endpoint.path}</code>
                    </div>
                    <div className="flex items-center gap-2">
                        <button
                            onClick={() => {
                                // Navigate to playground with endpoint pre-filled
                                const params = new URLSearchParams({
                                    method: endpoint.method,
                                    path: endpoint.path
                                });
                                router.push(`/playground?${params.toString()}`);
                            }}
                            className="px-4 py-2 bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 rounded-lg text-sm font-medium flex items-center gap-2 transition-all btn-press"
                        >
                            <Play size={14} />
                            Try API
                        </button>
                        <button
                            onClick={onClose}
                            className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
                        >
                            <X className="w-5 h-5 text-gray-400" />
                        </button>
                    </div>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto p-6 space-y-6">
                    {/* Summary */}
                    <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">
                            Summary
                        </label>
                        {editing ? (
                            <input
                                type="text"
                                value={summary}
                                onChange={(e) => setSummary(e.target.value)}
                                className="w-full px-4 py-2 bg-gray-800/50 border border-gray-700 rounded-lg text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                placeholder="Brief one-line description"
                            />
                        ) : (
                            <p className="text-gray-300">{endpoint.summary || "No summary"}</p>
                        )}
                    </div>

                    {/* Description */}
                    <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">
                            Description
                        </label>
                        {editing ? (
                            <textarea
                                value={description}
                                onChange={(e) => setDescription(e.target.value)}
                                rows={6}
                                className="w-full px-4 py-2 bg-gray-800/50 border border-gray-700 rounded-lg text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                placeholder="Detailed description of the endpoint"
                            />
                        ) : (
                            <p className="text-gray-400 whitespace-pre-wrap">{endpoint.description || "No description"}</p>
                        )}
                    </div>

                    {/* Tags */}
                    <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">
                            <Tag className="w-4 h-4 inline mr-1" />
                            Tags
                        </label>
                        <div className="flex flex-wrap gap-2 mb-2">
                            {tags.map((tag) => (
                                <span
                                    key={tag}
                                    className="px-3 py-1 bg-purple-500/10 text-purple-400 text-sm rounded-md flex items-center gap-2"
                                >
                                    {tag}
                                    {editing && (
                                        <button
                                            onClick={() => removeTag(tag)}
                                            className="hover:text-purple-300"
                                        >
                                            <X className="w-3 h-3" />
                                        </button>
                                    )}
                                </span>
                            ))}
                        </div>
                        {editing && (
                            <div className="flex gap-2">
                                <input
                                    type="text"
                                    value={newTag}
                                    onChange={(e) => setNewTag(e.target.value)}
                                    onKeyPress={(e) => e.key === 'Enter' && addTag()}
                                    placeholder="Add tag..."
                                    className="flex-1 px-3 py-2 bg-gray-800/50 border border-gray-700 rounded-lg text-white text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                />
                                <button
                                    onClick={addTag}
                                    className="px-4 py-2 bg-purple-500/20 text-purple-400 rounded-lg hover:bg-purple-500/30 transition-colors"
                                >
                                    Add
                                </button>
                            </div>
                        )}
                    </div>

                    {/* Auth Info */}
                    {endpoint.auth_required && (
                        <div className="flex items-center gap-2 text-yellow-400 bg-yellow-500/10 p-3 rounded-lg border border-yellow-500/20">
                            <Lock className="w-5 h-5" />
                            <span>Requires Authentication{endpoint.auth_type ? ` (${endpoint.auth_type})` : ''}</span>
                        </div>
                    )}

                    {/* Code Examples */}
                    <div>
                        <label className="block text-sm font-medium text-gray-300 mb-3">
                            <Code className="w-4 h-4 inline mr-1" />
                            Code Examples
                        </label>
                        <CodeBlock
                            title="Example Request"
                            examples={generateCodeExamples(
                                endpoint.method,
                                endpoint.path,
                                "https://api.example.com"
                            )}
                            defaultExpanded={true}
                        />
                    </div>

                    {/* File Location */}
                    <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">
                            <FileText className="w-4 h-4 inline mr-1" />
                            Source File
                        </label>
                        <code className="text-sm text-gray-400 bg-gray-800/50 px-3 py-2 rounded-lg block">
                            {endpoint.file_path || "Unknown"}
                        </code>
                    </div>

                    {/* Parameters (read-only) */}
                    {endpoint.parameters && endpoint.parameters.length > 0 && (
                        <div>
                            <label className="block text-sm font-medium text-gray-300 mb-2">
                                Parameters
                            </label>
                            <div className="bg-gray-800/50 rounded-lg p-4 font-mono text-sm">
                                <pre className="text-gray-400 overflow-x-auto">
                                    {JSON.stringify(endpoint.parameters, null, 2)}
                                </pre>
                            </div>
                        </div>
                    )}

                    {/* Responses (read-only) */}
                    {endpoint.responses && endpoint.responses.length > 0 && (
                        <div>
                            <label className="block text-sm font-medium text-gray-300 mb-2">
                                Responses
                            </label>
                            <div className="bg-gray-800/50 rounded-lg p-4 font-mono text-sm">
                                <pre className="text-gray-400 overflow-x-auto">
                                    {JSON.stringify(endpoint.responses, null, 2)}
                                </pre>
                            </div>
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="p-6 border-t border-gray-800 flex justify-between">
                    <button
                        onClick={onClose}
                        className="px-6 py-2 text-gray-400 hover:text-white transition-colors"
                    >
                        Close
                    </button>
                    <div className="flex gap-3">
                        {editing ? (
                            <>
                                <button
                                    onClick={() => {
                                        setEditing(false);
                                        setSummary(endpoint.summary);
                                        setDescription(endpoint.description);
                                        setTags(endpoint.tags);
                                    }}
                                    className="px-6 py-2 text-gray-400 hover:text-white transition-colors"
                                >
                                    Cancel
                                </button>
                                <button
                                    onClick={handleSave}
                                    disabled={saving}
                                    className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                                >
                                    {saving ? (
                                        <>
                                            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                                            Saving...
                                        </>
                                    ) : (
                                        <>
                                            <Save className="w-4 h-4" />
                                            Save Changes
                                        </>
                                    )}
                                </button>
                            </>
                        ) : (
                            <button
                                onClick={() => setEditing(true)}
                                className="px-6 py-2 bg-purple-500/20 text-purple-400 rounded-lg hover:bg-purple-500/30 transition-colors"
                            >
                                Edit Documentation
                            </button>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
