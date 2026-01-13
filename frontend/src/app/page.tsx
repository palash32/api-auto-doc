"use client";

import React, { useRef } from "react";
import { useGSAP } from "@gsap/react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import {
    ArrowRight,
    Check,
    Zap,
    Shield,
    Search,
    GitBranch,
    Database,
    Code2,
    Terminal
} from "lucide-react";
import { MagneticButton } from "@/components/ui/magnetic-button";
import { GlassCard } from "@/components/ui/glass-card";
import { GsapRegistry } from "@/lib/gsap-registry";
import Link from "next/link";

// Register plugins
gsap.registerPlugin(ScrollTrigger);

const FEATURES = [
    {
        title: "Auto-Discovery",
        description: "Automatically scans your GitHub repositories to find all API endpoints instantly.",
        icon: Search,
        color: "text-blue-400",
        bg: "bg-blue-500/10"
    },
    {
        title: "Live Documentation",
        description: "Beautiful, interactive API docs generated automatically from your code.",
        icon: Code2,
        color: "text-purple-400",
        bg: "bg-purple-500/10"
    },
    {
        title: "Multi-Language Support",
        description: "Works with Python, JavaScript, TypeScript, Go, Ruby, PHP, and more frameworks.",
        icon: GitBranch,
        color: "text-emerald-400",
        bg: "bg-emerald-500/10"
    },
];

// Pricing will be added in future updates

const COMPARISON = [
    { feature: "Auto API Discovery", autodoc: true, postman: false, swagger: false, readme: false },
    { feature: "Code-First Approach", autodoc: true, postman: false, swagger: true, readme: false },
    { feature: "Multi-Language Support", autodoc: true, postman: true, swagger: true, readme: true },
    { feature: "Zero Configuration", autodoc: true, postman: false, swagger: false, readme: false },
    { feature: "GitHub Integration", autodoc: true, postman: true, swagger: false, readme: true },
];

const TESTIMONIALS = [
    {
        quote: "AutoDocAI saved our team 10+ hours per week on documentation. It just works.",
        author: "Sarah Chen",
        role: "Engineering Lead",
        company: "TechFlow",
        avatar: "SC"
    },
    {
        quote: "Finally, documentation that stays up-to-date. Our API docs are now always accurate.",
        author: "Marcus Rodriguez",
        role: "CTO",
        company: "DataPipe",
        avatar: "MR"
    },
    {
        quote: "The AI-generated examples are surprisingly good. Better than what we wrote manually.",
        author: "Emily Watson",
        role: "Senior Developer",
        company: "CloudScale",
        avatar: "EW"
    }
];

