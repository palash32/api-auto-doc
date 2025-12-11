"use client";

import React from "react";
import { AlertTriangle, RefreshCcw } from "lucide-react";
import { Button } from "@/components/ui/button";

interface ErrorBoundaryProps {
    children: React.ReactNode;
}

interface ErrorBoundaryState {
    hasError: boolean;
    error?: Error;
}

export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
    constructor(props: ErrorBoundaryProps) {
        super(props);
        this.state = { hasError: false };
    }

    static getDerivedStateFromError(error: Error) {
        return { hasError: true, error };
    }

    componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
        console.error("Uncaught error:", error, errorInfo);
    }

    render() {
        if (this.state.hasError) {
            return (
                <div className="flex flex-col items-center justify-center min-h-[400px] p-6 text-center bg-red-500/5 rounded-xl border border-red-500/10">
                    <div className="w-12 h-12 rounded-full bg-red-500/10 flex items-center justify-center mb-4 text-red-400">
                        <AlertTriangle size={24} />
                    </div>
                    <h2 className="text-xl font-semibold mb-2 text-white">Something went wrong</h2>
                    <p className="text-muted-foreground mb-6 max-w-md">
                        We encountered an unexpected error. Our team has been notified.
                    </p>
                    <Button
                        onClick={() => this.setState({ hasError: false })}
                        variant="outline"
                        className="gap-2"
                    >
                        <RefreshCcw size={16} />
                        Try Again
                    </Button>
                </div>
            );
        }

        return this.props.children;
    }
}
