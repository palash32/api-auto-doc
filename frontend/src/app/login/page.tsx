"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";

export default function LoginPage() {
    const router = useRouter();

    useEffect(() => {
        // Redirect to new auth sign-in page
        router.replace('/auth/signin');
    }, [router]);

    return (
        <div className="min-h-screen flex flex-col items-center justify-center bg-black text-white">
            <div className="flex flex-col items-center gap-4">
                <Loader2 className="h-10 w-10 animate-spin text-purple-500" />
                <p className="text-muted-foreground">Redirecting to sign in...</p>
            </div>
        </div>
    );
}
