/**
 * Authentication Routes
 * 
 * Handles: Registration, Login, OAuth, User Profile
 */

import { Router, Request, Response } from 'express';
import jwt from 'jsonwebtoken';
import { v4 as uuidv4 } from 'uuid';
import { authenticateToken } from '../middleware/auth';

const router = Router();

// In-memory user store (replace with database in production)
interface User {
    id: string;
    email: string;
    fullName: string;
    passwordHash: string;
    organizationId: string;
    role: 'admin' | 'developer' | 'viewer';
    githubId?: string;
    createdAt: Date;
}

const users: Map<string, User> = new Map();
const organizations: Map<string, { id: string; name: string; memberCount: number }> = new Map();

// JWT secret (use env var in production)
const JWT_SECRET = process.env.JWT_SECRET || 'dev-secret-change-in-production';

// =============================================================================
// REGISTER
// =============================================================================

router.post('/register', async (req: Request, res: Response) => {
    try {
        // Accept both full_name (frontend) and fullName (camelCase)
        const { email, password, full_name, fullName: fullNameAlt } = req.body;
        const fullName = full_name || fullNameAlt;

        // Validation
        if (!email || !password || !fullName) {
            return res.status(400).json({
                error: 'Email, password, and full name are required',
                detail: 'Email, password, and full name are required'  // For frontend compatibility
            });
        }

        // Check if email exists
        const existingUser = Array.from(users.values()).find(u => u.email === email);
        if (existingUser) {
            return res.status(400).json({ error: 'An account with this email already exists' });
        }

        // Create organization based on email domain
        const emailDomain = email.split('@')[1].toLowerCase();
        let organization = Array.from(organizations.values()).find(o => o.name.includes(emailDomain));

        if (!organization) {
            organization = {
                id: uuidv4(),
                name: `${emailDomain} Workspace`,
                memberCount: 0
            };
            organizations.set(organization.id, organization);
        }
        organization.memberCount++;

        // Create user
        const user: User = {
            id: uuidv4(),
            email,
            fullName,
            passwordHash: password, // TODO: Hash password with bcrypt
            organizationId: organization.id,
            role: 'admin',
            createdAt: new Date()
        };
        users.set(user.id, user);

        // Generate JWT
        const token = jwt.sign(
            { sub: user.id, email: user.email },
            JWT_SECRET,
            { expiresIn: '7d' }
        );

        res.status(201).json({
            access_token: token,
            token_type: 'bearer',
            user: {
                id: user.id,
                email: user.email,
                full_name: user.fullName,
                organization_id: user.organizationId,
                role: user.role
            }
        });
    } catch (error) {
        console.error('Registration error:', error);
        res.status(500).json({ error: 'Registration failed' });
    }
});

// =============================================================================
// LOGIN
// =============================================================================

router.post('/login', async (req: Request, res: Response) => {
    try {
        const { email, password } = req.body;

        if (!email || !password) {
            return res.status(400).json({ error: 'Email and password are required' });
        }

        // Find user
        const user = Array.from(users.values()).find(u => u.email === email);
        if (!user || user.passwordHash !== password) { // TODO: Use bcrypt.compare
            return res.status(401).json({ error: 'Invalid email or password' });
        }

        // Generate JWT
        const token = jwt.sign(
            { sub: user.id, email: user.email },
            JWT_SECRET,
            { expiresIn: '7d' }
        );

        res.json({
            access_token: token,
            token_type: 'bearer',
            user: {
                id: user.id,
                email: user.email,
                full_name: user.fullName,
                organization_id: user.organizationId,
                role: user.role,
                github_connected: !!user.githubId
            }
        });
    } catch (error) {
        console.error('Login error:', error);
        res.status(500).json({ error: 'Login failed' });
    }
});

// =============================================================================
// GET CURRENT USER
// =============================================================================

router.get('/me', authenticateToken, async (req: Request, res: Response) => {
    try {
        const userId = (req as any).user?.sub;
        const user = users.get(userId);

        if (!user) {
            return res.status(404).json({ error: 'User not found' });
        }

        res.json({
            id: user.id,
            email: user.email,
            full_name: user.fullName,
            organization_id: user.organizationId,
            role: user.role,
            github_connected: !!user.githubId,
            is_verified: true
        });
    } catch (error) {
        console.error('Get user error:', error);
        res.status(500).json({ error: 'Failed to get user' });
    }
});

// =============================================================================
// GITHUB OAUTH
// =============================================================================

