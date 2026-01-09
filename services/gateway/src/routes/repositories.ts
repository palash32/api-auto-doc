/**
 * Repository Routes
 * 
 * Handles: List, Add, Delete, Scan repositories
 */

import { Router, Request, Response } from 'express';
import { v4 as uuidv4 } from 'uuid';
import axios from 'axios';
import { authenticateToken } from '../middleware/auth';
import { repositories, endpoints, Repository, Endpoint, RepoStore, EndpointStore, ActivityStore, Activity } from '../store';
import { queueScan, completeScan, hasActiveScan } from '../scan-queue';

const router = Router();
const SCANNER_URL = process.env.SCANNER_URL || 'http://localhost:3001';

// =============================================================================
// HELPER: TRIGGER SCAN
// =============================================================================

async function triggerScan(repo: Repository) {
    try {
        console.log(`🚀 Triggering scan for ${repo.fullName} at ${SCANNER_URL}`);

        // Update status to scanning in database
        await RepoStore.update(repo.id, { scanStatus: 'scanning' });

        // Log scan_started activity
        await ActivityStore.create({
            id: uuidv4(),
            organizationId: repo.organizationId,
            repositoryId: repo.id,
            type: 'scan_started',
            title: 'Scanning...',
            description: repo.fullName,
            metadata: { repoName: repo.fullName },
            createdAt: new Date()
        });

        // 1. Start Scan
        const startRes = await axios.post(`${SCANNER_URL}/scan`, {
            url: repo.url,
            branch: 'main' // Default to main/master
        });

        const scanId = startRes.data.scan_id;
        console.log(`✅ Scan started for ${repo.fullName} (ID: ${scanId})`);;

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

                    // 4. Update Repository in database
                    await RepoStore.update(repo.id, {
                        scanStatus: 'completed',
                        apiCount: detectedEndpoints.length,
                        lastScanned: new Date()
                    });

                    // 5. Clear old endpoints for this repo from database
                    await EndpointStore.deleteByRepo(repo.id);

                    // 6. Add new endpoints to database
                    for (const ep of detectedEndpoints) {
                        const newEndpoint: Endpoint = {
                            id: uuidv4(),
                            repositoryId: repo.id,
                            path: ep.path,
                            method: ep.method,
                            summary: ep.description || `${ep.method} ${ep.path}`,
                            description: '',
                            tags: [],
                            parameters: ep.parameters || [],
                            requestBody: ep.body || null,
                            responses: [],
                            authRequired: false,
                            filePath: ep.file_path,
                            codeSnippet: ep.code_snippet
                        };
                        await EndpointStore.create(newEndpoint);
                    }

                    // Log scan_completed activity
                    await ActivityStore.create({
                        id: uuidv4(),
                        organizationId: repo.organizationId,
                        repositoryId: repo.id,
                        type: 'scan_completed',
                        title: 'Scan completed',
                        description: repo.fullName,
                        metadata: { repoName: repo.fullName, endpointCount: detectedEndpoints.length },
                        createdAt: new Date()
                    });

                    console.log(`💾 Saved ${detectedEndpoints.length} endpoints for ${repo.fullName} to database`);

                } else if (status === 'failed') {
                    clearInterval(pollInterval);
                    await RepoStore.update(repo.id, { scanStatus: 'failed' });

                    // Log scan_failed activity
                    await ActivityStore.create({
                        id: uuidv4(),
                        organizationId: repo.organizationId,
                        repositoryId: repo.id,
                        type: 'scan_failed',
                        title: 'Scan failed',
                        description: `Could not parse ${repo.fullName}`,
                        metadata: { repoName: repo.fullName },
                        createdAt: new Date()
                    });

                    console.error(`❌ Scan failed for ${repo.fullName}`);
                }
            } catch (err) {
                console.error(`Error polling scan status:`, err);
                // Don't clear interval immediately, might be transient network error
            }
        }, 2000);

    } catch (error) {
        console.error('Failed to trigger scan:', error);
        await RepoStore.update(repo.id, { scanStatus: 'failed' });

        // Log scan_failed activity for connection errors
        await ActivityStore.create({
            id: uuidv4(),
            organizationId: repo.organizationId,
            repositoryId: repo.id,
            type: 'scan_failed',
            title: 'Scan failed',
            description: `Could not connect to scanner for ${repo.fullName}`,
            metadata: { repoName: repo.fullName, error: String(error) },
            createdAt: new Date()
        });
    }
}

// =============================================================================
// LIST REPOSITORIES
// =============================================================================

router.get('/', authenticateToken, async (req: Request, res: Response) => {
    try {
        const organizationId = (req as any).user?.organization_id;

        // Get repos from database (or in-memory fallback)
        const orgRepos = await RepoStore.findByOrg(organizationId || '');

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

        // Check if already added - use database
        const existing = await RepoStore.findByFullName(fullName, organizationId || '');

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

        // Save to database
        await RepoStore.create(repo);

        // Log repo_added activity
        await ActivityStore.create({
            id: uuidv4(),
            organizationId: repo.organizationId,
            repositoryId: repo.id,
            type: 'repo_added',
            title: 'Repository connected',
            description: repo.fullName,
            metadata: { repoName: repo.fullName, url: repo.url },
            createdAt: new Date()
        });

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

        // Use database lookup
        const repo = await RepoStore.findById(id);
        if (!repo) {
            return res.status(404).json({ error: 'Repository not found' });
        }

        if (repo.organizationId !== organizationId) {
            return res.status(403).json({ error: 'Access denied' });
        }

        // Delete repo and its endpoints from database
        await RepoStore.delete(id);

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
        // Use database lookup
        const repo = await RepoStore.findById(id);

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
