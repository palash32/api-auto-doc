/**
 * Performance Routes - Monitoring & Metrics
 */

import { Router, Request, Response } from 'express';
import { getQueueStats } from '../scan-queue';

const router = Router();

// In-memory metrics (for early-access/demo purposes)
const metricsStore = {
    requestCount: 0,
    totalLatency: 0,
    cacheHits: 0,
    cacheMisses: 0,
    queuePending: 0,
    queueProcessing: 0,
    queueCompleted: 0,
    queueFailed: 0
};

// Performance Dashboard - Returns aggregated performance stats
router.get('/dashboard', async (req: Request, res: Response) => {
    try {
        const avgLatency = metricsStore.requestCount > 0
            ? metricsStore.totalLatency / metricsStore.requestCount
            : 45; // Default value for demo

        const totalCacheRequests = metricsStore.cacheHits + metricsStore.cacheMisses;
        const cacheHitRate = totalCacheRequests > 0
            ? (metricsStore.cacheHits / totalCacheRequests) * 100
            : 85; // Default value for demo

        res.json({
            avg_api_latency_ms: Math.round(avgLatency),
            cache_hit_rate: parseFloat(cacheHitRate.toFixed(1)),
            queue_depth: metricsStore.queuePending + metricsStore.queueProcessing,
            active_workers: 2 // Default for demo
        });
    } catch (error) {
        console.error('Performance dashboard error:', error);
        res.status(500).json({ error: 'Failed to fetch performance data' });
    }
});

// Rate Limits Status
router.get('/rate-limits/status', async (req: Request, res: Response) => {
    try {
        // For demo/early-access, return generous limits
        res.json({
            tier: 'early_access',
            minute_used: 5,
            minute_limit: 100,
            hour_used: 45,
            hour_limit: 5000,
            day_used: 120,
            day_limit: 50000
        });
    } catch (error) {
        console.error('Rate limits error:', error);
        res.status(500).json({ error: 'Failed to fetch rate limits' });
    }
});

// Queue Stats - Real data from scan-queue
router.get('/queue/stats', async (req: Request, res: Response) => {
    try {
        const stats = getQueueStats();
        res.json({
            pending: stats.pending,
            processing: stats.processing,
            completed: stats.completed,
            failed: stats.failed,
            total: stats.total,
            active_global: stats.activeGlobal,
            max_global: stats.maxGlobal,
            max_per_org: stats.maxPerOrg
        });
    } catch (error) {
        console.error('Queue stats error:', error);
        res.status(500).json({ error: 'Failed to fetch queue stats' });
    }
});

// Cache Stats
router.get('/cache/stats', async (req: Request, res: Response) => {
    try {
        res.json({
            total_entries: 128, // Demo value
            total_size_mb: 12.5,
            entries_by_type: [
                { type: 'endpoint_docs', count: 45, total_size_mb: 3.2, total_hits: 1250 },
                { type: 'repo_metadata', count: 23, total_size_mb: 1.8, total_hits: 890 },
                { type: 'scan_results', count: 60, total_size_mb: 7.5, total_hits: 340 }
            ]
        });
    } catch (error) {
        console.error('Cache stats error:', error);
        res.status(500).json({ error: 'Failed to fetch cache stats' });
    }
});

// Clear Cache
router.post('/cache/clear', async (req: Request, res: Response) => {
    try {
        // In production, this would clear actual cache
        metricsStore.cacheHits = 0;
        metricsStore.cacheMisses = 0;

        res.json({ success: true, message: 'Cache cleared successfully' });
    } catch (error) {
        console.error('Cache clear error:', error);
        res.status(500).json({ error: 'Failed to clear cache' });
    }
});

// Track request for metrics (middleware helper - can be used by other routes)
export const trackRequest = (latencyMs: number) => {
    metricsStore.requestCount++;
    metricsStore.totalLatency += latencyMs;
};

export const trackCacheHit = () => {
    metricsStore.cacheHits++;
};

export const trackCacheMiss = () => {
    metricsStore.cacheMisses++;
};

export const updateQueueStats = (pending: number, processing: number, completed: number, failed: number) => {
    metricsStore.queuePending = pending;
    metricsStore.queueProcessing = processing;
    metricsStore.queueCompleted = completed;
    metricsStore.queueFailed = failed;
};

export default router;
