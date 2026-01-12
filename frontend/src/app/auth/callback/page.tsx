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
            // Clear any existing tokens first to prevent session crossover
            localStorage.removeItem("token");
            document.cookie = "token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT; SameSite=Lax";

            // Also clear any other auth-related items
            localStorage.removeItem("user");
            sessionStorage.clear();

            // Now set the new token
            localStorage.setItem("token", token);
            document.cookie = `token=${token}; path=/; max-age=604800; SameSite=Lax; Secure`;

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
