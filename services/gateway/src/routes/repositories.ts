/**
 * Repository Routes
 * 
 * Handles: List, Add, Delete, Scan repositories
 */

import { Router, Request, Response } from 'express';
import { v4 as uuidv4 } from 'uuid';
import axios from 'axios';
import { authenticateToken } from '../middleware/auth';
import { repositories, endpoints, Repository, Endpoint } from '../store';

const router = Router();
const SCANNER_URL = process.env.SCANNER_URL || 'http://localhost:3001';

// =============================================================================
// HELPER: TRIGGER SCAN
// =============================================================================

async function triggerScan(repo: Repository) {
    try {
        console.log(`🚀 Triggering scan for ${repo.fullName} at ${SCANNER_URL}`);
        repo.scanStatus = 'scanning';

        // 1. Start Scan
        const startRes = await axios.post(`${SCANNER_URL}/scan`, {
            url: repo.url,
            branch: 'main' // Default to main/master
        });

        const scanId = startRes.data.scan_id;
        console.log(`✅ Scan started for ${repo.fullName} (ID: ${scanId})`);

        // 2. Poll for completion
        const pollInterval = setInterval(async () => {
            try {
                const statusRes = await axios.get(`${SCANNER_URL}/scan/${scanId}`);
                const status = statusRes.data.status;

                if (status === 'completed') {
                    clearInterval(pollInterval);
                    console.log(`🎉 Scan completed for ${repo.fullName}`);

                    // 3. Get Results
                    const resultRes = await axios.get(`${SCANNER_URL}/scan/${scanId}/endpoints`);
                    const detectedEndpoints = resultRes.data.endpoints || [];

                    // 4. Update Store
                    repo.scanStatus = 'completed';
                    repo.apiCount = detectedEndpoints.length;
                    repo.lastScanned = new Date();

                    // Clear old endpoints for this repo
                    for (const [id, ep] of endpoints.entries()) {
                        if (ep.repositoryId === repo.id) {
                            endpoints.delete(id);
                        }
                    }

                    // Add new endpoints
                    detectedEndpoints.forEach((ep: any) => {
                        const newEndpoint: Endpoint = {
                            id: uuidv4(),
                            repositoryId: repo.id,
                            path: ep.path,
                            method: ep.method,
                            summary: ep.description || `${ep.method} ${ep.path}`,
                            description: '',
                            tags: [], // Scanner might detect tags, but simple for now
                            parameters: ep.parameters || [],
                            requestBody: ep.body || null,
                            responses: [],
                            authRequired: false, // Detect auth in scanner?
                            filePath: ep.file_path,
                            codeSnippet: ep.code_snippet
                        };
                        endpoints.set(newEndpoint.id, newEndpoint);
                    });

                    console.log(`💾 Saved ${detectedEndpoints.length} endpoints for ${repo.fullName}`);

                } else if (status === 'failed') {
                    clearInterval(pollInterval);
                    repo.scanStatus = 'failed';
                    console.error(`❌ Scan failed for ${repo.fullName}`);
                }
            } catch (err) {
                console.error(`Error polling scan status:`, err);
                // Don't clear interval immediately, might be transient network error
            }
        }, 2000);

    } catch (error) {
        console.error('Failed to trigger scan:', error);
        repo.scanStatus = 'failed';
    }
}

// =============================================================================
// LIST REPOSITORIES
// =============================================================================

router.get('/', authenticateToken, async (req: Request, res: Response) => {
    try {
        const organizationId = (req as any).user?.organization_id;

        // Filter repos by organization
        const orgRepos = Array.from(repositories.values())
            .filter(r => r.organizationId === organizationId);

        res.json(orgRepos.map(r => ({
            id: r.id,
            name: r.name,
            full_name: r.fullName,
            url: r.url,
            status: r.scanStatus,
            api_count: r.apiCount,
            last_scanned: r.lastScanned,
            health_score: 100
        })));
    } catch (error) {
        console.error('List repos error:', error);
        res.status(500).json({ error: 'Failed to list repositories' });
    }
});

// =============================================================================
// ADD REPOSITORY
// =============================================================================

router.post('/', authenticateToken, async (req: Request, res: Response) => {
    try {
        const { url } = req.query;
        const organizationId = (req as any).user?.organization_id;

        if (!url || typeof url !== 'string') {
            return res.status(400).json({ error: 'Repository URL is required' });
        }

        // Parse GitHub URL
        const match = url.match(/github\.com[\/:]([^\/]+)\/([^\/\.]+)/);
        if (!match) {
            return res.status(400).json({ error: 'Invalid GitHub URL' });
        }

        const [, owner, name] = match;
        const fullName = `${owner}/${name}`;

        // Check if already added
        const existing = Array.from(repositories.values())
            .find(r => r.fullName === fullName && r.organizationId === organizationId);

        if (existing) {
            return res.status(400).json({ error: 'Repository already added' });
        }

        // Create repository
        const repo: Repository = {
            id: uuidv4(),
            name,
            fullName,
            url: `https://github.com/${fullName}`,
            organizationId,
            scanStatus: 'pending',
            apiCount: 0,
            lastScanned: null,
            createdAt: new Date()
        };
        repositories.set(repo.id, repo);

        // Queue scan
        triggerScan(repo);

        res.status(201).json({
            id: repo.id,
            name: repo.name,
            full_name: repo.fullName,
            url: repo.url,
            status: repo.scanStatus,
            api_count: repo.apiCount,
            message: 'Repository added, scanning in progress'
        });
    } catch (error) {
        console.error('Add repo error:', error);
        res.status(500).json({ error: 'Failed to add repository' });
    }
});

// =============================================================================
// DELETE REPOSITORY
// =============================================================================

router.delete('/:id', authenticateToken, async (req: Request, res: Response) => {
    try {
        const { id } = req.params;
        const organizationId = (req as any).user?.organization_id;

        const repo = repositories.get(id);
        if (!repo) {
            return res.status(404).json({ error: 'Repository not found' });
        }

        if (repo.organizationId !== organizationId) {
            return res.status(403).json({ error: 'Access denied' });
        }

        // Delete repo and its endpoints
        repositories.delete(id);
        for (const [epId, ep] of endpoints.entries()) {
            if (ep.repositoryId === id) {
                endpoints.delete(epId);
            }
        }

        res.status(204).send();
    } catch (error) {
        console.error('Delete repo error:', error);
        res.status(500).json({ error: 'Failed to delete repository' });
    }
});

// =============================================================================
// TRIGGER RESCAN
// =============================================================================

router.post('/:id/scan', authenticateToken, async (req: Request, res: Response) => {
    try {
        const { id } = req.params;
        const repo = repositories.get(id);

        if (!repo) {
            return res.status(404).json({ error: 'Repository not found' });
        }

        triggerScan(repo);

        res.json({ message: 'Scan started', status: 'scanning' });
    } catch (error) {
        console.error('Rescan error:', error);
        res.status(500).json({ error: 'Failed to trigger scan' });
    }
});

export default router;
