import { FolderGit2, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { GlassCard } from "@/components/ui/glass-card";

interface EmptyStateProps {
    title?: string;
    description?: string;
    actionLabel?: string;
    onAction?: () => void;
}

export function EmptyState({
    title = "Your Dashboard is Empty",
    description = "Let's fix that. Connect a repository to see the magic happen.",
    actionLabel = "Scan First Repo",
    onAction,
}: EmptyStateProps) {
    return (
        <GlassCard className="flex flex-col items-center justify-center p-12 text-center border-dashed border-2 border-white/10 bg-black/20">
            <div className="rounded-full bg-purple-500/10 p-6 mb-6 ring-1 ring-purple-500/20">
                <FolderGit2 className="h-12 w-12 text-purple-400" />
            </div>

            <h3 className="text-xl font-semibold text-white mb-2">{title}</h3>
            <p className="text-muted-foreground max-w-sm mb-8">
                {description}
            </p>

            <Button
                onClick={onAction}
                className="bg-purple-600 hover:bg-purple-700 text-white font-medium px-8 py-6 h-auto rounded-xl shadow-lg shadow-purple-900/20 transition-all hover:scale-105"
            >
                <Plus className="mr-2 h-5 w-5" />
                {actionLabel}
            </Button>
        </GlassCard>
    );
}
