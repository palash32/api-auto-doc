"use client";

import React, { useCallback, useRef, useState, useEffect, useMemo } from 'react';
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
    Node,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { useGSAP } from "@gsap/react";
import gsap from "gsap";
import { AlertTriangle, Terminal, ArrowLeft, GitBranch, RefreshCw, Loader2 } from "lucide-react";
import Link from "next/link";
import { MagneticButton } from "@/components/ui/magnetic-button";
import { GlassCard } from "@/components/ui/glass-card";
import { GsapRegistry } from "@/lib/gsap-registry";
import { api, Repository, EndpointSummary } from "@/lib/api";

// Color palette for different file paths
const FILE_COLORS = [
    '#3b82f6', // blue
    '#8b5cf6', // purple
    '#10b981', // green
    '#f59e0b', // amber
    '#ec4899', // pink
    '#06b6d4', // cyan
    '#ef4444', // red
    '#84cc16', // lime
];

interface FileGroup {
    filePath: string;
    endpoints: EndpointSummary[];
}

function generateGraphFromEndpoints(
    repositories: Repository[],
    endpointsByRepo: Map<string, EndpointSummary[]>
): { nodes: Node[]; edges: Edge[] } {
    const nodes: Node[] = [];
    const edges: Edge[] = [];

    // Central hub node
    nodes.push({
        id: 'hub',
        type: 'default',
        data: { label: 'API Gateway' },
        position: { x: 400, y: 300 },
        style: {
            background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
            color: '#fff',
            border: 'none',
            borderRadius: '50%',
            width: 100,
            height: 100,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '12px',
            fontWeight: 'bold',
            boxShadow: '0 0 40px rgba(59, 130, 246, 0.5)'
        }
    });

    // Create nodes for each repository
    const repoRadius = 200;
    const repoAngleStep = (2 * Math.PI) / Math.max(repositories.length, 1);

    repositories.forEach((repo, repoIdx) => {
        const repoAngle = repoIdx * repoAngleStep - Math.PI / 2;
        const repoX = 400 + repoRadius * Math.cos(repoAngle);
        const repoY = 300 + repoRadius * Math.sin(repoAngle);
        const repoColor = FILE_COLORS[repoIdx % FILE_COLORS.length];

        // Repository node
        nodes.push({
            id: `repo-${repo.id}`,
            data: { label: repo.name },
            position: { x: repoX - 60, y: repoY - 20 },
            style: {
                background: '#1e1e24',
                color: '#fff',
                border: `2px solid ${repoColor}`,
                borderRadius: '12px',
                padding: '8px 16px',
                minWidth: 120,
                fontSize: '11px',
                fontWeight: '500'
            }
        });

        // Connect hub to repo
        edges.push({
            id: `hub-to-${repo.id}`,
            source: 'hub',
            target: `repo-${repo.id}`,
            animated: true,
            style: { stroke: repoColor, strokeWidth: 2 }
        });

        // Group endpoints by file path
        const endpoints = endpointsByRepo.get(repo.id) || [];
        const fileGroups = new Map<string, EndpointSummary[]>();

        endpoints.forEach(ep => {
            // Extract just the filename from path
            const fileName = (ep as any).file_path?.split('/').pop() || 'unknown.ts';
            if (!fileGroups.has(fileName)) {
                fileGroups.set(fileName, []);
            }
            fileGroups.get(fileName)!.push(ep);
        });

        // Create file nodes around repository
        const fileRadius = 100;
        const files = Array.from(fileGroups.entries());
        const fileAngleStep = (2 * Math.PI) / Math.max(files.length, 1);

        files.forEach(([fileName, fileEndpoints], fileIdx) => {
            const fileAngle = repoAngle + fileAngleStep * fileIdx - Math.PI / 2;
            const fileX = repoX + fileRadius * Math.cos(fileAngle);
            const fileY = repoY + fileRadius * Math.sin(fileAngle);
            const fileColor = FILE_COLORS[(repoIdx + fileIdx + 1) % FILE_COLORS.length];

            // File node
            const fileNodeId = `file-${repo.id}-${fileIdx}`;
            nodes.push({
                id: fileNodeId,
                data: {
                    label: `${fileName}\n(${fileEndpoints.length} endpoints)`
                },
                position: { x: fileX - 50, y: fileY - 15 },
                style: {
                    background: '#0a0a0a',
                    color: fileColor,
                    border: `1px solid ${fileColor}40`,
                    borderRadius: '8px',
                    padding: '4px 10px',
                    fontSize: '9px',
                    whiteSpace: 'pre-line',
                    textAlign: 'center' as const
                }
            });

            // Connect repo to file
            edges.push({
                id: `${repo.id}-to-${fileNodeId}`,
                source: `repo-${repo.id}`,
                target: fileNodeId,
                style: { stroke: `${fileColor}60`, strokeWidth: 1 },
                markerEnd: { type: MarkerType.ArrowClosed, color: fileColor }
            });
        });
    });

    return { nodes, edges };
}

