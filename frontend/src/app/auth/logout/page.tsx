"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Loader2, LogOut, RefreshCw } from "lucide-react";
import { API_BASE_URL } from "@/lib/api";
import { clearAllAuthData } from "@/lib/auth-utils";

/**
 * Logout page - clears all auth tokens and provides options
 * Navigate to /auth/logout to log out
 */
export default function LogoutPage() {
    const router = useRouter();
    const [cleared, setCleared] = useState(false);

    useEffect(() => {
        // Clear all auth tokens and session data
        clearAllAuthData();
        setCleared(true);
    }, []);

    const handleGoHome = () => {
        router.push("/");
    };

    const handleSwitchAccount = () => {
        // Use fresh login to force GitHub re-authentication
        window.location.href = `${API_BASE_URL}/api/auth/github/login?fresh=true`;
    };

    if (!cleared) {
        return (
            <div className="min-h-screen flex flex-col items-center justify-center bg-black text-white">
                <div className="flex flex-col items-center gap-4">
                    <Loader2 className="h-10 w-10 animate-spin text-purple-500" />
                    <p className="text-gray-400">Logging out...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen flex flex-col items-center justify-center bg-black text-white">
            <div className="flex flex-col items-center gap-6 max-w-md text-center px-4">
                <div className="w-16 h-16 rounded-full bg-green-500/20 flex items-center justify-center">
                    <LogOut className="h-8 w-8 text-green-400" />
                </div>
                <h1 className="text-2xl font-bold">You&apos;ve been logged out</h1>
                <p className="text-gray-400">
                    Your session has been cleared from this app.
                </p>

                <div className="flex flex-col gap-3 w-full mt-4">
                    <button
                        onClick={handleGoHome}
                        className="w-full px-6 py-3 bg-white/10 hover:bg-white/20 text-white rounded-xl font-medium transition-colors"
                    >
                        Go to Home
                    </button>

                    <button
                        onClick={handleSwitchAccount}
                        className="w-full px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-xl font-medium transition-colors flex items-center justify-center gap-2"
                    >
                        <RefreshCw size={18} />
                        Login with Different GitHub Account
                    </button>
                </div>

                <p className="text-xs text-gray-500 mt-4">
                    Note: If GitHub still shows the same account, you may need to
                    <a href="https://github.com/logout" target="_blank" rel="noopener noreferrer" className="text-purple-400 hover:underline ml-1">
                        log out from GitHub.com
                    </a> first.
                </p>
            </div>
        </div>
    );
}
