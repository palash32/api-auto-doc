/**
 * Health Routes - Dashboard and Alerts
 */

import { Router, Request, Response } from 'express';
import { RepoStore, EndpointStore } from '../store';

const router = Router();

// Basic health check
router.get('/', (req: Request, res: Response) => {
    res.json({
        status: 'healthy',
        version: '2.0.0',
        timestamp: new Date().toISOString(),
        uptime: process.uptime()
    });
});

router.get('/ready', (req: Request, res: Response) => {
    res.json({ ready: true });
});

router.get('/live', (req: Request, res: Response) => {
    res.json({ live: true });
});

// Health Dashboard - Returns aggregated health metrics
router.get('/dashboard', async (req: Request, res: Response) => {
    try {
        // Get all endpoints to calculate health metrics
        const orgId = (req as any).user?.organization_id || 'default';
        const repositories = await RepoStore.findByOrg(orgId);

        let totalEndpoints = 0;
        let healthyCount = 0;
        let degradedCount = 0;
        let unhealthyCount = 0;
        let unknownCount = 0;

        for (const repo of repositories) {
            const endpoints = await EndpointStore.findByRepo(repo.id);
            totalEndpoints += endpoints.length;

            // For now, consider all scanned endpoints as "healthy"
            // In a production system, you'd have actual health checks
            if (repo.scanStatus === 'completed') {
                healthyCount += endpoints.length;
            } else if (repo.scanStatus === 'scanning' || repo.scanStatus === 'pending') {
                unknownCount += endpoints.length;
            } else if (repo.scanStatus === 'failed') {
                unhealthyCount += endpoints.length;
            }
        }

        // Calculate average latency (mock data for now)
        const avgLatency = repositories.length > 0 ? 42 : null;

        res.json({
            total_endpoints: totalEndpoints,
            status_breakdown: {
                healthy: healthyCount,
                degraded: degradedCount,
                unhealthy: unhealthyCount,
                unknown: unknownCount
            },
            avg_uptime_24h: 99.9,
            avg_latency_ms: avgLatency,
            open_alerts: unhealthyCount > 0 ? 1 : 0
        });
    } catch (error) {
        console.error('Health dashboard error:', error);
        res.status(500).json({ error: 'Failed to fetch health data' });
    }
});

// Health Alerts - Returns recent alerts
router.get('/alerts', async (req: Request, res: Response) => {
    try {
        const resolved = req.query.resolved === 'true';
        const limit = parseInt(req.query.limit as string) || 10;

        // For now, return empty alerts (no alerts = all systems healthy)
        // In production, query from alerts table
        const alerts: any[] = [];

        res.json(alerts);
    } catch (error) {
        console.error('Health alerts error:', error);
        res.status(500).json({ error: 'Failed to fetch alerts' });
    }
});

// Run a quick health check on an external URL
router.post('/check', async (req: Request, res: Response) => {
    try {
        const { url, method = 'GET' } = req.body;

        if (!url) {
            return res.status(400).json({ error: 'URL is required' });
        }

        const startTime = Date.now();

        try {
            const response = await fetch(url, {
                method,
                signal: AbortSignal.timeout(10000) // 10s timeout
            });

            const latency = Date.now() - startTime;

            res.json({
                status: response.ok ? 'healthy' : (response.status >= 500 ? 'unhealthy' : 'degraded'),
                status_code: response.status,
                latency_ms: latency,
                error_message: null
            });
        } catch (fetchError: any) {
            const latency = Date.now() - startTime;
            res.json({
                status: 'unhealthy',
                status_code: null,
                latency_ms: latency,
                error_message: fetchError.message || 'Connection failed'
            });
        }
    } catch (error) {
        console.error('Health check error:', error);
        res.status(500).json({ error: 'Failed to run health check' });
    }
});

// Resolve an alert
router.post('/alerts/:alertId/resolve', async (req: Request, res: Response) => {
    try {
        const { alertId } = req.params;
        // In production, update alert in database
        res.json({ success: true, message: `Alert ${alertId} resolved` });
    } catch (error) {
        console.error('Resolve alert error:', error);
        res.status(500).json({ error: 'Failed to resolve alert' });
    }
});

export default router;