export default function DependencyGraphPage() {
    const [nodes, setNodes, onNodesChange] = useNodesState([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState([]);
    const [loading, setLoading] = useState(true);
    const [repositories, setRepositories] = useState<Repository[]>([]);
    const [circularDeps, setCircularDeps] = useState(0);
    const containerRef = useRef<HTMLDivElement>(null);

    const onConnect = useCallback(
        (params: Edge | Connection) => setEdges((eds) => addEdge(params, eds)),
        [setEdges],
    );

    const fetchData = async () => {
        setLoading(true);
        try {
            const repos = await api.getRepositories();
            setRepositories(repos);

            // Fetch endpoints for each repository
            const endpointsByRepo = new Map<string, EndpointSummary[]>();
            await Promise.all(
                repos.map(async (repo) => {
                    const result = await api.getRepositoryEndpoints(repo.id, { per_page: 100 });
                    endpointsByRepo.set(repo.id, result.endpoints);
                })
            );

            // Generate graph
            const { nodes: newNodes, edges: newEdges } = generateGraphFromEndpoints(repos, endpointsByRepo);
            setNodes(newNodes);
            setEdges(newEdges);

            // No circular deps detected (placeholder for future implementation)
            setCircularDeps(0);
        } catch (error) {
            console.error('Failed to fetch dependency data:', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, []);

    useGSAP(() => {
        if (!loading) {
            gsap.from(".graph-container", {
                scale: 0.95,
                opacity: 0,
                duration: 1,
                ease: "power3.out"
            });

            gsap.from(".alert-banner", {
                y: -50,
                opacity: 0,
                duration: 0.8,
                delay: 0.5,
                ease: "back.out(1.7)"
            });
        }
    }, { scope: containerRef, dependencies: [loading] });

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
                            <span>API Dependency Graph</span>
                        </div>
                    </div>
                    <div className="flex items-center gap-4">
                        <button
                            onClick={fetchData}
                            className="p-2 hover:bg-white/5 rounded-lg transition-colors"
                            disabled={loading}
                        >
                            <RefreshCw size={18} className={loading ? "animate-spin text-primary" : "text-muted-foreground"} />
                        </button>
                        <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-xs font-mono text-muted-foreground">
                            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                            {repositories.length} Repositories
                        </div>
                    </div>
                </div>
            </nav>

            {/* Main Content */}
            <main className="flex-1 relative overflow-hidden">
                {/* Alert Banner */}
                <div className="alert-banner absolute top-6 left-1/2 -translate-x-1/2 z-40">
                    <GlassCard
                        className={`px-6 py-3 flex items-center gap-3 backdrop-blur-xl shadow-xl ${circularDeps > 0
                                ? 'border-red-500/20 bg-red-500/5'
                                : 'border-emerald-500/20 bg-emerald-500/5'
                            }`}
                        hoverEffect={false}
                    >
                        {circularDeps > 0 ? (
                            <>
                                <AlertTriangle size={18} className="text-red-500" />
                                <span className="text-sm font-medium text-red-200">
                                    {circularDeps} circular dependencies detected
                                </span>
                            </>
                        ) : (
                            <>
                                <Terminal size={18} className="text-emerald-500" />
                                <span className="text-sm font-medium text-emerald-200">
                                    No circular dependencies detected
                                </span>
                            </>
                        )}
                    </GlassCard>
                </div>

                {/* Loading State */}
                {loading && (
                    <div className="absolute inset-0 flex items-center justify-center bg-[#05050A]/80 z-30">
                        <div className="flex flex-col items-center gap-4">
                            <Loader2 size={40} className="animate-spin text-primary" />
                            <p className="text-sm text-muted-foreground">Loading API dependencies...</p>
                        </div>
                    </div>
                )}

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
                        minZoom={0.3}
                        maxZoom={2}
                        defaultViewport={{ x: 0, y: 0, zoom: 0.8 }}
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

