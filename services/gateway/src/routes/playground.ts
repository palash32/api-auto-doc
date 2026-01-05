/**
 * Playground Routes
 * 
 * Provides proxy functionality for testing API endpoints
 */

import { Router, Request, Response } from 'express';
import axios from 'axios';
import { authenticateToken } from '../middleware/auth';

const router = Router();

// =============================================================================
// PROXY REQUEST
// =============================================================================

router.post('/proxy', authenticateToken, async (req: Request, res: Response) => {
    try {
        const { method, url, headers, body } = req.body;

        if (!url) {
            return res.status(400).json({ error: 'URL is required' });
        }

        const startTime = Date.now();

        try {
            const response = await axios({
                method: method || 'GET',
                url,
                headers: headers || {},
                data: body || undefined,
                validateStatus: () => true, // Don't throw on any status
                timeout: 30000 // 30 second timeout
            });

            const endTime = Date.now();

            res.json({
                status: response.status,
                headers: response.headers,
                body: JSON.stringify(response.data, null, 2),
                time_ms: endTime - startTime
            });

        } catch (error: any) {
            const endTime = Date.now();

            res.status(500).json({
                status: 500,
                headers: {},
                body: JSON.stringify({ error: error.message }, null, 2),
                time_ms: endTime - startTime
            });
        }

    } catch (error) {
        console.error('Playground proxy error:', error);
        res.status(500).json({ error: 'Proxy request failed' });
    }
});

// =============================================================================
// REQUEST HISTORY (Mock - in-memory only)
// =============================================================================

const requestHistory: any[] = [];

router.get('/history', authenticateToken, async (req: Request, res: Response) => {
    const limit = parseInt(req.query.limit as string) || 20;
    res.json(requestHistory.slice(0, limit));
});

router.delete('/history', authenticateToken, async (req: Request, res: Response) => {
    requestHistory.length = 0;
    res.json({ message: 'History cleared' });
});

// =============================================================================
// AUTH TOKENS (Mock - in-memory only)
// =============================================================================

const savedTokens: any[] = [];

router.get('/tokens', authenticateToken, async (req: Request, res: Response) => {
    res.json(savedTokens);
});

router.post('/tokens', authenticateToken, async (req: Request, res: Response) => {
    const { name, token, token_type } = req.body;

    const newToken = {
        id: `token-${Date.now()}`,
        name,
        prefix: token.substring(0, 8) + '...',
        token_type,
        token // Store full token (in production, encrypt this!)
    };

    savedTokens.push(newToken);
    res.json(newToken);
});

export default router;
