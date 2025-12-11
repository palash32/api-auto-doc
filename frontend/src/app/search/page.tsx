"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
    Search,
    Filter,
    X,
    Clock,
    Star,
    TrendingUp,
    BookmarkPlus,
    ChevronDown,
    Loader2
} from "lucide-react";
import { cn } from "@/lib/utils";
import { GlassCard } from "@/components/ui/glass-card";
import { useDebounce } from "@/hooks/useDebounce";

interface SearchResult {
    endpoint_id: string;
    path: string;
    method: string;
    description: string | null;
    repository_id: string;
    repository_name: string;
    tags: string[] | null;
    is_deprecated: boolean;
    score: number;
    highlights: { path?: string; description?: string };
}

interface SearchResponse {
    query: string;
    total: number;
    page: number;
    page_size: number;
    results: SearchResult[];
    suggestions: string[];
    filters_applied: object;
}

const METHOD_COLORS: Record<string, string> = {
    GET: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30",
    POST: "bg-blue-500/10 text-blue-400 border-blue-500/30",
    PUT: "bg-amber-500/10 text-amber-400 border-amber-500/30",
    PATCH: "bg-purple-500/10 text-purple-400 border-purple-500/30",
    DELETE: "bg-red-500/10 text-red-400 border-red-500/30"
};

const METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE"];

