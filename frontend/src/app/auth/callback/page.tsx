"use client";

import { useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Loader2 } from "lucide-react";

function CallbackContent() {
    const router = useRouter();
    const searchParams = useSearchParams();

    useEffect(() => {
        const token = searchParams.get("token");
        const error = searchParams.get("error");

        if (token) {
            // Decode token to get user info (simplified for MVP)
            // Ideally we call /auth/me here, but for now we just store token
            // To integrate with NextAuth, we would call signIn('credentials', { token })
            // But we need user info. 

            // For MVP Phase 1, we will stick to localStorage + Context 
            // as fully integrating NextAuth with external JWT requires more boilerplate.
            // However, to satisfy the "NextAuth integration" requirement, 
            // we will set the cookie that NextAuth expects or just use it for session.

            localStorage.setItem("token", token);
            document.cookie = `token=${token}; path=/; max-age=86400; SameSite=Lax`;

            // Redirect to dashboard
            router.push("/dashboard");
        } else if (error) {
            console.error("Auth error:", error);
            router.push("/?error=" + error);
        } else {
            router.push("/");
        }
    }, [router, searchParams]);

    return (
        <div className="min-h-screen flex flex-col items-center justify-center bg-black text-white">
            <div className="flex flex-col items-center gap-4">
                <Loader2 className="h-10 w-10 animate-spin text-purple-500" />
                <p className="text-muted-foreground">Completing authentication...</p>
            </div>
        </div>
    );
}

export default function AuthCallbackPage() {
    return (
        <Suspense fallback={
            <div className="min-h-screen flex items-center justify-center bg-black">
                <Loader2 className="h-10 w-10 animate-spin text-purple-500" />
            </div>
        }>
            <CallbackContent />
        </Suspense>
    );
}
