/**
 * Endpoints Routes
 * 
 * Handles: List endpoints, Get endpoint details, Update documentation, AI Generation
 */

import { Router, Request, Response } from 'express';
import axios from 'axios';
import { authenticateToken } from '../middleware/auth';
import { endpoints, Endpoint, EndpointStore } from '../store';

const router = Router();
const AI_SERVICE_URL = process.env.AI_SERVICE_URL || 'http://localhost:3002';

// =============================================================================
// LIST ENDPOINTS FOR REPOSITORY
// =============================================================================

router.get('/repositories/:repoId/endpoints', authenticateToken, async (req: Request, res: Response) => {
    try {
        const { repoId } = req.params;
        const { page = 1, per_page = 50, method, search } = req.query;

        // Get endpoints from database (or in-memory fallback)
        let allEndpoints = await EndpointStore.findByRepo(repoId);
        console.log(`📊 DEBUG: Found ${allEndpoints.length} endpoints for repo ${repoId} from database`);

        // Filter by method
        if (method) {
            allEndpoints = allEndpoints.filter(e => e.method === (method as string).toUpperCase());
        }

        // Filter by search
        if (search) {
            const searchLower = (search as string).toLowerCase();
            allEndpoints = allEndpoints.filter(e =>
                e.path.toLowerCase().includes(searchLower) ||
                e.summary.toLowerCase().includes(searchLower)
            );
        }

        // Paginate
        const start = (Number(page) - 1) * Number(per_page);
        const paginated = allEndpoints.slice(start, start + Number(per_page));

        res.json({
            total: allEndpoints.length,
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
        // Use database lookup
        const endpoint = await EndpointStore.findById(id);

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

        // Use database lookup
        const endpoint = await EndpointStore.findById(id);
        if (!endpoint) {
            return res.status(404).json({ error: 'Endpoint not found' });
        }

        // Update fields in database
        const updates: any = {};
        if (summary !== undefined) updates.summary = summary;
        if (description !== undefined) updates.description = description;
        if (tags !== undefined) updates.tags = tags;

        await EndpointStore.update(id, updates);

        // Return updated endpoint
        const updated = await EndpointStore.findById(id);
        res.json({
            id: updated!.id,
            path: updated!.path,
            method: updated!.method,
            summary: updated!.summary,
            description: updated!.description,
            tags: updated!.tags
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
        // Use database lookup
        const endpoint = await EndpointStore.findById(id);

        if (!endpoint) {
            return res.status(404).json({ error: 'Endpoint not found' });
        }

        console.log(`🤖 Generating docs for ${endpoint.method} ${endpoint.path}...`);

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

                // Update endpoint in database with generated docs
                const updates: any = {};
                if (doc.summary) updates.summary = doc.summary;
                if (doc.description) updates.description = doc.description;
                if (doc.parameters && doc.parameters.length > 0) updates.parameters = doc.parameters;
                if (doc.request_body) updates.requestBody = doc.request_body;
                if (doc.responses && doc.responses.length > 0) updates.responses = doc.responses;

                await EndpointStore.update(id, updates);
                console.log(`✅ AI Docs generated and saved for ${endpoint.path}`);

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