export default function SearchPage() {
    const [query, setQuery] = useState("");
    const [results, setResults] = useState<SearchResult[]>([]);
    const [total, setTotal] = useState(0);
    const [loading, setLoading] = useState(false);
    const [suggestions, setSuggestions] = useState<string[]>([]);
    const [recentSearches, setRecentSearches] = useState<string[]>([]);
    const [popularTags, setPopularTags] = useState<string[]>([]);
    const [showFilters, setShowFilters] = useState(false);
    const [showSuggestions, setShowSuggestions] = useState(false);

    // Filters
    const [selectedMethods, setSelectedMethods] = useState<string[]>([]);
    const [selectedTags, setSelectedTags] = useState<string[]>([]);

    const debouncedQuery = useDebounce(query, 300);

    useEffect(() => {
        fetchSuggestions();
    }, []);

    useEffect(() => {
        if (debouncedQuery.length >= 2) {
            performSearch();
        } else if (debouncedQuery.length === 0) {
            setResults([]);
            setTotal(0);
        }
    }, [debouncedQuery, selectedMethods, selectedTags]);

    const fetchSuggestions = async () => {
        try {
            const res = await fetch(`http://localhost:8000/api/search/suggestions?q=${query}`);
            if (res.ok) {
                const data = await res.json();
                setSuggestions(data.suggestions);
                setRecentSearches(data.recent_searches);
                setPopularTags(data.popular_tags);
            }
        } catch (e) {
            console.error("Failed to fetch suggestions:", e);
        }
    };

    const performSearch = async () => {
        setLoading(true);
        try {
            const res = await fetch("http://localhost:8000/api/search", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    query: debouncedQuery,
                    methods: selectedMethods.length > 0 ? selectedMethods : null,
                    tags: selectedTags.length > 0 ? selectedTags : null,
                    page: 1,
                    page_size: 50
                })
            });

            if (res.ok) {
                const data: SearchResponse = await res.json();
                setResults(data.results);
                setTotal(data.total);
                setSuggestions(data.suggestions);
            }
        } catch (e) {
            console.error("Search failed:", e);
        } finally {
            setLoading(false);
        }
    };

    const toggleMethod = (method: string) => {
        setSelectedMethods(prev =>
            prev.includes(method)
                ? prev.filter(m => m !== method)
                : [...prev, method]
        );
    };

    const toggleTag = (tag: string) => {
        setSelectedTags(prev =>
            prev.includes(tag)
                ? prev.filter(t => t !== tag)
                : [...prev, tag]
        );
    };

    const clearFilters = () => {
        setSelectedMethods([]);
        setSelectedTags([]);
    };

    const selectSuggestion = (suggestion: string) => {
        setQuery(suggestion);
        setShowSuggestions(false);
    };

    const hasActiveFilters = selectedMethods.length > 0 || selectedTags.length > 0;

    return (
        <div className="min-h-screen bg-[#0a0a0a] text-white">
            {/* Header */}
            <header className="border-b border-white/10 bg-black/50 backdrop-blur-sm sticky top-0 z-50">
                <div className="max-w-4xl mx-auto px-6 py-4">
                    <div className="flex items-center gap-3 mb-4">
                        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
                            <Search size={20} />
                        </div>
                        <div>
                            <h1 className="text-xl font-semibold">Search APIs</h1>
                            <p className="text-xs text-gray-500">Find endpoints across all repositories</p>
                        </div>
                    </div>

                    {/* Search Input */}
                    <div className="relative">
                        <div className="relative flex items-center">
                            <Search size={18} className="absolute left-4 text-gray-400" />
                            <input
                                type="text"
                                value={query}
                                onChange={(e) => setQuery(e.target.value)}
                                onFocus={() => setShowSuggestions(true)}
                                placeholder="Search endpoints by path, description, or tags..."
                                className="w-full pl-12 pr-24 py-3 rounded-xl bg-white/5 border border-white/10 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500/50"
                            />

                            <div className="absolute right-3 flex items-center gap-2">
                                {loading && <Loader2 size={16} className="animate-spin text-gray-400" />}
                                <button
                                    onClick={() => setShowFilters(!showFilters)}
                                    className={cn(
                                        "p-2 rounded-lg transition-colors",
                                        showFilters || hasActiveFilters
                                            ? "bg-indigo-500/20 text-indigo-300"
                                            : "hover:bg-white/10 text-gray-400"
                                    )}
                                >
                                    <Filter size={16} />
                                </button>
                            </div>
                        </div>

                        {/* Suggestions Dropdown */}
                        {showSuggestions && !query && (
                            <div className="absolute top-full left-0 right-0 mt-2 bg-[#1a1a1a] border border-white/10 rounded-xl overflow-hidden z-50">
                                {recentSearches.length > 0 && (
                                    <div className="p-3 border-b border-white/5">
                                        <p className="text-xs text-gray-500 mb-2 flex items-center gap-1">
                                            <Clock size={12} /> Recent
                                        </p>
                                        <div className="space-y-1">
                                            {recentSearches.slice(0, 5).map((s, i) => (
                                                <button
                                                    key={i}
                                                    onClick={() => selectSuggestion(s)}
                                                    className="block w-full text-left px-2 py-1.5 text-sm hover:bg-white/5 rounded"
                                                >
                                                    {s}
                                                </button>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {popularTags.length > 0 && (
                                    <div className="p-3">
                                        <p className="text-xs text-gray-500 mb-2 flex items-center gap-1">
                                            <TrendingUp size={12} /> Popular Tags
                                        </p>
                                        <div className="flex flex-wrap gap-2">
                                            {popularTags.slice(0, 8).map((tag, i) => (
                                                <button
                                                    key={i}
                                                    onClick={() => toggleTag(tag)}
                                                    className="px-2 py-1 text-xs bg-white/5 hover:bg-white/10 rounded"
                                                >
                                                    {tag}
                                                </button>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>

                    {/* Filters Panel */}
                    {showFilters && (
                        <div className="mt-4 p-4 bg-white/5 rounded-xl border border-white/10">
                            <div className="flex items-center justify-between mb-3">
                                <span className="text-sm font-medium">Filters</span>
                                {hasActiveFilters && (
                                    <button
                                        onClick={clearFilters}
                                        className="text-xs text-gray-400 hover:text-white"
                                    >
                                        Clear all
                                    </button>
                                )}
                            </div>

                            {/* Method Filter */}
                            <div className="mb-4">
                                <p className="text-xs text-gray-400 mb-2">HTTP Method</p>
                                <div className="flex flex-wrap gap-2">
                                    {METHODS.map((method) => (
                                        <button
                                            key={method}
                                            onClick={() => toggleMethod(method)}
                                            className={cn(
                                                "px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors",
                                                selectedMethods.includes(method)
                                                    ? METHOD_COLORS[method]
                                                    : "border-white/10 text-gray-400 hover:border-white/20"
                                            )}
                                        >
                                            {method}
                                        </button>
                                    ))}
                                </div>
                            </div>

                            {/* Tags Filter */}
                            {popularTags.length > 0 && (
                                <div>
                                    <p className="text-xs text-gray-400 mb-2">Tags</p>
                                    <div className="flex flex-wrap gap-2">
                                        {popularTags.map((tag) => (
                                            <button
                                                key={tag}
                                                onClick={() => toggleTag(tag)}
                                                className={cn(
                                                    "px-3 py-1.5 rounded-lg text-xs border transition-colors",
                                                    selectedTags.includes(tag)
                                                        ? "bg-indigo-500/20 text-indigo-300 border-indigo-500/30"
                                                        : "border-white/10 text-gray-400 hover:border-white/20"
                                                )}
                                            >
                                                {tag}
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </header>

            {/* Results */}
            <div className="max-w-4xl mx-auto p-6">
                {/* Results count */}
                {query && (
                    <p className="text-sm text-gray-400 mb-4">
                        {loading ? "Searching..." : `${total} result${total !== 1 ? 's' : ''} for "${query}"`}
                    </p>
                )}

                {/* Results List */}
                <div className="space-y-3">
                    {results.map((result) => (
                        <GlassCard
                            key={result.endpoint_id}
                            className="p-4 hover:bg-white/[0.03] transition-colors cursor-pointer"
                        >
                            <div className="flex items-start gap-3">
                                <span className={cn(
                                    "text-[10px] font-bold px-2 py-1 rounded border flex-shrink-0",
                                    METHOD_COLORS[result.method]
                                )}>
                                    {result.method}
                                </span>

                                <div className="flex-1 min-w-0">
                                    <p
                                        className="font-mono text-sm mb-1"
                                        dangerouslySetInnerHTML={{
                                            __html: result.highlights?.path || result.path
                                        }}
                                    />

                                    {result.description && (
                                        <p
                                            className="text-sm text-gray-400 line-clamp-2"
                                            dangerouslySetInnerHTML={{
                                                __html: result.highlights?.description || result.description
                                            }}
                                        />
                                    )}

                                    <div className="flex items-center gap-3 mt-2">
                                        <span className="text-xs text-gray-500">
                                            {result.repository_name}
                                        </span>

                                        {result.tags && result.tags.length > 0 && (
                                            <div className="flex gap-1">
                                                {result.tags.slice(0, 3).map((tag, i) => (
                                                    <span
                                                        key={i}
                                                        className="text-[10px] px-1.5 py-0.5 bg-white/5 rounded"
                                                    >
                                                        {tag}
                                                    </span>
                                                ))}
                                            </div>
                                        )}

                                        {result.is_deprecated && (
                                            <span className="text-[10px] px-1.5 py-0.5 bg-amber-500/10 text-amber-400 rounded">
                                                Deprecated
                                            </span>
                                        )}
                                    </div>
                                </div>

                                <button className="p-2 hover:bg-white/10 rounded-lg text-gray-500 hover:text-white">
                                    <BookmarkPlus size={16} />
                                </button>
                            </div>
                        </GlassCard>
                    ))}
                </div>

                {/* Empty state */}
                {!loading && query && results.length === 0 && (
                    <div className="text-center py-16">
                        <Search size={48} className="mx-auto text-gray-600 mb-4" />
                        <p className="text-gray-400">No results found for "{query}"</p>
                        <p className="text-xs text-gray-600 mt-1">Try different keywords or adjust filters</p>
                    </div>
                )}

                {/* Initial state */}
                {!query && (
                    <div className="text-center py-16">
                        <Search size={48} className="mx-auto text-gray-600 mb-4" />
                        <p className="text-gray-400">Start typing to search</p>
                        <p className="text-xs text-gray-600 mt-1">
                            Search across {total || "all"} endpoints in your repositories
                        </p>
                    </div>
                )}
            </div>
        </div>
    );
}
