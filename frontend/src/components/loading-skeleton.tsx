export function LoadingSkeleton({ className }: { className?: string }) {
    return (
        <div className={`animate-pulse ${className}`}>
            <div className="h-4 bg-gray-800 rounded w-3/4 mb-3"></div>
            <div className="h-4 bg-gray-800 rounded w-1/2"></div>
        </div>
    );
}

export function TableLoadingSkeleton({ rows = 5 }: { rows?: number }) {
    return (
        <div className="space-y-3">
            {Array.from({ length: rows }).map((_, i) => (
                <div key={i} className="bg-gray-900/50 border border-gray-800 rounded-lg p-6 animate-pulse">
                    <div className="flex items-center gap-4">
                        <div className="h-6 w-16 bg-gray-800 rounded"></div>
                        <div className="h-6 flex-1 bg-gray-800 rounded"></div>
                    </div>
                    <div className="mt-3 h-4 w-2/3 bg-gray-800 rounded"></div>
                </div>
            ))}
        </div>
    );
}

export function CardLoadingSkeleton() {
    return (
        <div className="bg-gray-900/50 border border-gray-800 rounded-lg p-6 animate-pulse">
            <div className="h-6 bg-gray-800 rounded w-1/3 mb-4"></div>
            <div className="space-y-3">
                <div className="h-4 bg-gray-800 rounded w-full"></div>
                <div className="h-4 bg-gray-800 rounded w-5/6"></div>
                <div className="h-4 bg-gray-800 rounded w-4/6"></div>
            </div>
        </div>
    );
}
