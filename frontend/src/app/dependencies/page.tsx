"use client";

import React, { useCallback, useRef } from 'react';
import ReactFlow, {
    Background,
    Controls,
    MiniMap,
    useNodesState,
    useEdgesState,
    addEdge,
    Connection,
    Edge,
    MarkerType,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { useGSAP } from "@gsap/react";
import gsap from "gsap";
import { AlertTriangle, Terminal, ArrowLeft, GitBranch } from "lucide-react";
import Link from "next/link";
import { MagneticButton } from "@/components/ui/magnetic-button";
import { GlassCard } from "@/components/ui/glass-card";
import { GsapRegistry } from "@/lib/gsap-registry";

// --- Mock Data ---
const INITIAL_NODES = [
    { id: '1', type: 'input', data: { label: 'API Gateway' }, position: { x: 250, y: 0 }, style: { background: '#1e1e24', color: '#fff', border: '1px solid #3b82f6', borderRadius: '12px', padding: '10px', width: 150 } },
    { id: '2', data: { label: 'Auth Service' }, position: { x: 100, y: 150 }, style: { background: '#1e1e24', color: '#fff', border: '1px solid #a855f7', borderRadius: '12px', padding: '10px', width: 150 } },
    { id: '3', data: { label: 'User Service' }, position: { x: 400, y: 150 }, style: { background: '#1e1e24', color: '#fff', border: '1px solid #10b981', borderRadius: '12px', padding: '10px', width: 150 } },
    { id: '4', data: { label: 'Payment Service' }, position: { x: 250, y: 300 }, style: { background: '#1e1e24', color: '#fff', border: '1px solid #f59e0b', borderRadius: '12px', padding: '10px', width: 150 } },
    { id: '5', type: 'output', data: { label: 'Stripe API' }, position: { x: 250, y: 450 }, style: { background: '#1e1e24', color: '#fff', border: '1px solid #6366f1', borderRadius: '12px', padding: '10px', width: 150 } },
];

const INITIAL_EDGES = [
    { id: 'e1-2', source: '1', target: '2', animated: true, style: { stroke: '#3b82f6' } },
    { id: 'e1-3', source: '1', target: '3', animated: true, style: { stroke: '#3b82f6' } },
    { id: 'e2-3', source: '2', target: '3', animated: true, style: { stroke: '#a855f7' } },
    { id: 'e3-4', source: '3', target: '4', animated: true, style: { stroke: '#10b981' } },
    { id: 'e4-5', source: '4', target: '5', animated: true, style: { stroke: '#f59e0b' }, markerEnd: { type: MarkerType.ArrowClosed } },
];

export default function DependencyGraphPage() {
    const [nodes, setNodes, onNodesChange] = useNodesState(INITIAL_NODES);
    const [edges, setEdges, onEdgesChange] = useEdgesState(INITIAL_EDGES);
    const containerRef = useRef<HTMLDivElement>(null);

    const onConnect = useCallback(
        (params: Edge | Connection) => setEdges((eds) => addEdge(params, eds)),
        [setEdges],
    );

    useGSAP(() => {
        // Animate graph container entry
        gsap.from(".graph-container", {
            scale: 0.95,
            opacity: 0,
            duration: 1,
            ease: "power3.out"
        });

        // Animate alert banner
        gsap.from(".alert-banner", {
            y: -50,
            opacity: 0,
            duration: 0.8,
            delay: 0.5,
            ease: "back.out(1.7)"
        });
    }, { scope: containerRef });

    return (
        <div ref={containerRef} className="min-h-screen bg-background text-foreground font-sans selection:bg-primary/30 flex flex-col">
            <GsapRegistry />

            {/* Navbar */}
            <nav className="h-16 border-b border-white/5 bg-background/60 backdrop-blur-xl sticky top-0 z-50 flex-shrink-0">
                <div className="container mx-auto px-6 h-full flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <Link href="/dashboard" className="p-2 hover:bg-white/5 rounded-lg transition-colors">
                            <ArrowLeft size={20} className="text-muted-foreground" />
                        </Link>
                        <div className="flex items-center gap-2 font-bold text-lg">
                            <GitBranch className="text-primary" size={20} />
                            <span>Dependency Graph</span>
                        </div>
                    </div>
                    <div className="flex items-center gap-4">
                        <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-xs font-mono text-muted-foreground">
                            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                            Live Mapping
                        </div>
                    </div>
                </div>
            </nav>

            {/* Main Content */}
            <main className="flex-1 relative overflow-hidden">
                {/* Alert Banner */}
                <div className="alert-banner absolute top-6 left-1/2 -translate-x-1/2 z-40">
                    <GlassCard className="px-6 py-3 flex items-center gap-3 border-yellow-500/20 bg-yellow-500/5 backdrop-blur-xl shadow-xl" hoverEffect={false}>
                        <AlertTriangle size={18} className="text-yellow-500" />
                        <span className="text-sm font-medium text-yellow-200">No circular dependencies detected</span>
                    </GlassCard>
                </div>

                {/* Graph Area */}
                <div className="graph-container w-full h-full bg-[#05050A]">
                    <ReactFlow
                        nodes={nodes}
                        edges={edges}
                        onNodesChange={onNodesChange}
                        onEdgesChange={onEdgesChange}
                        onConnect={onConnect}
                        fitView
                        className="bg-[#05050A]"
                        minZoom={0.5}
                        maxZoom={1.5}
                        defaultViewport={{ x: 0, y: 0, zoom: 1 }}
                    >
                        <Background color="#333" gap={20} size={1} />
                        <Controls className="bg-white/5 border border-white/10 text-white fill-white" />
                        <MiniMap
                            nodeStrokeColor={(n) => {
                                if (n.style?.background) return n.style.background as string;
                                return '#fff';
                            }}
                            nodeColor={(n) => {
                                if (n.style?.background) return n.style.background as string;
                                return '#fff';
                            }}
                            maskColor="rgba(0, 0, 0, 0.7)"
                            className="bg-black/40 border border-white/10 rounded-lg overflow-hidden"
                        />
                    </ReactFlow>
                </div>
            </main>
        </div>
    );
}
