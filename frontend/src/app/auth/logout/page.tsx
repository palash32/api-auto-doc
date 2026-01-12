"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";

/**
 * Logout page - clears all auth tokens and redirects to home
 * Navigate to /auth/logout to log out
 */
export default function LogoutPage() {
    const router = useRouter();

    useEffect(() => {
        // Clear all auth tokens and session data
        clearAllAuthData();

        // Redirect to home after cleanup
        setTimeout(() => {
            router.push("/");
        }, 500);
    }, [router]);

    return (
        <div className="min-h-screen flex flex-col items-center justify-center bg-black text-white">
            <div className="flex flex-col items-center gap-4">
                <Loader2 className="h-10 w-10 animate-spin text-purple-500" />
                <p className="text-gray-400">Logging out...</p>
            </div>
        </div>
    );
}

/**
 * Utility function to clear all auth data
 * Can be imported and used elsewhere
 */
export function clearAllAuthData() {
    // Clear localStorage
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    localStorage.removeItem("github_token");

    // Clear sessionStorage
    sessionStorage.clear();

    // Clear all auth cookies
    const cookies = document.cookie.split(";");
    cookies.forEach(cookie => {
        const eqPos = cookie.indexOf("=");
        const name = eqPos > -1 ? cookie.substring(0, eqPos).trim() : cookie.trim();
        // Clear cookie by setting expiry to past
        document.cookie = `${name}=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT; SameSite=Lax`;
        document.cookie = `${name}=; path=/; domain=${window.location.hostname}; expires=Thu, 01 Jan 1970 00:00:00 GMT; SameSite=Lax`;
    });

    // Also try to clear next-auth session cookie if present
    document.cookie = "next-auth.session-token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";
    document.cookie = "__Secure-next-auth.session-token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT; Secure";
}
