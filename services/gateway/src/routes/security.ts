/**
 * Security Routes - API Security Analysis
 * 
 * Detects authentication gaps and security vulnerabilities in APIs.
 */

import { Router, Request, Response } from 'express';
import { RepoStore, EndpointStore } from '../store';

const router = Router();

// Security Scan Results - Analyze endpoints for authentication gaps
router.get('/scan-results', async (req: Request, res: Response) => {
    try {
        const orgId = (req as any).user?.organization_id || 'default';
        const repositories = await RepoStore.findByOrg(orgId);

        let totalEndpoints = 0;
        let authRequiredCount = 0;
        let publicCount = 0;
        const vulnerabilities: any[] = [];

        for (const repo of repositories) {
            const endpoints = await EndpointStore.findByRepo(repo.id);
            totalEndpoints += endpoints.length;

            for (const endpoint of endpoints) {
                if (endpoint.authRequired) {
                    authRequiredCount++;
                } else {
                    publicCount++;

                    // Flag potentially sensitive endpoints without auth
                    const sensitivePatterns = [
                        /\/user/i, /\/admin/i, /\/account/i, /\/payment/i,
                        /\/billing/i, /\/settings/i, /\/profile/i, /\/private/i
                    ];

                    const isSensitive = sensitivePatterns.some(p => p.test(endpoint.path));

                    if (isSensitive) {
                        vulnerabilities.push({
                            id: `vuln_${endpoint.id}`,
                            type: 'auth_gap',
                            severity: 'medium',
                            endpoint_path: endpoint.path,
                            endpoint_method: endpoint.method,
                            repository_name: repo.name,
                            description: `Potentially sensitive endpoint without authentication`,
                            recommendation: 'Consider adding authentication requirement',
                            detected_at: new Date().toISOString()
                        });
                    }
                }
            }
        }

        res.json({
            summary: {
                total_endpoints: totalEndpoints,
                auth_required: authRequiredCount,
                public: publicCount,
                vulnerability_count: vulnerabilities.length,
                security_score: totalEndpoints > 0
                    ? Math.round(100 - (vulnerabilities.length / totalEndpoints * 100))
                    : 100
            },
            vulnerabilities: vulnerabilities.slice(0, 20) // Limit to 20
        });
    } catch (error) {
        console.error('Security scan error:', error);
        res.status(500).json({ error: 'Failed to fetch security scan results' });
    }
});

// Vulnerabilities list
router.get('/vulnerabilities', async (req: Request, res: Response) => {
    try {
        const severity = req.query.severity as string;
        const orgId = (req as any).user?.organization_id || 'default';
        const repositories = await RepoStore.findByOrg(orgId);

        const vulnerabilities: any[] = [];

        for (const repo of repositories) {
            const endpoints = await EndpointStore.findByRepo(repo.id);

            for (const endpoint of endpoints) {
                if (!endpoint.authRequired) {
                    const sensitivePatterns = [
                        { pattern: /\/admin/i, severity: 'high' },
                        { pattern: /\/payment/i, severity: 'high' },
                        { pattern: /\/billing/i, severity: 'high' },
                        { pattern: /\/user/i, severity: 'medium' },
                        { pattern: /\/account/i, severity: 'medium' },
                        { pattern: /\/settings/i, severity: 'medium' },
                        { pattern: /\/profile/i, severity: 'low' },
                    ];

                    for (const { pattern, severity: vuln_severity } of sensitivePatterns) {
                        if (pattern.test(endpoint.path)) {
                            if (!severity || severity === vuln_severity) {
                                vulnerabilities.push({
                                    id: `vuln_${endpoint.id}`,
                                    type: 'auth_gap',
                                    severity: vuln_severity,
                                    endpoint_id: endpoint.id,
                                    endpoint_path: endpoint.path,
                                    endpoint_method: endpoint.method,
                                    repository_id: repo.id,
                                    repository_name: repo.name,
                                    description: `${endpoint.method} ${endpoint.path} lacks authentication`,
                                    recommendation: 'Add authentication middleware',
                                    detected_at: new Date().toISOString()
                                });
                            }
                            break;
                        }
                    }
                }
            }
        }

        res.json(vulnerabilities);
    } catch (error) {
        console.error('Vulnerabilities error:', error);
        res.status(500).json({ error: 'Failed to fetch vulnerabilities' });
    }
});

// Acknowledge a vulnerability
router.post('/vulnerabilities/:vulnId/acknowledge', async (req: Request, res: Response) => {
    try {
        const { vulnId } = req.params;
        // In production, store acknowledgment in database
        res.json({ success: true, message: `Vulnerability ${vulnId} acknowledged` });
    } catch (error) {
        console.error('Acknowledge vulnerability error:', error);
        res.status(500).json({ error: 'Failed to acknowledge vulnerability' });
    }
});

export default router;
