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
    Play,
    Github
} from "lucide-react";
import { cn } from "@/lib/utils";
import { GlassCard } from "@/components/ui/glass-card";
import { MagneticButton } from "@/components/ui/magnetic-button";
import { SkeletonCard, SkeletonStatCard } from "@/components/ui/skeleton";
import { GsapRegistry } from "@/lib/gsap-registry";
import { api, Repository, DashboardStats, ActivityItem } from "@/lib/api";
import { AddRepositoryModal } from "@/components/add-repository-modal";
import { ActivityFeed } from "@/components/activity-feed";
import Link from "next/link";
import { API_BASE_URL } from "@/lib/api";

// Register GSAP plugins
gsap.registerPlugin(ScrollTrigger, Flip);

// --- Components ---

const Sidebar = ({ collapsed, setCollapsed, userName }: { collapsed: boolean; setCollapsed: (v: boolean) => void; userName: string }) => {
    const sidebarRef = useRef(null);
    const initials = userName.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2) || 'U';

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
                    { icon: Activity, label: "Monitoring", href: "/health" },
                    { icon: Shield, label: "Security", href: "/settings/security" },
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
                        {initials}
                    </div>
                    <div className={cn("transition-opacity duration-300", collapsed ? "opacity-0 w-0 hidden" : "opacity-100")}>
                        <p className="text-sm font-medium text-white">{userName}</p>
                        <p className="text-xs text-gray-400">Pro Plan</p>
                    </div>
                </div>
            </div>
        </div>
    );
};

interface HealthStat {
    label: string;
    value: string;
    trend: string;
    color: string;
}

