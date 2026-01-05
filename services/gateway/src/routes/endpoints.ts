/**
 * Endpoints Routes
 * 
 * Handles: List endpoints, Get endpoint details, Update documentation, AI Generation
 */

import { Router, Request, Response } from 'express';
import axios from 'axios';
import { authenticateToken } from '../middleware/auth';
import { endpoints, Endpoint } from '../store';

const router = Router();
const AI_SERVICE_URL = process.env.AI_SERVICE_URL || 'http://localhost:3002';

// =============================================================================
// LIST ENDPOINTS FOR REPOSITORY
// =============================================================================

router.get('/repositories/:repoId/endpoints', authenticateToken, async (req: Request, res: Response) => {
    try {
        const { repoId } = req.params;
        const { page = 1, per_page = 50, method, search } = req.query;

        console.log(`📊 DEBUG: Total endpoints in store: ${endpoints.size}`);
        console.log(`📊 DEBUG: Fetching endpoints for repo: ${repoId}`);

        // Filter endpoints
        let filtered = Array.from(endpoints.values())
            .filter(e => e.repositoryId === repoId);

        console.log(`📊 DEBUG: Found ${filtered.length} endpoints for repo ${repoId}`);

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

// =============================================================================
// GENERATE DOCUMENTATION (AI)
// =============================================================================

router.post('/endpoints/:id/generate', authenticateToken, async (req: Request, res: Response) => {
    try {
        const { id } = req.params;
        const endpoint = endpoints.get(id);

        if (!endpoint) {
            return res.status(404).json({ error: 'Endpoint not found' });
        }

        console.log(`🤖 Generatng docs for ${endpoint.method} ${endpoint.path}...`);

        // Call AI Service
        try {
            const aiResponse = await axios.post(`${AI_SERVICE_URL}/generate`, {
                endpoint: {
                    path: endpoint.path,
                    method: endpoint.method,
                    code_snippet: endpoint.codeSnippet || "",
                    file_path: endpoint.filePath
                }
            });

            const result = aiResponse.data;
            if (result.success && result.documentation) {
                const doc = result.documentation;

                // Update endpoint with generated docs
                endpoint.summary = doc.summary || endpoint.summary;
                endpoint.description = doc.description || endpoint.description;

                if (doc.parameters && doc.parameters.length > 0) {
                    endpoint.parameters = doc.parameters;
                }

                if (doc.request_body) {
                    endpoint.requestBody = doc.request_body;
                }

                if (doc.responses && doc.responses.length > 0) {
                    endpoint.responses = doc.responses;
                }

                console.log(`✅ AI Docs generated for ${endpoint.path}`);

                res.json({
                    id: endpoint.id,
                    success: true,
                    cost: result.cost,
                    documentation: doc
                });
            } else {
                throw new Error('AI service returned unsuccessful response');
            }

        } catch (aiError: any) {
            console.error('AI Service call failed:', aiError.response?.data || aiError.message);
            return res.status(502).json({
                error: 'AI Generation failed',
                details: aiError.response?.data || aiError.message
            });
        }

    } catch (error) {
        console.error('Generate docs error:', error);
        res.status(500).json({ error: 'Failed to generate documentation' });
    }
});

export default router;