router.get('/github/login', (req: Request, res: Response) => {
    const clientId = process.env.GITHUB_CLIENT_ID;

    if (!clientId) {
        return res.status(500).json({ error: 'GitHub OAuth not configured' });
    }

    const redirectUri = process.env.GITHUB_REDIRECT_URI || 'http://localhost:8000/api/auth/github/callback';
    const scope = 'read:user user:email repo';

    const githubAuthUrl = `https://github.com/login/oauth/authorize?client_id=${clientId}&redirect_uri=${encodeURIComponent(redirectUri)}&scope=${encodeURIComponent(scope)}`;

    res.redirect(githubAuthUrl);
});

router.get('/github/callback', async (req: Request, res: Response) => {
    const { code, error } = req.query;
    const frontendUrl = process.env.FRONTEND_URL || 'http://localhost:3000';

    if (error) {
        console.error('GitHub OAuth error:', error);
        return res.redirect(`${frontendUrl}/auth/callback?error=${error}`);
    }

    if (!code) {
        return res.redirect(`${frontendUrl}/auth/callback?error=missing_code`);
    }

    try {
        // Exchange code for access token
        const tokenResponse = await fetch('https://github.com/login/oauth/access_token', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            },
            body: JSON.stringify({
                client_id: process.env.GITHUB_CLIENT_ID,
                client_secret: process.env.GITHUB_CLIENT_SECRET,
                code: code,
                redirect_uri: process.env.GITHUB_REDIRECT_URI || 'http://localhost:8000/api/auth/github/callback',
            }),
        });

        const tokenData = await tokenResponse.json() as { error?: string; access_token?: string };

        if (tokenData.error) {
            console.error('GitHub token exchange error:', tokenData);
            return res.redirect(`${frontendUrl}/auth/callback?error=${tokenData.error}`);
        }

        const accessToken = tokenData.access_token;

        // Fetch user profile from GitHub
        const userResponse = await fetch('https://api.github.com/user', {
            headers: {
                'Authorization': `Bearer ${accessToken}`,
                'Accept': 'application/vnd.github.v3+json',
            },
        });

        const githubUser = await userResponse.json() as { id: number; login: string; name?: string; email?: string };

        // Fetch user emails (in case primary email is private)
        const emailsResponse = await fetch('https://api.github.com/user/emails', {
            headers: {
                'Authorization': `Bearer ${accessToken}`,
                'Accept': 'application/vnd.github.v3+json',
            },
        });

        const emails = await emailsResponse.json() as Array<{ email: string; primary: boolean }>;
        const primaryEmail = emails.find((e) => e.primary)?.email || githubUser.email;

        if (!primaryEmail) {
            return res.redirect(`${frontendUrl}/auth/callback?error=no_email`);
        }

        // Find or create user
        let user = Array.from(users.values()).find(u => u.githubId === String(githubUser.id));

        if (!user) {
            // Check if user exists with this email
            user = Array.from(users.values()).find(u => u.email === primaryEmail);

            if (user) {
                // Link GitHub to existing user
                user.githubId = String(githubUser.id);
            } else {
                // Create new user
                const emailDomain = primaryEmail.split('@')[1]?.toLowerCase() || 'github';
                let organization = Array.from(organizations.values()).find(o => o.name.includes(emailDomain));

                if (!organization) {
                    organization = {
                        id: uuidv4(),
                        name: `${emailDomain} Workspace`,
                        memberCount: 0
                    };
                    organizations.set(organization.id, organization);
                }
                organization.memberCount++;

                user = {
                    id: uuidv4(),
                    email: primaryEmail,
                    fullName: githubUser.name || githubUser.login,
                    passwordHash: '', // No password for OAuth users
                    organizationId: organization.id,
                    role: 'admin',
                    githubId: String(githubUser.id),
                    createdAt: new Date()
                };
                users.set(user.id, user);
            }
        }

        // Generate JWT with GitHub token included
        const token = jwt.sign(
            {
                sub: user.id,
                email: user.email,
                github_token: accessToken // Include GitHub token for API calls
            },
            JWT_SECRET,
            { expiresIn: '7d' }
        );

        console.log(`✅ GitHub OAuth successful for: ${user.email}`);

        // Redirect to frontend with token
        res.redirect(`${frontendUrl}/auth/callback?token=${token}`);

    } catch (error) {
        console.error('GitHub OAuth callback error:', error);
        res.redirect(`${frontendUrl}/auth/callback?error=oauth_failed`);
    }
});

export default router;
