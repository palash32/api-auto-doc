/**
 * JWT Authentication Middleware
 */

import { Request, Response, NextFunction } from 'express';
import jwt from 'jsonwebtoken';

const JWT_SECRET = process.env.JWT_SECRET || 'dev-secret-change-in-production';

export interface AuthenticatedRequest extends Request {
    user?: {
        sub: string;
        email: string;
        organization_id?: string;
    };
}

export const authenticateToken = (req: Request, res: Response, next: NextFunction) => {
    const authHeader = req.headers.authorization;
    const token = authHeader && authHeader.split(' ')[1]; // Bearer TOKEN

    if (!token) {
        return res.status(401).json({ error: 'Access token required' });
    }

    try {
        const decoded = jwt.verify(token, JWT_SECRET) as any;
        (req as AuthenticatedRequest).user = {
            sub: decoded.sub,
            email: decoded.email,
            organization_id: decoded.organization_id
        };
        next();
    } catch (error) {
        return res.status(403).json({ error: 'Invalid or expired token' });
    }
};

export const optionalAuth = (req: Request, res: Response, next: NextFunction) => {
    const authHeader = req.headers.authorization;
    const token = authHeader && authHeader.split(' ')[1];

    if (token) {
        try {
            const decoded = jwt.verify(token, JWT_SECRET) as any;
            (req as AuthenticatedRequest).user = {
                sub: decoded.sub,
                email: decoded.email,
                organization_id: decoded.organization_id
            };
        } catch {
            // Token invalid, continue without user
        }
    }

    next();
};