export default function LandingPage() {
    const containerRef = useRef<HTMLDivElement>(null);


    useGSAP(() => {
        const tl = gsap.timeline();

        // Hero Animation
        tl.from(".hero-badge", {
            y: -20,
            opacity: 0,
            duration: 0.6,
            ease: "power3.out",
            clearProps: "all"
        })
            .from(".hero-headline span", {
                y: 100,
                opacity: 0,
                duration: 1,
                stagger: 0.1,
                ease: "power4.out",
                clearProps: "all"
            }, "-=0.4")
            .from(".hero-subheadline", {
                y: 30,
                opacity: 0,
                duration: 0.8,
                ease: "power3.out",
                clearProps: "all"
            }, "-=0.6")
            .from(".hero-cta", {
                scale: 0.9,
                opacity: 0,
                duration: 0.6,
                stagger: 0.1,
                ease: "back.out(1.7)",
                clearProps: "all"
            }, "-=0.4")
            .from(".hero-visual", {
                y: 50,
                opacity: 0,
                duration: 1.2,
                ease: "power3.out",
                clearProps: "all"
            }, "-=0.8");

        // Features Scroll Animation
        gsap.from(".feature-card", {
            scrollTrigger: {
                trigger: ".features-grid",
                start: "top 80%",
            },
            y: 50,
            opacity: 0,
            duration: 0.8,
            stagger: 0.1,
            ease: "power3.out",
            clearProps: "all"
        });

    }, { scope: containerRef });

    return (
        <div ref={containerRef} className="min-h-screen bg-background text-foreground overflow-x-hidden selection:bg-primary/30">
            <GsapRegistry />

            {/* Navbar */}
            <nav className="fixed top-0 left-0 right-0 z-50 border-b border-white/5 bg-background/60 backdrop-blur-xl">
                <div className="container mx-auto px-6 h-16 flex items-center justify-between">
                    <div className="flex items-center gap-2 font-bold text-xl tracking-tight">
                        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-600 to-purple-600 flex items-center justify-center text-white">
                            <Terminal size={18} />
                        </div>
                        <span>AutoDoc<span className="text-primary">AI</span></span>
                    </div>
                    <div className="hidden md:flex items-center gap-8 text-sm font-medium text-muted-foreground">
                        <Link href="#features" className="hover:text-white transition-colors">Features</Link>
                        <Link href="#how-it-works" className="hover:text-white transition-colors">How It Works</Link>
                    </div>
                    <div className="flex items-center gap-4">
                        <Link href="/login">
                            <MagneticButton className="px-5 py-2 text-sm">
                                Sign In
                            </MagneticButton>
                        </Link>
                    </div>
                </div>
            </nav>

            {/* Hero Section */}
            <section className="relative pt-32 pb-20 md:pt-48 md:pb-32 overflow-hidden">
                {/* Background Gradients */}
                <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1000px] h-[600px] bg-blue-600/20 rounded-full blur-[120px] -z-10 opacity-50" />
                <div className="absolute bottom-0 right-0 w-[800px] h-[600px] bg-purple-600/10 rounded-full blur-[100px] -z-10 opacity-30" />

                <div className="container mx-auto px-6 text-center relative z-10">
                    <div className="hero-badge inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-xs font-medium text-blue-400 mb-8">
                        <span className="relative flex h-2 w-2">
                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
                            <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500"></span>
                        </span>
                        v2.0 is now live
                    </div>

                    <h1 className="hero-headline text-5xl md:text-7xl font-bold tracking-tight mb-6 leading-[1.1]">
                        <span className="block bg-gradient-to-b from-white to-white/60 bg-clip-text text-transparent">Turn API Chaos</span>
                        <span className="block bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">Into Clarity</span>
                    </h1>

                    <p className="hero-subheadline text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto mb-10 leading-relaxed">
                        Automatically discover, document, and monitor every API in your organization.
                        Save weeks of debugging time with AI-powered insights.
                    </p>

                    <div className="flex items-center justify-center mb-20">
                        <Link href="/login" className="hero-cta">
                            <MagneticButton className="px-8 py-4 text-lg shadow-[0_0_30px_rgba(0,113,227,0.3)]">
                                Start Free Trial <ArrowRight className="ml-2 w-5 h-5" />
                            </MagneticButton>
                        </Link>
                    </div>

                    {/* Live Code-to-Docs Demo */}
                    <div className="hero-visual max-w-5xl mx-auto">
                        <GlassCard className="p-2 bg-black/40 border-white/10 rounded-xl shadow-2xl backdrop-blur-xl">
                            <div className="bg-[#0A0A0A] rounded-lg border border-white/5 overflow-hidden aspect-[16/9] relative group">
                                <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-purple-500/5" />

                                {/* Window Title Bar */}
                                <div className="absolute top-0 left-0 right-0 h-10 bg-white/5 border-b border-white/5 flex items-center px-4 gap-2">
                                    <div className="flex gap-1.5">
                                        <div className="w-3 h-3 rounded-full bg-red-500/20 border border-red-500/50" />
                                        <div className="w-3 h-3 rounded-full bg-yellow-500/20 border border-yellow-500/50" />
                                        <div className="w-3 h-3 rounded-full bg-green-500/20 border border-green-500/50" />
                                    </div>
                                    <div className="mx-auto flex gap-2">
                                        <div className="px-3 py-1 rounded-md bg-blue-500/10 border border-blue-500/20 text-[10px] text-blue-400 font-mono">
                                            Code
                                        </div>
                                        <div className="px-3 py-1 rounded-md bg-white/5 border border-white/5 text-[10px] text-gray-400 font-mono">
                                            → Docs
                                        </div>
                                    </div>
                                </div>

                                {/* Split View: Code → Documentation */}
                                <div className="mt-10 h-[calc(100%-40px)] grid grid-cols-2 divide-x divide-white/5">
                                    {/* Left: Code Panel */}
                                    <div className="p-4 overflow-hidden relative">
                                        <div className="text-[10px] text-gray-500 mb-2 font-mono">main.py</div>
                                        <div className="font-mono text-[11px] leading-relaxed overflow-hidden h-full">
                                            <div className="animate-code-scroll">
                                                <div><span className="text-purple-400">from</span> <span className="text-blue-400">fastapi</span> <span className="text-purple-400">import</span> FastAPI</div>
                                                <div className="mt-1"><span className="text-gray-500"># Initialize app</span></div>
                                                <div>app = <span className="text-yellow-400">FastAPI</span>()</div>
                                                <div className="mt-3"><span className="text-purple-400">@app</span>.get(<span className="text-green-400">"/users"</span>)</div>
                                                <div><span className="text-purple-400">async def</span> <span className="text-blue-400">get_users</span>():</div>
                                                <div className="pl-4"><span className="text-gray-500">"""Fetch all users"""</span></div>
                                                <div className="pl-4"><span className="text-purple-400">return</span> {'{"users": []}'}</div>
                                                <div className="mt-3"><span className="text-purple-400">@app</span>.post(<span className="text-green-400">"/users"</span>)</div>
                                                <div><span className="text-purple-400">async def</span> <span className="text-blue-400">create_user</span>(user: User):</div>
                                                <div className="pl-4"><span className="text-gray-500">"""Create a new user"""</span></div>
                                                <div className="pl-4"><span className="text-purple-400">return</span> user</div>
                                                <div className="mt-3"><span className="text-purple-400">@app</span>.get(<span className="text-green-400">"/health"</span>)</div>
                                                <div><span className="text-purple-400">async def</span> <span className="text-blue-400">health</span>():</div>
                                                <div className="pl-4"><span className="text-purple-400">return</span> {'{"status": "ok"}'}</div>
                                                {/* Duplicate for continuous scroll */}
                                                <div className="mt-8"><span className="text-purple-400">from</span> <span className="text-blue-400">fastapi</span> <span className="text-purple-400">import</span> FastAPI</div>
                                                <div className="mt-1"><span className="text-gray-500"># Initialize app</span></div>
                                                <div>app = <span className="text-yellow-400">FastAPI</span>()</div>
                                            </div>
                                        </div>
                                    </div>

                                    {/* Right: Generated Docs Panel */}
                                    <div className="p-4 bg-white/[0.02]">
                                        <div className="text-[10px] text-gray-500 mb-2 font-mono">Generated Documentation</div>
                                        <div className="space-y-3">
                                            <div className="p-3 rounded-lg bg-white/5 border border-white/5">
                                                <div className="flex items-center gap-2 mb-2">
                                                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-400">GET</span>
                                                    <span className="text-sm text-white font-mono">/users</span>
                                                </div>
                                                <p className="text-[11px] text-gray-400">Fetch all users from the database. Returns a list of user objects.</p>
                                            </div>
                                            <div className="p-3 rounded-lg bg-white/5 border border-white/5">
                                                <div className="flex items-center gap-2 mb-2">
                                                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-500/20 text-blue-400">POST</span>
                                                    <span className="text-sm text-white font-mono">/users</span>
                                                </div>
                                                <p className="text-[11px] text-gray-400">Create a new user. Requires user data in request body.</p>
                                            </div>
                                            <div className="p-3 rounded-lg bg-white/5 border border-white/5">
                                                <div className="flex items-center gap-2 mb-2">
                                                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-400">GET</span>
                                                    <span className="text-sm text-white font-mono">/health</span>
                                                </div>
                                                <p className="text-[11px] text-gray-400">Health check endpoint. Returns system status.</p>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                {/* Floating Badge */}
                                <div className="absolute bottom-4 right-4 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-medium flex items-center gap-2 backdrop-blur-md animate-pulse-glow">
                                    <Check size={12} />3 endpoints documented
                                </div>

                                {/* Processing Indicator */}
                                <div className="absolute bottom-4 left-4 px-3 py-1.5 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-xs font-medium flex items-center gap-2 backdrop-blur-md">
                                    <div className="w-2 h-2 rounded-full bg-blue-400 animate-ping" />
                                    AI generating...
                                </div>
                            </div>
                        </GlassCard>
                        <p className="text-center text-sm text-muted-foreground mt-4">Connect your repository in 30 seconds → Get beautiful docs instantly</p>
                    </div>
                </div>
            </section>

            {/* How It Works Section */}
            <section id="how-it-works" className="py-24 relative border-y border-white/5 bg-white/[0.02]">
                <div className="container mx-auto px-6">
                    <div className="text-center mb-16">
                        <h2 className="text-3xl md:text-4xl font-bold mb-4">From Code to Docs in Seconds</h2>
                        <p className="text-muted-foreground">No manual writing. No outdated wikis. Just pure automation.</p>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-12 relative">
                        {/* Connecting Line (Desktop) */}
                        <div className="hidden md:block absolute top-12 left-0 w-full h-0.5 bg-gradient-to-r from-transparent via-blue-500/20 to-transparent" />

                        {[
                            {
                                step: "01",
                                title: "Connect",
                                desc: "Link your GitHub repository with a single click.",
                                icon: GitBranch,
                                color: "text-blue-400"
                            },
                            {
                                step: "02",
                                title: "Scan",
                                desc: "Our AI analyzes your code structure and dependencies.",
                                icon: Search,
                                color: "text-purple-400"
                            },
                            {
                                step: "03",
                                title: "Document",
                                desc: "Get instant, interactive API documentation.",
                                icon: Database,
                                color: "text-emerald-400"
                            }
                        ].map((item, i) => (
                            <div key={i} className="relative flex flex-col items-center text-center group">
                                <div className={`w-24 h-24 rounded-2xl bg-[#0A0A0A] border border-white/10 flex items-center justify-center mb-6 relative z-10 group-hover:scale-110 transition-transform duration-300 shadow-2xl`}>
                                    <div className={`absolute inset-0 bg-${item.color.split('-')[1]}-500/10 rounded-2xl blur-xl opacity-0 group-hover:opacity-100 transition-opacity`} />
                                    <item.icon className={`w-10 h-10 ${item.color}`} />
                                    <div className="absolute -top-3 -right-3 w-8 h-8 rounded-full bg-white/10 border border-white/10 flex items-center justify-center text-xs font-bold backdrop-blur-md">
                                        {item.step}
                                    </div>
                                </div>
                                <h3 className="text-xl font-semibold mb-2">{item.title}</h3>
                                <p className="text-muted-foreground text-sm max-w-[250px]">{item.desc}</p>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* Features Section */}
            <section id="features" className="py-32 relative">
                <div className="container mx-auto px-6">
                    <div className="text-center mb-20">
                        <h2 className="text-3xl md:text-4xl font-bold mb-4">Everything you need to scale</h2>
                        <p className="text-muted-foreground max-w-2xl mx-auto">
                            Powerful features designed for modern engineering teams.
                        </p>
                    </div>

                    <div className="features-grid grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {FEATURES.map((feature, idx) => (
                            <GlassCard
                                key={idx}
                                className="feature-card p-8 hover:bg-white/10 transition-colors group"
                                hoverEffect={true}
                            >
                                <div className={`w-12 h-12 rounded-xl ${feature.bg} ${feature.color} flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300`}>
                                    <feature.icon size={24} />
                                </div>
                                <h3 className="text-xl font-semibold mb-3 text-white">{feature.title}</h3>
                                <p className="text-muted-foreground leading-relaxed">
                                    {feature.description}
                                </p>
                            </GlassCard>
                        ))}
                    </div>
                </div>
            </section>

            {/* Comparison Matrix Section */}
            <section className="py-24 relative border-y border-white/5 bg-white/[0.01]">
                <div className="container mx-auto px-6">
                    <div className="text-center mb-16">
                        <h2 className="text-3xl md:text-4xl font-bold mb-4">Why teams switch to AutoDocAI</h2>
                        <p className="text-muted-foreground">Compare us with traditional documentation tools.</p>
                    </div>

                    <div className="max-w-4xl mx-auto overflow-x-auto">
                        <table className="w-full">
                            <thead>
                                <tr className="border-b border-white/10">
                                    <th className="p-4 text-left text-sm font-medium text-muted-foreground">Feature</th>
                                    <th className="p-4 text-center">
                                        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20">
                                            <Terminal size={14} className="text-blue-400" />
                                            <span className="text-sm font-medium text-blue-400">AutoDocAI</span>
                                        </div>
                                    </th>
                                    <th className="p-4 text-center text-sm font-medium text-muted-foreground">Postman</th>
                                    <th className="p-4 text-center text-sm font-medium text-muted-foreground">Swagger</th>
                                    <th className="p-4 text-center text-sm font-medium text-muted-foreground">Readme</th>
                                </tr>
                            </thead>
                            <tbody>
                                {COMPARISON.map((row, idx) => (
                                    <tr key={idx} className="border-b border-white/5 hover:bg-white/[0.02] transition-colors">
                                        <td className="p-4 text-sm text-white">{row.feature}</td>
                                        <td className="p-4 text-center">
                                            {row.autodoc ? (
                                                <div className="inline-flex w-6 h-6 rounded-full bg-emerald-500/20 items-center justify-center">
                                                    <Check size={14} className="text-emerald-400" />
                                                </div>
                                            ) : (
                                                <span className="text-gray-600">—</span>
                                            )}
                                        </td>
                                        <td className="p-4 text-center">
                                            {row.postman ? (
                                                <div className="inline-flex w-6 h-6 rounded-full bg-white/10 items-center justify-center">
                                                    <Check size={14} className="text-gray-400" />
                                                </div>
                                            ) : (
                                                <span className="text-gray-600">—</span>
                                            )}
                                        </td>
                                        <td className="p-4 text-center">
                                            {row.swagger ? (
                                                <div className="inline-flex w-6 h-6 rounded-full bg-white/10 items-center justify-center">
                                                    <Check size={14} className="text-gray-400" />
                                                </div>
                                            ) : (
                                                <span className="text-gray-600">—</span>
                                            )}
                                        </td>
                                        <td className="p-4 text-center">
                                            {row.readme ? (
                                                <div className="inline-flex w-6 h-6 rounded-full bg-white/10 items-center justify-center">
                                                    <Check size={14} className="text-gray-400" />
                                                </div>
                                            ) : (
                                                <span className="text-gray-600">—</span>
                                            )}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            </section>

            {/* Social Proof / Testimonials Section */}
            <section className="py-24 relative">
                <div className="container mx-auto px-6">
                    <div className="text-center mb-16">
                        <h2 className="text-3xl md:text-4xl font-bold mb-4">Loved by engineering teams</h2>
                        <p className="text-muted-foreground">Join hundreds of teams shipping better documentation.</p>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl mx-auto">
                        {TESTIMONIALS.map((testimonial, idx) => (
                            <GlassCard
                                key={idx}
                                className="p-8 hover:bg-white/10 transition-colors"
                                hoverEffect={true}
                            >
                                <div className="flex items-center gap-4 mb-6">
                                    <div className="w-12 h-12 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center text-white font-bold">
                                        {testimonial.avatar}
                                    </div>
                                    <div>
                                        <div className="font-semibold text-white">{testimonial.author}</div>
                                        <div className="text-sm text-muted-foreground">{testimonial.role} at {testimonial.company}</div>
                                    </div>
                                </div>
                                <p className="text-gray-300 leading-relaxed italic">"{testimonial.quote}"</p>
                            </GlassCard>
                        ))}
                    </div>

                    {/* Stats Row */}
                    <div className="mt-20 grid grid-cols-2 md:grid-cols-4 gap-8 max-w-4xl mx-auto text-center">
                        {[
                            { value: "100%", label: "Free during beta" },
                            { value: "30s", label: "Setup time" },
                            { value: "5+", label: "Languages supported" },
                            { value: "∞", label: "APIs documented" }
                        ].map((stat, idx) => (
                            <div key={idx}>
                                <div className="text-4xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                                    {stat.value}
                                </div>
                                <div className="text-sm text-muted-foreground mt-1">{stat.label}</div>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* CTA Section - Free to Use */}
            <section className="py-24 relative bg-gradient-to-b from-transparent to-black/50">
                <div className="container mx-auto px-6 text-center">
                    <h2 className="text-3xl md:text-4xl font-bold mb-4">Ready to streamline your API docs?</h2>
                    <p className="text-muted-foreground max-w-2xl mx-auto mb-8">
                        Connect your GitHub repository in 30 seconds and get beautiful,
                        auto-generated documentation. No credit card required.
                    </p>
                    <div className="flex justify-center">
                        <Link href="/login">
                            <MagneticButton className="px-8 py-4 text-lg shadow-[0_0_30px_rgba(0,113,227,0.3)]">
                                Get Started Free <ArrowRight className="ml-2 w-5 h-5" />
                            </MagneticButton>
                        </Link>
                    </div>
                </div>
            </section>

            {/* Footer */}
            <footer className="py-12 border-t border-white/10 bg-black/40 backdrop-blur-xl">
                <div className="container mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-6">
                    <div className="flex items-center gap-2 font-bold text-lg">
                        <div className="w-6 h-6 rounded bg-gradient-to-br from-blue-600 to-purple-600 flex items-center justify-center text-white text-xs">
                            <Terminal size={14} />
                        </div>
                        <span>AutoDoc<span className="text-primary">AI</span></span>
                    </div>
                    <div className="text-sm text-muted-foreground">
                        © 2025 UniSpark Inc. All rights reserved.
                    </div>
                    <div className="flex gap-6 text-sm text-muted-foreground">
                        <a href="#" className="hover:text-white transition-colors">Privacy</a>
                        <a href="#" className="hover:text-white transition-colors">Terms</a>
                        <a href="#" className="hover:text-white transition-colors">Contact</a>
                    </div>
                </div>
            </footer>
        </div>
    );
}
