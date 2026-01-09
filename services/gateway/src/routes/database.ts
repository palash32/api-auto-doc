/**
 * Database Routes - Database Insights
 * 
 * Shows database table relationships and API-to-table mappings.
 */

import { Router, Request, Response } from 'express';
import { RepoStore, EndpointStore } from '../store';

const router = Router();

// Database patterns to detect in code/endpoints
const DB_PATTERNS = [
    { name: 'users', pattern: /user|account|profile|member/i, operations: ['read', 'write'] },
    { name: 'repositories', pattern: /repo|repository|project/i, operations: ['read', 'write'] },
    { name: 'endpoints', pattern: /endpoint|api|route/i, operations: ['read', 'write'] },
    { name: 'organizations', pattern: /org|organization|team|company/i, operations: ['read'] },
    { name: 'sessions', pattern: /session|auth|token|login/i, operations: ['read', 'write', 'delete'] },
    { name: 'activities', pattern: /activity|log|event|audit/i, operations: ['write'] },
    { name: 'settings', pattern: /setting|config|preference/i, operations: ['read', 'write'] },
    { name: 'payments', pattern: /payment|billing|invoice|subscription/i, operations: ['read', 'write'] }
];

// Database Overview - Shows detected tables and connections
router.get('/overview', async (req: Request, res: Response) => {
    try {
        const orgId = (req as any).user?.organization_id || 'default';
        const repositories = await RepoStore.findByOrg(orgId);

        const tableStats: Map<string, { reads: number; writes: number; endpoints: string[] }> = new Map();

        // Initialize tables
        DB_PATTERNS.forEach(({ name }) => {
            tableStats.set(name, { reads: 0, writes: 0, endpoints: [] });
        });

        // Analyze endpoints
        for (const repo of repositories) {
            const endpoints = await EndpointStore.findByRepo(repo.id);

            for (const endpoint of endpoints) {
                const pathLower = endpoint.path.toLowerCase();

                for (const { name, pattern, operations } of DB_PATTERNS) {
                    if (pattern.test(pathLower)) {
                        const stats = tableStats.get(name)!;

                        if (endpoint.method === 'GET') {
                            stats.reads++;
                        } else {
                            stats.writes++;
                        }

                        if (stats.endpoints.length < 5) {
                            stats.endpoints.push(`${endpoint.method} ${endpoint.path}`);
                        }
                    }
                }
            }
        }

        // Convert to response format
        const tables = Array.from(tableStats.entries())
            .map(([name, stats]) => ({
                name,
                total_reads: stats.reads,
                total_writes: stats.writes,
                related_endpoints: stats.endpoints,
                estimated_size: Math.round(Math.random() * 1000 + 100) + ' KB' // Mock
            }))
            .filter(t => t.total_reads > 0 || t.total_writes > 0);

        res.json({
            total_tables: tables.length,
            tables,
            relationships: [
                { from: 'users', to: 'organizations', type: 'belongs_to' },
                { from: 'repositories', to: 'organizations', type: 'belongs_to' },
                { from: 'endpoints', to: 'repositories', type: 'belongs_to' },
                { from: 'activities', to: 'repositories', type: 'references' },
                { from: 'sessions', to: 'users', type: 'belongs_to' }
            ]
        });
    } catch (error) {
        console.error('Database overview error:', error);
        res.status(500).json({ error: 'Failed to fetch database overview' });
    }
});

// Table Details
router.get('/tables/:tableName', async (req: Request, res: Response) => {
    try {
        const { tableName } = req.params;
        const orgId = (req as any).user?.organization_id || 'default';
        const repositories = await RepoStore.findByOrg(orgId);

        const relatedEndpoints: any[] = [];
        const pattern = DB_PATTERNS.find(p => p.name === tableName)?.pattern || new RegExp(tableName, 'i');

        for (const repo of repositories) {
            const endpoints = await EndpointStore.findByRepo(repo.id);

            for (const endpoint of endpoints) {
                if (pattern.test(endpoint.path)) {
                    relatedEndpoints.push({
                        id: endpoint.id,
                        method: endpoint.method,
                        path: endpoint.path,
                        repository: repo.name,
                        operation: endpoint.method === 'GET' ? 'read' : 'write'
                    });
                }
            }
        }

        res.json({
            name: tableName,
            columns: [
                { name: 'id', type: 'uuid', primary: true },
                { name: 'created_at', type: 'timestamp', nullable: false },
                { name: 'updated_at', type: 'timestamp', nullable: true },
                { name: 'data', type: 'jsonb', nullable: true }
            ],
            indexes: [
                { name: `${tableName}_pkey`, columns: ['id'], unique: true },
                { name: `${tableName}_created_at_idx`, columns: ['created_at'], unique: false }
            ],
            related_endpoints: relatedEndpoints.slice(0, 20),
            statistics: {
                estimated_rows: Math.round(Math.random() * 10000 + 100),
                total_size_kb: Math.round(Math.random() * 5000 + 50),
                index_size_kb: Math.round(Math.random() * 500 + 10)
            }
        });
    } catch (error) {
        console.error('Table details error:', error);
        res.status(500).json({ error: 'Failed to fetch table details' });
    }
});

// Query Insights - Slow queries, optimization suggestions
router.get('/insights', async (req: Request, res: Response) => {
    try {
        // Mock data for demo
        res.json({
            slow_queries: [
                {
                    query: 'SELECT * FROM endpoints WHERE repository_id = ?',
                    avg_time_ms: 45,
                    call_count: 1250,
                    suggestion: 'Consider adding index on repository_id'
                }
            ],
            optimization_suggestions: [
                {
                    table: 'endpoints',
                    type: 'index',
                    description: 'Add index on (repository_id, method) for faster filtering',
                    impact: 'medium'
                },
                {
                    table: 'activities',
                    type: 'partition',
                    description: 'Consider partitioning by created_at for better query performance',
                    impact: 'low'
                }
            ],
            connection_pool: {
                active: 3,
                idle: 7,
                max: 20,
                waiting: 0
            }
        });
    } catch (error) {
        console.error('Database insights error:', error);
        res.status(500).json({ error: 'Failed to fetch database insights' });
    }
});

export default router;