const StatCard = ({ stat, index }: { stat: HealthStat; index: number }) => {
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
                    onClick={(e) => {
                        e.stopPropagation();
                        window.location.href = `/apis?repo=${repo.id}`;
                    }}
                    className="text-xs text-white hover:text-blue-400 flex items-center gap-1"
                >
                    View Details <ChevronRight size={12} />
                </button>
                <button
                    onClick={async (e) => {
                        e.stopPropagation();
                        try {
                            const token = localStorage.getItem('token');
                            await fetch(`${API_BASE_URL}/api/repositories/${repo.id}/scan`, {
                                method: 'POST',
                                headers: token ? { 'Authorization': `Bearer ${token}` } : {}
                            });
                            alert('Scan initiated! Please refresh in a moment.');
                        } catch (error) {
                            alert('Failed to start scan. Please try again.');
                        }
                    }}
                    className="px-3 py-1.5 text-xs bg-blue-500/20 hover:bg-blue-500/30 text-blue-400 rounded-lg flex items-center gap-1 transition-colors"
                >
                    <Activity size={12} /> Scan Now
                </button>
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
    const [githubConnected, setGithubConnected] = useState(true); // Default true to hide button until we know
    const [userName, setUserName] = useState("User");
    const [userEmail, setUserEmail] = useState("");
    const [mounted, setMounted] = useState(false);
    const [searchQuery, setSearchQuery] = useState("");
    const [showNotifications, setShowNotifications] = useState(false);
    const [showProfileMenu, setShowProfileMenu] = useState(false);
    const containerRef = useRef<HTMLDivElement>(null);

    // Real-time dashboard data
    const [dashboardStats, setDashboardStats] = useState<DashboardStats>({
        totalRepositories: 0,
        totalEndpoints: 0,
        avgHealthScore: 0,
        lastScanTime: null,
        scanningCount: 0
    });
    const [activities, setActivities] = useState<ActivityItem[]>([]);

    // Notifications derived from activities
    const notifications = activities.slice(0, 5).map((a, i) => ({
        id: i + 1,
        title: a.title,
        message: a.description || '',
        time: formatTimeAgo(new Date(a.createdAt)),
        read: i > 2 // Mark first 3 as unread
    }));

    // Format time ago helper
    function formatTimeAgo(date: Date): string {
        const now = new Date();
        const diffMs = now.getTime() - date.getTime();
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMins / 60);
        const diffDays = Math.floor(diffHours / 24);
        if (diffMins < 1) return "Just now";
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        if (diffDays < 7) return `${diffDays}d ago`;
        return date.toLocaleDateString();
    }

    // Mark all notifications as read (no-op since derived from activities)
    const markAllRead = () => { };

    // Filter repositories based on search
    const filteredRepos = repositories.filter(repo =>
        repo.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        repo.url?.toLowerCase().includes(searchQuery.toLowerCase())
    );

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
        const token = localStorage.getItem('token');
        setIsAuthenticated(!!token);

        // Fetch user info to check GitHub connection status
        if (token) {
            fetch(`${API_BASE_URL}/api/auth/me`, {
                headers: { 'Authorization': `Bearer ${token}` }
            })
                .then(res => res.ok ? res.json() : null)
                .then(user => {
                    if (user) {
                        setGithubConnected(user.github_connected ?? false);
                        setUserName(user.full_name || user.email?.split('@')[0] || 'User');
                        setUserEmail(user.email || '');
                    }
                })
                .catch(() => setGithubConnected(false));
        }

        fetchRepos();

        // Fetch dashboard stats and activity
        api.getDashboardStats().then(setDashboardStats);
        api.getDashboardActivity().then(setActivities);

        // Set up periodic refresh for real-time updates (every 10 seconds)
        const refreshInterval = setInterval(() => {
            api.getDashboardStats().then(setDashboardStats);
            api.getDashboardActivity().then(setActivities);
        }, 10000);

        // Cleanup interval on unmount
        return () => clearInterval(refreshInterval);
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

            <Sidebar collapsed={collapsed} setCollapsed={setCollapsed} userName={userName} />

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
                        <p className="text-white/40 mt-1 font-medium">Welcome back, {userName}</p>
                    </div>

                    <div className="flex items-center gap-4">
                        <div className="relative group">
                            <div className="absolute inset-0 bg-gradient-to-r from-blue-500/20 to-purple-500/20 rounded-xl blur opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                            <div className="relative bg-white/5 backdrop-blur-xl border border-white/10 rounded-xl flex items-center px-4 py-2.5 w-[300px] transition-all duration-300 ease-out focus-within:w-[400px] focus-within:bg-white/10 focus-within:border-white/20 focus-within:shadow-lg">
                                <Search size={18} className="text-white/40 mr-3" />
                                <input
                                    type="text"
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                    placeholder="Search repositories..."
                                    className="bg-transparent border-none outline-none text-sm text-white placeholder-white/30 w-full"
                                />
                                {searchQuery && (
                                    <button
                                        onClick={() => setSearchQuery("")}
                                        className="text-white/40 hover:text-white mr-2"
                                    >
                                        ×
                                    </button>
                                )}
                                <div className="flex items-center gap-1 px-1.5 py-0.5 rounded bg-white/10 text-[10px] text-white/40 font-mono border border-white/5">
                                    <span>⌘</span><span>K</span>
                                </div>
                            </div>
                        </div>

                        {/* Connect GitHub Button - Only show for email users */}
                        {!githubConnected && (
                            <button
                                onClick={() => window.location.href = `${API_BASE_URL}/api/auth/github/login`}
                                className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 hover:border-white/20 transition-all duration-300 text-white/80 hover:text-white"
                            >
                                <Github size={18} />
                                <span className="text-sm font-medium">Connect GitHub</span>
                            </button>
                        )}

                        <div className="relative">
                            <button
                                onClick={() => setShowNotifications(!showNotifications)}
                                className="p-2.5 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 hover:border-white/20 transition-all duration-300 text-white/60 hover:text-white active:scale-95 relative"
                            >
                                <Bell size={20} />
                                {notifications.filter(n => !n.read).length > 0 && (
                                    <span className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 rounded-full text-[10px] flex items-center justify-center text-white">
                                        {notifications.filter(n => !n.read).length}
                                    </span>
                                )}
                            </button>

                            {showNotifications && (
                                <div className="absolute right-0 top-12 w-80 bg-[#1a1a1a] backdrop-blur-xl border border-white/20 rounded-xl shadow-2xl z-50 overflow-hidden">
                                    <div className="p-3 border-b border-white/10 flex items-center justify-between">
                                        <h4 className="text-sm font-medium">Notifications</h4>
                                        <button
                                            onClick={markAllRead}
                                            className="text-xs text-blue-400 hover:text-blue-300 cursor-pointer"
                                        >
                                            Mark all read
                                        </button>
                                    </div>
                                    <div className="max-h-80 overflow-y-auto">
                                        {notifications.map(n => (
                                            <div key={n.id} className={`p-3 border-b border-white/5 hover:bg-white/5 cursor-pointer ${!n.read ? 'bg-blue-500/5' : ''}`}>
                                                <div className="flex items-center justify-between">
                                                    <p className="text-sm font-medium">{n.title}</p>
                                                    <span className="text-[10px] text-gray-500">{n.time}</span>
                                                </div>
                                                <p className="text-xs text-gray-400 mt-0.5">{n.message}</p>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>

                        {isAuthenticated ? (
                            <div className="relative">
                                <button
                                    onClick={() => setShowProfileMenu(!showProfileMenu)}
                                    className="w-10 h-10 rounded-full bg-gradient-to-tr from-purple-500 to-blue-500 flex items-center justify-center text-white font-bold shadow-lg cursor-pointer hover:scale-110 transition-transform"
                                >
                                    {userName.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2) || 'U'}
                                </button>

                                {showProfileMenu && (
                                    <div className="absolute right-0 top-12 w-56 bg-[#1a1a1a] backdrop-blur-xl border border-white/20 rounded-xl shadow-2xl z-50 overflow-hidden">
                                        <div className="p-3 border-b border-white/10">
                                            <p className="text-sm font-medium text-white">{userName}</p>
                                            <p className="text-xs text-gray-400">{userEmail}</p>
                                        </div>
                                        <div className="p-2">
                                            <button
                                                onClick={() => window.location.href = '/settings'}
                                                className="w-full text-left px-3 py-2 text-sm text-gray-300 hover:bg-white/10 rounded-lg transition-colors flex items-center gap-2"
                                            >
                                                <Settings size={14} />
                                                Settings
                                            </button>
                                            <button
                                                onClick={() => {
                                                    localStorage.removeItem('token');
                                                    window.location.href = '/';
                                                }}
                                                className="w-full text-left px-3 py-2 text-sm text-red-400 hover:bg-red-500/10 rounded-lg transition-colors flex items-center gap-2"
                                            >
                                                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" /><polyline points="16 17 21 12 16 7" /><line x1="21" x2="9" y1="12" y2="12" /></svg>
                                                Logout
                                            </button>
                                        </div>
                                    </div>
                                )}
                            </div>
                        ) : (
                            <MagneticButton
                                onClick={() => window.location.href = `${API_BASE_URL}/api/auth/github/login`}
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
                    {[
                        {
                            label: "Total Repositories",
                            value: String(dashboardStats.totalRepositories),
                            trend: dashboardStats.scanningCount > 0 ? `${dashboardStats.scanningCount} scanning` : "All complete",
                            color: "text-emerald-400"
                        },
                        {
                            label: "APIs Discovered",
                            value: String(dashboardStats.totalEndpoints),
                            trend: dashboardStats.totalEndpoints > 0 ? "+documented" : "Scan repos",
                            color: "text-blue-400"
                        },
                        {
                            label: "Currently Scanning",
                            value: String(dashboardStats.scanningCount),
                            trend: dashboardStats.scanningCount > 0 ? "In progress" : "Idle",
                            color: "text-purple-400"
                        },
                        {
                            label: "Health Score",
                            value: `${dashboardStats.avgHealthScore}%`,
                            trend: dashboardStats.avgHealthScore >= 80 ? "Good" : dashboardStats.avgHealthScore >= 50 ? "Fair" : "Needs work",
                            color: "text-cyan-400"
                        },
                    ].map((stat: HealthStat, i: number) => (
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
                            ) : filteredRepos.length > 0 ? (
                                filteredRepos.map((repo) => (
                                    <RepoCard key={repo.id} repo={repo} />
                                ))
                            ) : (
                                <div className="col-span-full">
                                    <div
                                        onClick={() => setIsModalOpen(true)}
                                        className="group border-2 border-dashed border-white/10 rounded-2xl flex items-center justify-between px-6 text-white/40 hover:text-white hover:border-primary/30 hover:bg-primary/5 cursor-pointer h-[180px] transition-all duration-300"
                                    >
                                        <p className="text-sm font-medium">Connect New Repository</p>
                                        <div className="w-12 h-12 rounded-full bg-white/5 flex items-center justify-center group-hover:scale-110 group-hover:bg-primary/10 group-hover:text-primary transition-all duration-300">
                                            <Plus size={24} />
                                        </div>
                                    </div>
                                </div>
                            )}

                            {/* Add New Card Placeholder - Only show when repos exist */}
                            {!loading && filteredRepos.length > 0 && (
                                <GlassCard
                                    onClick={() => setIsModalOpen(true)}
                                    className="group border-dashed border-white/10 flex items-center justify-between px-6 text-white/40 hover:text-white hover:border-primary/30 hover:bg-primary/5 cursor-pointer min-h-[180px] transition-all duration-300"
                                    hoverEffect={false}
                                >
                                    <p className="text-sm font-medium">Connect New Repository</p>
                                    <div className="w-12 h-12 rounded-full bg-white/5 flex items-center justify-center group-hover:scale-110 group-hover:bg-primary/10 group-hover:text-primary transition-all duration-300">
                                        <Plus size={24} />
                                    </div>
                                </GlassCard>
                            )}
                        </div>
                    </section>

                    {/* Activity Feed Sidebar - 1 column */}
                    <aside className="lg:col-span-1">
                        <GlassCard className="p-4 sticky top-24">
                            <ActivityFeed
                                activities={activities.map(a => ({
                                    id: a.id,
                                    type: a.type,
                                    title: a.title,
                                    description: a.description || '',
                                    timestamp: new Date(a.createdAt),
                                    status: a.type === 'scan_completed' || a.type === 'repo_added' ? 'success' :
                                        a.type === 'scan_started' ? 'pending' :
                                            a.type === 'scan_failed' ? 'failed' : undefined,
                                    metadata: a.metadata
                                }))}
                                maxItems={5}
                            />
                        </GlassCard>
                    </aside>
                </div>
            </main>
        </div>
    );
}
