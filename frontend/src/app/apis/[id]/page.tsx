'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { Loader2, ArrowLeft, Sparkles } from 'lucide-react';
import Link from 'next/link';
import { api, EndpointDetail } from '@/lib/api';
import SwaggerViewer from '@/components/swagger-ui';
import { MagneticButton } from '@/components/ui/magnetic-button';

export default function ApiDocPage() {
    const params = useParams();
    const [endpoint, setEndpoint] = useState<EndpointDetail | null>(null);
    const [loading, setLoading] = useState(true);
    const [generating, setGenerating] = useState(false);

    useEffect(() => {
        const fetchEndpoint = async () => {
            if (params.id) {
                const data = await api.getEndpointDetail(params.id as string);
                setEndpoint(data);
                setLoading(false);
            }
        };
        fetchEndpoint();
    }, [params.id]);

    // const handleGenerate = async () => {
    //     if (!endpoint) return;
    //     setGenerating(true);
    //     const updated = await api.generateDocs(endpoint.id);
    //     if (updated) {
    //         setEndpoint(updated);
    //     }
    //     setGenerating(false);
    // };

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-background">
                <Loader2 className="animate-spin text-primary" size={32} />
            </div>
        );
    }

    if (!endpoint) {
        return (
            <div className="min-h-screen flex flex-col items-center justify-center bg-background text-white">
                <h1 className="text-2xl font-bold mb-4">Endpoint not found</h1>
                <Link href="/apis" className="text-primary hover:underline">
                    Back to API List
                </Link>
            </div>
        );
    }

    // Construct a minimal OpenAPI spec for this endpoint
    const spec = {
        openapi: '3.0.0',
        info: {
            title: endpoint.summary || 'API Documentation',
            version: '1.0.0',
        },
        paths: {
            [endpoint.path]: {
                [endpoint.method.toLowerCase()]: {
                    summary: endpoint.summary,
                    description: endpoint.description,
                    parameters: endpoint.parameters,
                    responses: endpoint.responses,
                },
            },
        },
    };

    return (
        <div className="min-h-screen bg-background pt-24 pb-12 px-4">
            <div className="max-w-7xl mx-auto">
                <div className="flex items-center justify-between mb-8">
                    <Link
                        href="/apis"
                        className="flex items-center text-white/60 hover:text-white transition-colors"
                    >
                        <ArrowLeft size={20} className="mr-2" />
                        Back to APIs
                    </Link>


                    {/* <MagneticButton
                        onClick={handleGenerate}
                        disabled={generating}
                        className="bg-gradient-to-r from-purple-600 to-blue-600 text-white px-6 py-2 rounded-full font-medium flex items-center gap-2 disabled:opacity-50"
                    >
                        {generating ? (
                            <Loader2 size={18} className="animate-spin" />
                        ) : (
                            <Sparkles size={18} />
                        )}
                        {generating ? 'Generating AI Docs...' : 'Regenerate with AI'}
                    </MagneticButton> */}
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    {/* Metadata Card */}
                    <div className="lg:col-span-1 space-y-6">
                        <div className="p-6 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-xl">
                            <h2 className="text-xl font-bold text-white mb-4">Metadata</h2>
                            <div className="space-y-4">
                                <div>
                                    <label className="text-xs text-white/40 uppercase font-semibold">Path</label>
                                    <p className="text-white font-mono text-sm bg-black/30 p-2 rounded mt-1">
                                        {endpoint.method} {endpoint.path}
                                    </p>
                                </div>
                                <div>
                                    <label className="text-xs text-white/40 uppercase font-semibold">File Path</label>
                                    <p className="text-white/80 text-sm mt-1 font-mono text-xs">{endpoint.file_path}</p>
                                </div>
                                {endpoint.auth_required && (
                                    <div>
                                        <label className="text-xs text-white/40 uppercase font-semibold">Authentication</label>
                                        <p className="text-white/80 text-sm mt-1">{endpoint.auth_type || 'Required'}</p>
                                    </div>
                                )}
                                {endpoint.tags && endpoint.tags.length > 0 && (
                                    <div>
                                        <label className="text-xs text-white/40 uppercase font-semibold">Tags</label>
                                        <div className="flex flex-wrap gap-2 mt-2">
                                            {endpoint.tags.map((tag, i) => (
                                                <span key={i} className="px-2 py-1 text-xs bg-blue-500/20 text-blue-300 rounded">
                                                    {tag}
                                                </span>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* Swagger UI */}
                    <div className="lg:col-span-2">
                        <SwaggerViewer spec={spec} />
                    </div>
                </div>
            </div>
        </div>
    );
}
