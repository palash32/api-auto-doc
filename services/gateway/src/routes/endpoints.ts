/**
 * Endpoints Routes
 * 
 * Handles: List endpoints, Get endpoint details, Update documentation
 */

import { Router, Request, Response } from 'express';
import { authenticateToken } from '../middleware/auth';

const router = Router();

// In-memory endpoint store (replace with database)
interface Endpoint {
    id: string;
    repositoryId: string;
    path: string;
    method: string;
    summary: string;
    description: string;
    tags: string[];
    parameters: any[];
    requestBody: any | null;
    responses: any[];
    authRequired: boolean;
    filePath: string;
}

const endpoints: Map<string, Endpoint> = new Map();

// Seed some demo endpoints
const demoEndpoints: Endpoint[] = [
    {
        id: 'ep-1',
        repositoryId: 'demo',
        path: '/api/users',
        method: 'GET',
        summary: 'List all users',
        description: 'Returns a paginated list of users in the organization',
        tags: ['users'],
        parameters: [{ name: 'page', in: 'query', type: 'integer' }],
        requestBody: null,
        responses: [{ status: 200, description: 'Success' }],
        authRequired: true,
        filePath: 'src/routes/users.ts'
    },
    {
        id: 'ep-2',
        repositoryId: 'demo',
        path: '/api/users/{id}',
        method: 'GET',
        summary: 'Get user by ID',
        description: 'Returns details of a specific user',
        tags: ['users'],
        parameters: [{ name: 'id', in: 'path', type: 'string', required: true }],
        requestBody: null,
        responses: [{ status: 200, description: 'Success' }, { status: 404, description: 'Not found' }],
        authRequired: true,
        filePath: 'src/routes/users.ts'
    }
];
demoEndpoints.forEach(e => endpoints.set(e.id, e));

// =============================================================================
// LIST ENDPOINTS FOR REPOSITORY
// =============================================================================

router.get('/repositories/:repoId/endpoints', authenticateToken, async (req: Request, res: Response) => {
    try {
        const { repoId } = req.params;
        const { page = 1, per_page = 50, method, search } = req.query;

        // Filter endpoints
        let filtered = Array.from(endpoints.values())
            .filter(e => e.repositoryId === repoId || repoId === 'demo');

        if (method) {
            filtered = filtered.filter(e => e.method === (method as string).toUpperCase());
        }

        if (search) {
            const searchLower = (search as string).toLowerCase();
            filtered = filtered.filter(e =>
                e.path.toLowerCase().includes(searchLower) ||
                e.summary.toLowerCase().includes(searchLower)
            );
        }

        // Paginate
        const start = (Number(page) - 1) * Number(per_page);
        const paginated = filtered.slice(start, start + Number(per_page));

        res.json({
            total: filtered.length,
            page: Number(page),
            per_page: Number(per_page),
            endpoints: paginated.map(e => ({
                id: e.id,
                path: e.path,
                method: e.method,
                summary: e.summary,
                tags: e.tags,
                auth_required: e.authRequired
            }))
        });
    } catch (error) {
        console.error('List endpoints error:', error);
        res.status(500).json({ error: 'Failed to list endpoints' });
    }
});

// =============================================================================
// GET ENDPOINT DETAILS
// =============================================================================

router.get('/endpoints/:id', authenticateToken, async (req: Request, res: Response) => {
    try {
        const { id } = req.params;
        const endpoint = endpoints.get(id);

        if (!endpoint) {
            return res.status(404).json({ error: 'Endpoint not found' });
        }

        res.json({
            id: endpoint.id,
            path: endpoint.path,
            method: endpoint.method,
            summary: endpoint.summary,
            description: endpoint.description,
            tags: endpoint.tags,
            parameters: endpoint.parameters,
            request_body: endpoint.requestBody,
            responses: endpoint.responses,
            auth_required: endpoint.authRequired,
            file_path: endpoint.filePath
        });
    } catch (error) {
        console.error('Get endpoint error:', error);
        res.status(500).json({ error: 'Failed to get endpoint' });
    }
});

// =============================================================================
// UPDATE ENDPOINT DOCUMENTATION
// =============================================================================

router.patch('/endpoints/:id', authenticateToken, async (req: Request, res: Response) => {
    try {
        const { id } = req.params;
        const { summary, description, tags } = req.body;

        const endpoint = endpoints.get(id);
        if (!endpoint) {
            return res.status(404).json({ error: 'Endpoint not found' });
        }

        // Update fields
        if (summary !== undefined) endpoint.summary = summary;
        if (description !== undefined) endpoint.description = description;
        if (tags !== undefined) endpoint.tags = tags;

        res.json({
            id: endpoint.id,
            path: endpoint.path,
            method: endpoint.method,
            summary: endpoint.summary,
            description: endpoint.description,
            tags: endpoint.tags
        });
    } catch (error) {
        console.error('Update endpoint error:', error);
        res.status(500).json({ error: 'Failed to update endpoint' });
    }
});

export default router;
