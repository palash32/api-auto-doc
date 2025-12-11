"use client";

import React, { useState, useRef, useEffect } from "react";
import { useGSAP } from "@gsap/react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { Flip } from "gsap/Flip";
import {
    LayoutDashboard,
    Search,
    GitBranch,
    Activity,
    Settings,
    ChevronLeft,
    ChevronRight,
    Plus,
    Terminal,
    Shield,
    Menu,
    Bell,
    Play
} from "lucide-react";
import { cn } from "@/lib/utils";
import { GlassCard } from "@/components/ui/glass-card";
import { MagneticButton } from "@/components/ui/magnetic-button";
import { SkeletonCard, SkeletonStatCard } from "@/components/ui/skeleton";
import { GsapRegistry } from "@/lib/gsap-registry";
import { api, Repository } from "@/lib/api";
import { AddRepositoryModal } from "@/components/add-repository-modal";
import { ActivityFeed, DEMO_ACTIVITIES } from "@/components/activity-feed";
import Link from "next/link";

// Register GSAP plugins
gsap.registerPlugin(ScrollTrigger, Flip);

// --- Mock Data ---
const HEALTH_STATS = [
    { label: "System Uptime", value: "99.99%", trend: "+0.01%", color: "text-emerald-400" },
    { label: "Avg Latency", value: "42ms", trend: "-5ms", color: "text-blue-400" },
    { label: "API Requests", value: "1.2M", trend: "+12%", color: "text-purple-400" },
    { label: "Security Score", value: "A+", trend: "Stable", color: "text-cyan-400" },
];

// --- Components ---

const Sidebar = ({ collapsed, setCollapsed }: { collapsed: boolean; setCollapsed: (v: boolean) => void }) => {
    const sidebarRef = useRef(null);

    useGSAP(() => {
        gsap.to(sidebarRef.current, {
            width: collapsed ? "80px" : "280px",
            duration: 0.5,
            ease: "power3.inOut",
        });
    }, [collapsed]);

    return (
        <div
            ref={sidebarRef}
            className="h-screen fixed left-0 top-0 z-50 bg-black/40 backdrop-blur-xl border-r border-white/10 flex flex-col transition-all duration-300 overflow-hidden"
        >
            <div className="p-6 flex items-center justify-between">
                {!collapsed && (
                    <span className="text-xl font-bold bg-gradient-to-r from-blue-400 to-purple-600 bg-clip-text text-transparent opacity-0 animate-in fade-in duration-500 fill-mode-forwards" style={{ animationDelay: "0.3s" }}>
                        AutoDoc<span className="text-white">AI</span>
                    </span>
                )}
                <button
                    onClick={() => setCollapsed(!collapsed)}
                    className="p-2 hover:bg-white/10 rounded-lg transition-colors ml-auto text-gray-400 hover:text-white"
                >
                    {collapsed ? <Menu size={20} /> : <ChevronLeft size={20} />}
                </button>
            </div>

            <nav className="flex-1 px-4 py-6 space-y-2">
                {[
                    { icon: LayoutDashboard, label: "Dashboard", href: "/dashboard", active: true },
                    { icon: GitBranch, label: "Repositories", href: "/apis" },
                    { icon: Play, label: "Playground", href: "/playground" },
                    { icon: Activity, label: "Monitoring", href: "/monitoring" },
                    { icon: Shield, label: "Security", href: "/security" },
                    { icon: Settings, label: "Settings", href: "/settings" },
                ].map((item, idx) => (
                    <Link
                        key={idx}
                        href={item.href}
                        className={cn(
                            "w-full flex items-center p-3 rounded-xl transition-all duration-300 group relative overflow-hidden",
                            item.active ? "bg-blue-600/20 text-blue-400" : "hover:bg-white/5 text-gray-400 hover:text-white"
                        )}
                    >
                        <item.icon size={22} className={cn("min-w-[22px]", item.active && "text-blue-400")} />
                        <span className={cn(
                            "ml-4 font-medium whitespace-nowrap transition-opacity duration-300",
                            collapsed ? "opacity-0 w-0" : "opacity-100"
                        )}>
                            {item.label}
                        </span>
                        {item.active && (
                            <div className="absolute left-0 top-0 w-1 h-full bg-blue-500 shadow-[0_0_10px_rgba(59,130,246,0.5)]" />
                        )}
                    </Link>
                ))}
            </nav>

            <div className="p-4 border-t border-white/10">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-purple-500 to-blue-500 flex items-center justify-center text-white font-bold shadow-lg">
                        US
                    </div>
                    <div className={cn("transition-opacity duration-300", collapsed ? "opacity-0 w-0 hidden" : "opacity-100")}>
                        <p className="text-sm font-medium text-white">UniSpark</p>
                        <p className="text-xs text-gray-400">Pro Plan</p>
                    </div>
                </div>
            </div>
        </div>
    );
};

