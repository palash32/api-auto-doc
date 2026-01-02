/**
 * Health Routes
 */

import { Router, Request, Response } from 'express';

const router = Router();

router.get('/', (req: Request, res: Response) => {
    res.json({
        status: 'healthy',
        version: '2.0.0',
        timestamp: new Date().toISOString(),
        uptime: process.uptime()
    });
});

router.get('/ready', (req: Request, res: Response) => {
    // TODO: Check database, redis, other service connections
    res.json({ ready: true });
});

router.get('/live', (req: Request, res: Response) => {
    res.json({ live: true });
});

export default router;
