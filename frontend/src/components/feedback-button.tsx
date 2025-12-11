"use client";

import { useState } from "react";
import { MessageSquarePlus, X, Send, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { GlassCard } from "@/components/ui/glass-card";
import { useToast } from "@/components/toast-provider";
import { sendFeedback } from "@/lib/emailjs";
import { cn } from "@/lib/utils";
import { AnimatePresence, motion } from "framer-motion";

export function FeedbackButton() {
    const [isOpen, setIsOpen] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [message, setMessage] = useState("");
    const [type, setType] = useState<"bug" | "feature" | "other">("bug");
    const { success, error } = useToast();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!message.trim()) return;

        setIsLoading(true);
        try {
            await sendFeedback({ message, type });
            success("Feedback sent! Thank you for helping us improve.");
            setIsOpen(false);
            setMessage("");
            setType("bug");
        } catch (err) {
            error("Failed to send feedback. Please try again.");
            console.error(err);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <>
            <AnimatePresence>
                {isOpen && (
                    <motion.div
                        initial={{ opacity: 0, scale: 0.9, y: 20 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.9, y: 20 }}
                        className="fixed bottom-24 right-6 z-50 w-[350px]"
                    >
                        <GlassCard className="p-0 overflow-hidden border-white/10 shadow-2xl">
                            <div className="bg-white/5 p-4 border-b border-white/10 flex justify-between items-center">
                                <h3 className="font-semibold text-white">Send Feedback</h3>
                                <Button
                                    variant="ghost"
                                    size="icon"
                                    className="h-8 w-8 hover:bg-white/10"
                                    onClick={() => setIsOpen(false)}
                                >
                                    <X className="h-4 w-4" />
                                </Button>
                            </div>

                            <form onSubmit={handleSubmit} className="p-4 space-y-4">
                                <div className="space-y-2">
                                    <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Type</label>
                                    <div className="flex gap-2">
                                        {(["bug", "feature", "other"] as const).map((t) => (
                                            <button
                                                key={t}
                                                type="button"
                                                onClick={() => setType(t)}
                                                className={cn(
                                                    "flex-1 px-3 py-2 rounded-lg text-xs font-medium transition-all border",
                                                    type === t
                                                        ? "bg-purple-500/20 border-purple-500/50 text-purple-200"
                                                        : "bg-white/5 border-white/10 text-muted-foreground hover:bg-white/10"
                                                )}
                                            >
                                                {t.charAt(0).toUpperCase() + t.slice(1)}
                                            </button>
                                        ))}
                                    </div>
                                </div>

                                <div className="space-y-2">
                                    <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Message</label>
                                    <textarea
                                        value={message}
                                        onChange={(e) => setMessage(e.target.value)}
                                        placeholder="Tell us what's wrong or what you'd like to see..."
                                        className="w-full h-32 bg-black/20 border border-white/10 rounded-lg p-3 text-sm text-white placeholder:text-white/20 focus:outline-none focus:ring-1 focus:ring-purple-500/50 resize-none"
                                        required
                                    />
                                </div>

                                <Button
                                    type="submit"
                                    disabled={isLoading}
                                    className="w-full bg-purple-600 hover:bg-purple-700 text-white"
                                >
                                    {isLoading ? (
                                        <Loader2 className="h-4 w-4 animate-spin mr-2" />
                                    ) : (
                                        <Send className="h-4 w-4 mr-2" />
                                    )}
                                    Send Feedback
                                </Button>
                            </form>
                        </GlassCard>
                    </motion.div>
                )}
            </AnimatePresence>

            <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => setIsOpen(!isOpen)}
                className={cn(
                    "fixed bottom-6 right-6 z-50 h-14 w-14 rounded-full shadow-lg flex items-center justify-center transition-colors",
                    isOpen
                        ? "bg-muted text-muted-foreground hover:bg-muted/80"
                        : "bg-purple-600 text-white hover:bg-purple-700 shadow-purple-900/20"
                )}
            >
                {isOpen ? <X className="h-6 w-6" /> : <MessageSquarePlus className="h-6 w-6" />}
            </motion.button>
        </>
    );
}
