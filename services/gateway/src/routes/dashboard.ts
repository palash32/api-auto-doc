/**
 * Dashboard Routes
 * 
 * Provides real-time aggregated metrics and activity feed for the dashboard.
 */

import { Router, Request, Response } from 'express';
import { authenticateToken, AuthenticatedRequest } from '../middleware/auth';
import { ActivityStore, RepoStore } from '../store';
import { isUsingDatabase, query } from '../db';

const router = Router();

// =============================================================================
// GET DASHBOARD STATS - Aggregated metrics
// =============================================================================

router.get('/stats', authenticateToken, async (req: Request, res: Response) => {
    try {
        const authReq = req as AuthenticatedRequest;
        const orgId = authReq.user?.organization_id;

        if (!orgId) {
            return res.status(401).json({ error: 'Organization not found' });
        }

        let stats;

        if (isUsingDatabase()) {
            // Aggregate stats from database
            const result = await query<any>(`
                SELECT 
                    COUNT(*) as total_repositories,
                    COALESCE(SUM(api_count), 0) as total_endpoints,
                    COALESCE(AVG(health_score), 0) as avg_health_score,
                    MAX(last_scanned) as last_scan_time,
                    COUNT(CASE WHEN status = 'scanning' THEN 1 END) as scanning_count
                FROM repositories
                WHERE organization_id = $1
            `, [orgId]);

            const row = result[0] || {};
            stats = {
                totalRepositories: parseInt(row.total_repositories) || 0,
                totalEndpoints: parseInt(row.total_endpoints) || 0,
                avgHealthScore: Math.round(parseFloat(row.avg_health_score) || 0),
                lastScanTime: row.last_scan_time ? new Date(row.last_scan_time).toISOString() : null,
                scanningCount: parseInt(row.scanning_count) || 0
            };
        } else {
            // In-memory fallback
            const repos = await RepoStore.findByOrg(orgId);
            const totalEndpoints = repos.reduce((sum, r) => sum + r.apiCount, 0);
            const avgHealth = repos.length > 0
                ? Math.round(repos.reduce((sum, r) => sum + (r.apiCount > 0 ? 100 : 0), 0) / repos.length)
                : 0;
            const lastScan = repos
                .filter(r => r.lastScanned)
                .sort((a, b) => (b.lastScanned?.getTime() || 0) - (a.lastScanned?.getTime() || 0))[0];

            stats = {
                totalRepositories: repos.length,
                totalEndpoints,
                avgHealthScore: avgHealth,
                lastScanTime: lastScan?.lastScanned?.toISOString() || null,
                scanningCount: repos.filter(r => r.scanStatus === 'scanning').length
            };
        }

        res.json(stats);
    } catch (error) {
        console.error('Dashboard stats error:', error);
        res.status(500).json({ error: 'Failed to get dashboard stats' });
    }
});

// =============================================================================
// GET RECENT ACTIVITY - Activity feed
// =============================================================================

router.get('/activity', authenticateToken, async (req: Request, res: Response) => {
    try {
        const authReq = req as AuthenticatedRequest;
        const orgId = authReq.user?.organization_id;
        const limit = parseInt(req.query.limit as string) || 10;

        if (!orgId) {
            return res.status(401).json({ error: 'Organization not found' });
        }

        const activities = await ActivityStore.findByOrg(orgId, limit);

        // Transform to API response format
        const response = activities.map(a => ({
            id: a.id,
            type: a.type,
            title: a.title,
            description: a.description,
            repositoryId: a.repositoryId,
            metadata: a.metadata,
            createdAt: a.createdAt.toISOString()
        }));

        res.json(response);
    } catch (error) {
        console.error('Dashboard activity error:', error);
        res.status(500).json({ error: 'Failed to get activity feed' });
    }
});

export default router;
