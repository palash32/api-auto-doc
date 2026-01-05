"use client";

import React, { useState, useRef, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { useGSAP } from "@gsap/react";
import gsap from "gsap";
import {
    Search,
    Filter,
    Edit,
    FileText,
    Lock,
    Plus
} from "lucide-react";
import { cn } from "@/lib/utils";
import { GlassCard } from "@/components/ui/glass-card";
import { MagneticButton } from "@/components/ui/magnetic-button";
import { api, Repository, EndpointSummary, PaginatedEndpoints } from "@/lib/api";
import { EndpointDetailModal } from "@/components/endpoint-detail-modal";

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

function ApiViewerPageContent() {
    const containerRef = useRef<HTMLDivElement>(null);
    const searchParams = useSearchParams();
    const [repositories, setRepositories] = useState<Repository[]>([]);
    const [selectedRepo, setSelectedRepo] = useState<string>("");
    const [searchQuery, setSearchQuery] = useState("");
    const [selectedMethod, setSelectedMethod] = useState<string>("");
    const [endpoints, setEndpoints] = useState<EndpointSummary[]>([]);
    const [total, setTotal] = useState(0);
    const [loading, setLoading] = useState(false);
    const [page, setPage] = useState(1);
    const [selectedEndpointId, setSelectedEndpointId] = useState<string | null>(null);

    // Fetch repositories on mount
    useEffect(() => {
        fetchRepositories();
    }, []);

    // Fetch endpoints when repo or filters change
    useEffect(() => {
        if (selectedRepo) {
            fetchEndpoints();
        }
    }, [selectedRepo, searchQuery, selectedMethod, page]);

    const fetchRepositories = async () => {
        const repos = await api.getRepositories();
        setRepositories(repos);

        // Check URL for repo param first, otherwise use first repo
        const repoIdFromUrl = searchParams.get('repo');
        if (repoIdFromUrl && repos.some(r => r.id === repoIdFromUrl)) {
            setSelectedRepo(repoIdFromUrl);
        } else if (repos.length > 0) {
            setSelectedRepo(repos[0].id);
        }
    };

    const fetchEndpoints = async () => {
        if (!selectedRepo) return;

        setLoading(true);
        const result = await api.getRepositoryEndpoints(selectedRepo, {
            page,
            per_page: 50,
            method: selectedMethod || undefined,
            search: searchQuery || undefined
        });

        setEndpoints(result.endpoints);
        setTotal(result.total);
        setLoading(false);
    };

    // GSAP animations
    useGSAP(() => {
        if (containerRef.current) {
            gsap.fromTo(".api-card",
                {
                    opacity: 0,
                    y: 20
                },
                {
                    opacity: 1,
                    y: 0,
                    duration: 0.6,
                    stagger: 0.1,
                    ease: "power2.out"
                }
            );
        }
    }, [endpoints]);

    return (
        <div ref={containerRef} className="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950 pt-24 px-6 pb-20">
            <div className="max-w-7xl mx-auto space-y-8">
                {/* Header */}
                <div className="text-center space-y-4">
                    <h1 className="text-5xl font-bold bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
                        API Documentation
                    </h1>
                    <p className="text-gray-400 text-lg">
                        Auto-generated documentation for your repositories
                    </p>
                </div>

                {/* Controls */}
                <GlassCard className="p-6">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        {/* Repository Selector */}
                        <div>
                            <label className="block text-sm font-medium text-gray-300 mb-2">
                                Repository
                            </label>
                            <select
                                value={selectedRepo}
                                onChange={(e) => setSelectedRepo(e.target.value)}
                                className="w-full px-4 py-2 bg-gray-800/50 border border-gray-700 rounded-lg text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            >
                                {repositories.map((repo) => (
                                    <option key={repo.id} value={repo.id}>
                                        {repo.full_name} ({repo.api_count} APIs)
                                    </option>
                                ))}
                            </select>
                        </div>

                        {/* Method Filter */}
                        <div>
                            <label className="block text-sm font-medium text-gray-300 mb-2">
                                Method
                            </label>
                            <select
                                value={selectedMethod}
                                onChange={(e) => setSelectedMethod(e.target.value)}
                                className="w-full px-4 py-2 bg-gray-800/50 border border-gray-700 rounded-lg text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            >
                                <option value="">All Methods</option>
                                <option value="GET">GET</option>
                                <option value="POST">POST</option>
                                <option value="PUT">PUT</option>
                                <option value="DELETE">DELETE</option>
                                <option value="PATCH">PATCH</option>
                            </select>
                        </div>

                        {/* Search */}
                        <div>
                            <label className="block text-sm font-medium text-gray-300 mb-2">
                                Search
                            </label>
                            <div className="relative">
                                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                                <input
                                    type="text"
                                    placeholder="Search endpoints..."
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                    className="w-full pl-10 pr-4 py-2 bg-gray-800/50 border border-gray-700 rounded-lg text-white placeholder:text-gray-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                />
                            </div>
                        </div>
                    </div>

                    {/* Results count */}
                    <div className="mt-4 text-sm text-gray-400">
                        Showing {endpoints.length} of {total} endpoints
                    </div>
                </GlassCard>

                {/* Endpoints Table */}
                {loading ? (
                    <div className="text-center py-12">
                        <div className="inline-block w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
                        <p className="mt-4 text-gray-400">Loading endpoints...</p>
                    </div>
                ) : endpoints.length === 0 ? (
                    <GlassCard className="p-12 text-center">
                        <FileText className="w-16 h-16 mx-auto text-gray-600 mb-4" />
                        <h3 className="text-xl font-semibold text-gray-300 mb-2">
                            No endpoints found
                        </h3>
                        <p className="text-gray-500">
                            Try scanning a repository to discover API endpoints
                        </p>
                    </GlassCard>
                ) : (
                    <div className="space-y-3">
                        {endpoints.map((endpoint) => (
                            <GlassCard key={endpoint.id} className="api-card p-6 hover:scale-[1.01] transition-all cursor-pointer group">
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-4 flex-1">
                                        <MethodBadge method={endpoint.method} />
                                        <code className="text-lg font-mono text-blue-400 group-hover:text-blue-300">
                                            {endpoint.path}
                                        </code>
                                    </div>

                                    <div className="flex items-center gap-4">
                                        {endpoint.auth_required && (
                                            <div className="flex items-center gap-2 text-yellow-400">
                                                <Lock className="w-4 h-4" />
                                                <span className="text-xs">Auth</span>
                                            </div>
                                        )}
                                        <button
                                            onClick={() => setSelectedEndpointId(endpoint.id)}
                                            className="p-2 hover:bg-white/10 rounded-lg transition-colors"
                                        >
                                            <Edit className="w-5 h-5 text-gray-400 group-hover:text-blue-400" />
                                        </button>
                                    </div>
                                </div>

                                {endpoint.summary && (
                                    <p className="mt-3 text-gray-400 text-sm">
                                        {endpoint.summary}
                                    </p>
                                )}

                                {endpoint.tags && endpoint.tags.length > 0 && (
                                    <div className="mt-3 flex gap-2">
                                        {endpoint.tags.map((tag) => (
                                            <span
                                                key={tag}
                                                className="px-2 py-1 bg-purple-500/10 text-purple-400 text-xs rounded-md"
                                            >
                                                {tag}
                                            </span>
                                        ))}
                                    </div>
                                )}
                            </GlassCard>
                        ))}
                    </div>
                )}

                {/* Pagination */}
                {total > 50 && (
                    <div className="flex justify-center gap-2">
                        <button
                            disabled={page === 1}
                            onClick={() => setPage(p => p - 1)}
                            className="px-4 py-2 bg-gray-800 text-white rounded-lg disabled:opacity-50 hover:bg-gray-700 transition-colors"
                        >
                            Previous
                        </button>
                        <span className="px-4 py-2 text-gray-400">
                            Page {page}
                        </span>
                        <button
                            disabled={page * 50 >= total}
                            onClick={() => setPage(p => p + 1)}
                            className="px-4 py-2 bg-gray-800 text-white rounded-lg disabled:opacity-50 hover:bg-gray-700 transition-colors"
                        >
                            Next
                        </button>
                    </div>
                )}
            </div>

            {/* Endpoint Detail Modal */}
            {selectedEndpointId && (
                <EndpointDetailModal
                    endpointId={selectedEndpointId}
                    onClose={() => setSelectedEndpointId(null)}
                    onSave={() => fetchEndpoints()}
                />
            )}
        </div>
    );
}

// Wrap with Suspense to fix Next.js 14 useSearchParams prerender issue
export default function ApiViewerPage() {
    return (
        <Suspense fallback={
            <div className="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950 pt-24 px-6 flex items-center justify-center">
                <div className="inline-block w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
            </div>
        }>
            <ApiViewerPageContent />
        </Suspense>
    );
}