const StatCard = ({ stat, index }: { stat: typeof HEALTH_STATS[0]; index: number }) => {
    // Deterministic width based on index to avoid hydration mismatch
    const progressWidth = [75, 82, 68, 90][index % 4];

    return (
        <GlassCard className="stat-card p-6" hoverEffect={true}>
            <p className="text-gray-400 text-sm font-medium mb-2">{stat.label}</p>
            <div className="flex items-end justify-between">
                <h3 className="text-3xl font-bold text-white tracking-tight">{stat.value}</h3>
                <span className={cn("text-sm font-medium px-2 py-1 rounded-full bg-white/5", stat.color)}>
                    {stat.trend}
                </span>
            </div>
            {/* Animated Chart Line (Simulated) */}
            <div className="mt-4 h-1 w-full bg-white/10 rounded-full overflow-hidden">
                <div
                    className={cn("h-full rounded-full animate-pulse", stat.color.replace('text-', 'bg-'))}
                    style={{ width: `${progressWidth}%` }}
                />
            </div>
        </GlassCard>
    );
};

const RepoCard = ({ repo }: { repo: Repository }) => {
    return (
        <GlassCard
            className="repo-card p-5 cursor-pointer group"
            hoverEffect={true}
            tiltEffect={true}
            onClick={() => window.location.href = `/apis?repo=${repo.id}`}
        >
            <div className="flex justify-between items-start mb-4">
                <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-blue-500/10 text-blue-400 group-hover:text-blue-300 group-hover:bg-blue-500/20 transition-colors">
                        <Terminal size={20} />
                    </div>
                    <div>
                        <h4 className="text-white font-semibold group-hover:text-blue-400 transition-colors">{repo.name}</h4>
                        <p className="text-xs text-gray-500">{repo.status} • {repo.last_scanned ? new Date(repo.last_scanned).toLocaleDateString() : 'Never scanned'}</p>
                    </div>
                </div>
                <div className={cn(
                    "px-2 py-1 rounded-full text-xs font-medium border",
                    repo.health_score > 90 ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" :
                        repo.health_score > 70 ? "bg-yellow-500/10 text-yellow-400 border-yellow-500/20" :
                            "bg-red-500/10 text-red-400 border-red-500/20"
                )}>
                    {repo.health_score}% Health
                </div>
            </div>

            <div className="space-y-3">
                <div className="flex justify-between text-xs text-gray-400">
                    <span>Documentation Coverage</span>
                    <span>{repo.health_score}%</span>
                </div>
                <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                    <div
                        className={cn(
                            "h-full rounded-full transition-all duration-1000 ease-out",
                            repo.health_score > 90 ? "bg-emerald-500" : repo.health_score > 70 ? "bg-yellow-500" : "bg-red-500"
                        )}
                        style={{ width: `${repo.health_score}%` }}
                    />
                </div>
            </div>

            <div className="mt-4 flex items-center justify-between opacity-0 group-hover:opacity-100 transition-opacity duration-300 transform translate-y-2 group-hover:translate-y-0">
                <button
                    onClick={() => window.location.href = `/apis?repo=${repo.id}`}
                    className="text-xs text-white hover:text-blue-400 flex items-center gap-1"
                >
                    View Details <ChevronRight size={12} />
                </button>
                <div className="flex -space-x-2">
                    {[1, 2, 3].map(i => (
                        <div key={i} className="w-6 h-6 rounded-full bg-gray-800 border border-black flex items-center justify-center text-[10px] text-gray-400">
                            U{i}
                        </div>
                    ))}
                </div>
            </div>
        </GlassCard>
    );
};

