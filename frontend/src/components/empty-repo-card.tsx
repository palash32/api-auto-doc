'use client';

import { Plus } from 'lucide-react';
import { GlassCard } from '@/components/ui/glass-card';
import { cn } from '@/lib/utils';

interface EmptyRepoCardProps {
    onClick: () => void;
    variant?: 'primary' | 'secondary';
    className?: string;
}

/**
 * Reusable empty repository card component
 * Use this throughout the app for consistent "add new" CTAs
 */
export function EmptyRepoCard({ onClick, variant = 'primary', className }: EmptyRepoCardProps) {
    const isPrimary = variant === 'primary';

    return (
        <GlassCard
            onClick={onClick}
            className={cn(
                "group flex items-center justify-between px-6 cursor-pointer transition-all duration-300",
                "border-dashed border-white/10 hover:border-primary/30 hover:bg-primary/5",
                "text-white/40 hover:text-white",
                "h-[180px] min-h-[180px] max-h-[180px]", // Consistent fixed height
                isPrimary && "border-2",
                className
            )}
            hoverEffect={false}
        >
            <p className="text-sm font-medium">Connect New Repository</p>
            <div className={cn(
                "w-12 h-12 rounded-full flex items-center justify-center transition-all duration-300",
                "bg-white/5 group-hover:scale-110 group-hover:bg-primary/10 group-hover:text-primary"
            )}>
                <Plus size={24} />
            </div>
        </GlassCard>
    );
}
