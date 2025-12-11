import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "@/components/providers";
import { ToastProvider } from "@/components/toast-provider";
import { ErrorBoundary } from "@/components/error-boundary";
import { FeedbackButton } from "@/components/feedback-button";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
    title: "API Auto-Documentation Platform",
    description: "Automatically discover, document, and monitor all APIs across your organization's codebase",
    keywords: ["API", "documentation", "monitoring", "developer tools"],
    authors: [{ name: "API Auto-Documentation Platform" }],
};

export const viewport: Viewport = {
    width: "device-width",
    initialScale: 1,
    themeColor: [
        { media: "(prefers-color-scheme: light)", color: "#ffffff" },
        { media: "(prefers-color-scheme: dark)", color: "#0a0a0a" },
    ],
};

export default function RootLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <html lang="en" suppressHydrationWarning>
            <body className={inter.className}>
                <ErrorBoundary>
                    <ToastProvider>
                        <Providers>
                            {children}
                            <FeedbackButton />
                        </Providers>
                    </ToastProvider>
                </ErrorBoundary>
            </body>
        </html>
    );
}
