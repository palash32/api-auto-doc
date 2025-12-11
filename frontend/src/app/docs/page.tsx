"use client";

import Link from "next/link";
import { ArrowLeft, BookOpen, Construction } from "lucide-react";
import { GlassCard } from "@/components/ui/glass-card";
import { MagneticButton } from "@/components/ui/magnetic-button";

export default function DocsPage() {
    return (
        <div className="min-h-screen bg-background flex items-center justify-center p-6">
            <GlassCard className="max-w-2xl w-full p-12 text-center">
                <div className="flex justify-center mb-6">
                    <div className="relative">
                        <div className="w-20 h-20 rounded-full bg-blue-500/10 flex items-center justify-center">
                            <Construction className="w-10 h-10 text-blue-400" />
                        </div>
                        <div className="absolute -top-2 -right-2 w-8 h-8 rounded-full bg-yellow-500/20 flex items-center justify-center border border-yellow-500/30">
                            <BookOpen className="w-4 h-4 text-yellow-400" />
                        </div>
                    </div>
                </div>

                <h1 className="text-3xl font-bold mb-4 bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                    Documentation Coming Soon
                </h1>
                <p className="text-muted-foreground mb-8 max-w-md mx-auto">
                    We're crafting comprehensive guides, API references, and tutorials.
                    In the meantime, explore the platform to see how it works.
                </p>

                <div className="flex flex-col sm:flex-row gap-4 justify-center">
                    <Link href="/dashboard">
                        <MagneticButton className="gap-2">
                            <BookOpen className="w-4 h-4" />
                            Try the Platform
                        </MagneticButton>
                    </Link>
                    <Link href="/">
                        <MagneticButton variant="secondary" className="gap-2">
                            <ArrowLeft className="w-4 h-4" />
                            Back to Home
                        </MagneticButton>
                    </Link>
                </div>
            </GlassCard>
        </div>
    );
}
