'use client';

import { useState } from 'react';
import { X, Github, Loader2, CheckCircle2, AlertCircle } from 'lucide-react';
import { MagneticButton } from '@/components/ui/magnetic-button';
import { GlassCard } from '@/components/ui/glass-card';
import { api } from '@/lib/api';

interface AddRepositoryModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSuccess: () => void;
}

export function AddRepositoryModal({ isOpen, onClose, onSuccess }: AddRepositoryModalProps) {
    const [url, setUrl] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [loadingStatus, setLoadingStatus] = useState('');

    if (!isOpen) return null;

    // Validate GitHub URL
    const isValidGitHubUrl = (url: string) => {
        const githubPattern = /^https?:\/\/(www\.)?github\.com\/[\w-]+\/[\w.-]+/;
        return githubPattern.test(url);
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');

        // Frontend validation
        if (!url.trim()) {
            setError('Please enter a repository URL');
            return;
        }

        if (!isValidGitHubUrl(url)) {
            setError('Please enter a valid GitHub repository URL (e.g., https://github.com/owner/repo)');
            return;
        }

        setLoading(true);

        try {
            // Step 1: Validating
            setLoadingStatus('Validating URL...');
            await new Promise(resolve => setTimeout(resolve, 300));

            // Step 2: Fetching from GitHub
            setLoadingStatus('Fetching repository info from GitHub...');

            const result = await api.addRepository(url);

            if (result) {
                // Step 3: Success!
                setLoadingStatus('Repository added successfully! ✨');
                await new Promise(resolve => setTimeout(resolve, 500));

                onSuccess();
                onClose();
                setUrl('');
                setLoadingStatus('');
            }
        } catch (err: unknown) {
            setLoading(false);
            setLoadingStatus('');

            // User-friendly error messages
            const errorMessage = (err instanceof Error ? err.message : String(err)) || '';

            if (errorMessage.includes('404') || errorMessage.includes('not fetch')) {
                setError('Repository not found. Please check the URL and make sure the repository is public.');
            } else if (errorMessage.includes('Invalid GitHub URL')) {
                setError('Invalid URL format. Please use: https://github.com/owner/repository');
            } else if (errorMessage.includes('network') || errorMessage.includes('fetch')) {
                setError('Network error. Please check your internet connection and try again.');
            } else {
                setError(errorMessage || 'Failed to add repository. Please try again.');
            }
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
            <GlassCard className="w-full max-w-md p-6 relative animate-in fade-in zoom-in duration-300">
                <button
                    onClick={() => {
                        if (!loading) {
                            onClose();
                            setUrl('');
                            setError('');
                            setLoadingStatus('');
                        }
                    }}
                    disabled={loading}
                    className="absolute top-4 right-4 text-white/40 hover:text-white transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                >
                    <X size={20} />
                </button>

                <div className="flex items-center gap-3 mb-6">
                    <div className="p-3 rounded-full bg-white/5 text-white">
                        <Github size={24} />
                    </div>
                    <div>
                        <h2 className="text-xl font-bold text-white">Add Repository</h2>
                        <p className="text-sm text-white/40">Connect a GitHub repository to auto-discover APIs</p>
                    </div>
                </div>

                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-white/60 mb-1">
                            Repository URL
                        </label>
                        <input
                            type="url"
                            value={url}
                            onChange={(e) => {
                                setUrl(e.target.value);
                                setError(''); // Clear error on input
                            }}
                            placeholder="https://github.com/owner/repository"
                            className="w-full px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-white placeholder-white/20 focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/30 transition-all"
                            required
                            disabled={loading}
                        />
                        <p className="text-xs text-white/30 mt-1">We'll automatically detect the language and fetch repository details</p>
                    </div>

                    {/* Loading Status */}
                    {loading && loadingStatus && (
                        <div className="flex items-center gap-2 text-sm text-primary bg-primary/10 p-3 rounded-lg border border-primary/20">
                            <Loader2 size={16} className="animate-spin" />
                            <span>{loadingStatus}</span>
                        </div>
                    )}

                    {/* Error Message */}
                    {error && (
                        <div className="flex items-start gap-2 text-sm text-red-400 bg-red-400/10 p-3 rounded-lg border border-red-400/20">
                            <AlertCircle size={16} className="flex-shrink-0 mt-0.5" />
                            <span>{error}</span>
                        </div>
                    )}

                    <div className="flex justify-end gap-3 mt-6">
                        <button
                            type="button"
                            onClick={() => {
                                onClose();
                                setUrl('');
                                setError('');
                                setLoadingStatus('');
                            }}
                            disabled={loading}
                            className="px-4 py-2 text-sm text-white/60 hover:text-white transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                        >
                            Cancel
                        </button>
                        <MagneticButton
                            type="submit"
                            disabled={loading || !url.trim()}
                            className="bg-primary hover:bg-primary/90 text-black px-6 py-2 rounded-full font-medium flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                        >
                            {loading ? (
                                <>
                                    <Loader2 size={16} className="animate-spin" />
                                    Adding...
                                </>
                            ) : (
                                <>
                                    <Github size={16} />
                                    Add Repository
                                </>
                            )}
                        </MagneticButton>
                    </div>
                </form>
            </GlassCard>
        </div>
    );
}