export default function DashboardPage() {
    const [collapsed, setCollapsed] = useState(false);
    const [repositories, setRepositories] = useState<Repository[]>([]);
    const [loading, setLoading] = useState(true);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [mounted, setMounted] = useState(false);
    const containerRef = useRef<HTMLDivElement>(null);

    const fetchRepos = async () => {
        try {
            const data = await api.getRepositories();
            setRepositories(data);
        } catch (err) {
            console.error("Failed to fetch repositories", err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        // Mark as mounted for hydration-safe client-only features
        setMounted(true);
        // Check authentication status on client side only
        setIsAuthenticated(!!localStorage.getItem('token'));
        fetchRepos();
    }, []);

    // GSAP Animations
    useGSAP(() => {
        // Breathing Background Animation - only if elements exist
        const ambientBlobs = document.querySelectorAll(".ambient-blob");
        if (ambientBlobs.length > 0) {
            gsap.to(".ambient-blob", {
                scale: 1.2,
                opacity: 0.15,
                duration: 8,
                repeat: -1,
                yoyo: true,
                ease: "sine.inOut",
                stagger: 2
            });
        }

        if (loading) return;

        const tl = gsap.timeline();

        // Staggered entry for stats
        tl.from(".stat-card", {
            y: 20,
            opacity: 0,
            duration: 0.6,
            stagger: 0.1,
            ease: "power2.out",
            clearProps: "all"
        });

        // Staggered entry for repos
        tl.from(".repo-card", {
            y: 20,
            opacity: 0,
            duration: 0.6,
            stagger: 0.05,
            ease: "power2.out",
            clearProps: "all"
        }, "-=0.3");

    }, { scope: containerRef, dependencies: [loading] });

    return (
        <div className="min-h-screen bg-background text-foreground font-sans selection:bg-primary/30">
            <GsapRegistry />
            <AddRepositoryModal
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                onSuccess={fetchRepos}
            />

            {/* Background Ambient Glow - Breathing */}
            <div className="fixed inset-0 pointer-events-none overflow-hidden">
                <div className="ambient-blob absolute top-[-10%] left-[-10%] w-[50%] h-[50%] bg-blue-600/10 rounded-full blur-[120px]" />
                <div className="ambient-blob absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] bg-purple-600/10 rounded-full blur-[120px]" />
                <div className="ambient-blob absolute top-[40%] left-[40%] w-[30%] h-[30%] bg-cyan-500/5 rounded-full blur-[100px]" />
            </div>

            <Sidebar collapsed={collapsed} setCollapsed={setCollapsed} />

            <main
                ref={containerRef}
                className={cn(
                    "transition-all duration-500 ease-[cubic-bezier(0.32,0.72,0,1)] min-h-screen p-8 relative z-10", // Apple-style ease
                    collapsed ? "ml-[80px]" : "ml-[280px]"
                )}
            >
                {/* Header / Search */}
                <header className="flex items-center justify-between mb-12">
                    <div>
                        <h1 className="text-3xl font-bold tracking-tight text-white">
                            Dashboard
                        </h1>
                        <p className="text-white/40 mt-1 font-medium">Welcome back, UniSpark</p>
                    </div>

                    <div className="flex items-center gap-4">
                        <div className="relative group">
                            <div className="absolute inset-0 bg-gradient-to-r from-blue-500/20 to-purple-500/20 rounded-xl blur opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                            <div className="relative bg-white/5 backdrop-blur-xl border border-white/10 rounded-xl flex items-center px-4 py-2.5 w-[300px] transition-all duration-300 ease-out focus-within:w-[400px] focus-within:bg-white/10 focus-within:border-white/20 focus-within:shadow-lg">
                                <Search size={18} className="text-white/40 mr-3" />
                                <input
                                    type="text"
                                    placeholder="Search repositories..."
                                    className="bg-transparent border-none outline-none text-sm text-white placeholder-white/30 w-full"
                                />
                                <div className="flex items-center gap-1 px-1.5 py-0.5 rounded bg-white/10 text-[10px] text-white/40 font-mono border border-white/5">
                                    <span>⌘</span><span>K</span>
                                </div>
                            </div>
                        </div>

                        <button className="p-2.5 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 hover:border-white/20 transition-all duration-300 text-white/60 hover:text-white active:scale-95">
                            <Bell size={20} />
                        </button>

                        {isAuthenticated ? (
                            <div className="flex items-center gap-3">
                                <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-purple-500 to-blue-500 flex items-center justify-center text-white font-bold shadow-lg cursor-pointer hover:scale-110 transition-transform">
                                    US
                                </div>
                            </div>
                        ) : (
                            <MagneticButton
                                onClick={() => window.location.href = 'http://localhost:8000/api/auth/github/login'}
                                className="bg-white/10 hover:bg-white/20 text-white px-4 py-2.5 rounded-xl font-medium flex items-center gap-2 border border-white/10 transition-all"
                            >
                                <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round" className="text-white">
                                    <path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"></path>
                                </svg>
                                Login with GitHub
                            </MagneticButton>
                        )}
                    </div>
                </header>

                {/* Hero Stats */}
                <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
                    {HEALTH_STATS.map((stat, i) => (
                        <StatCard key={i} stat={stat} index={i} />
                    ))}
                </section>

                {/* Main Content Grid */}
                <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
                    {/* Projects Grid - 3 columns */}
                    <section className="lg:col-span-3">
                        <div className="flex items-center justify-between mb-6">
                            <h2 className="text-xl font-semibold flex items-center gap-2 text-white/90">
                                <GitBranch size={20} className="text-primary" />
                                Active Repositories
                            </h2>
                            <MagneticButton
                                onClick={() => setIsModalOpen(true)}
                                className="px-5 py-2.5 text-sm bg-[#0071E3] hover:bg-[#0077ED] shadow-lg shadow-blue-500/20"
                            >
                                <Plus size={16} className="mr-2" />
                                Add Repository
                            </MagneticButton>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                            {loading ? (
                                // Loading Skeletons using reusable components
                                [1, 2, 3].map(i => (
                                    <SkeletonCard key={i} className="min-h-[180px]" />
                                ))
                            ) : (
                                repositories.map((repo) => (
                                    <RepoCard key={repo.id} repo={repo} />
                                ))
                            )}

                            {/* Add New Card Placeholder - Polished */}
                            {!loading && (
                                <GlassCard
                                    onClick={() => setIsModalOpen(true)}
                                    className="group border-dashed border-white/10 flex flex-col items-center justify-center text-white/40 hover:text-white hover:border-primary/30 hover:bg-primary/5 cursor-pointer min-h-[180px] transition-all duration-300"
                                    hoverEffect={false}
                                >
                                    <div className="w-14 h-14 rounded-full bg-white/5 flex items-center justify-center mb-4 group-hover:scale-110 group-hover:bg-primary/10 group-hover:text-primary transition-all duration-300">
                                        <Plus size={24} />
                                    </div>
                                    <p className="text-sm font-medium">Connect New Repository</p>
                                </GlassCard>
                            )}
                        </div>
                    </section>

                    {/* Activity Feed Sidebar - 1 column */}
                    <aside className="lg:col-span-1">
                        <GlassCard className="p-4 sticky top-24">
                            <ActivityFeed activities={DEMO_ACTIVITIES} maxItems={5} />
                        </GlassCard>
                    </aside>
                </div>
            </main>
        </div>
    );
}
