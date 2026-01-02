/**
 * Repository Routes
 * 
 * Handles: List, Add, Delete, Scan repositories
 */

import { Router, Request, Response } from 'express';
import { v4 as uuidv4 } from 'uuid';
import { authenticateToken } from '../middleware/auth';

const router = Router();

// In-memory repository store (replace with database)
interface Repository {
    id: string;
    name: string;
    fullName: string;
    url: string;
    organizationId: string;
    scanStatus: 'pending' | 'scanning' | 'completed' | 'failed';
    apiCount: number;
    lastScanned: Date | null;
    createdAt: Date;
}

const repositories: Map<string, Repository> = new Map();

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

        // TODO: Queue scan job (call scanner service)
        console.log(`📥 Repository added: ${fullName} - Scan queued`);

        // Simulate scan completion after 2 seconds (for demo)
        setTimeout(() => {
            const r = repositories.get(repo.id);
            if (r) {
                r.scanStatus = 'completed';
                r.apiCount = Math.floor(Math.random() * 20) + 5; // Random 5-25 APIs
                r.lastScanned = new Date();
                console.log(`✅ Scan complete: ${fullName} - Found ${r.apiCount} APIs`);
            }
        }, 2000);

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

        repositories.delete(id);
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

        repo.scanStatus = 'scanning';

        // TODO: Call scanner service
        console.log(`🔄 Rescan triggered: ${repo.fullName}`);

        // Simulate scan
        setTimeout(() => {
            repo.scanStatus = 'completed';
            repo.apiCount = Math.floor(Math.random() * 20) + 5;
            repo.lastScanned = new Date();
        }, 2000);

        res.json({ message: 'Scan started', status: 'scanning' });
    } catch (error) {
        console.error('Rescan error:', error);
        res.status(500).json({ error: 'Failed to trigger scan' });
    }
});

export default router;
