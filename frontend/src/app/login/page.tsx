"use client";

import { useEffect } from "react";
import { Loader2 } from "lucide-react";

export default function LoginPage() {
    useEffect(() => {
        // Redirect to backend GitHub OAuth endpoint
        const API_URL = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/$/, '');
        window.location.href = `${API_URL}/api/auth/github/login`;
    }, []);

    return (
        <div className="min-h-screen flex flex-col items-center justify-center bg-black text-white">
            <div className="flex flex-col items-center gap-4">
                <Loader2 className="h-10 w-10 animate-spin text-blue-500" />
                <p className="text-muted-foreground">Redirecting to GitHub...</p>
            </div>
        </div>
    );
}
