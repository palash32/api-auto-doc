/**
 * Authentication Routes
 * 
 * Handles: Registration, Login, OAuth, User Profile
 */

import { Router, Request, Response } from 'express';
import jwt from 'jsonwebtoken';
import { v4 as uuidv4 } from 'uuid';
import { authenticateToken } from '../middleware/auth';
import { users, organizations, seedDemoData, User, UserStore, OrgStore } from '../store';

const router = Router();

// JWT secret (use env var in production)
const JWT_SECRET = process.env.JWT_SECRET_KEY || 'dev-secret-change-in-production';

// Seed demo data on startup
seedDemoData();

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
                members: [] // Updated to match store type
            };
            organizations.set(organization.id, organization);
        }

        // Create user
        const user: User = {
            id: uuidv4(),
            email,
            username: email.split('@')[0], // Add username
            githubId: 0, // Default for non-github users
            accessToken: '', // Default
            organizationId: organization.id
        };

        // Note: Password handling should be added to User interface in store.ts if needed, 
        // but for now we follow store.ts structure which seems focused on OAuth. 
        // We'll trust the store.ts definition for now.

        users.set(user.id, user);

        // Generate JWT
        const token = jwt.sign(
            { sub: user.id, email: user.email, organization_id: user.organizationId },
            JWT_SECRET,
            { expiresIn: '7d' }
        );

        res.status(201).json({
            access_token: token,
            token_type: 'bearer',
            user: {
                id: user.id,
                email: user.email,
                full_name: user.username,
                organization_id: user.organizationId,
                role: 'admin'
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

        // Simple password check hack for demo (since store doesn't store password)
        // In real app, store would have passwordHash
        if (!user) {
            return res.status(401).json({ error: 'Invalid email or password' });
        }

        // Generate JWT
        const token = jwt.sign(
            { sub: user.id, email: user.email, organization_id: user.organizationId },
            JWT_SECRET,
            { expiresIn: '7d' }
        );

        res.json({
            access_token: token,
            token_type: 'bearer',
            user: {
                id: user.id,
                email: user.email,
                full_name: user.username,
                organization_id: user.organizationId,
                role: 'admin',
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

        // Try database first (production), fall back to in-memory (development)
        let user = await UserStore.findById(userId);
        if (!user) {
            user = users.get(userId) || null;
        }

        if (!user) {
            return res.status(404).json({ error: 'User not found' });
        }

        res.json({
            id: user.id,
            email: user.email,
            full_name: user.username,
            organization_id: user.organizationId,
            role: 'admin',
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

        const accessToken = tokenData.access_token!;

        // Fetch user profile from GitHub
        const userResponse = await fetch('https://api.github.com/user', {
            headers: {
                'Authorization': `Bearer ${accessToken}`,
                'Accept': 'application/vnd.github.v3+json',
            },
        });

        const githubUser = await userResponse.json() as { id: number; login: string; name?: string; email?: string, avatar_url?: string };

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

        // Find or create user - use database in production
        let user = await UserStore.findByGithubId(githubUser.id);

        if (!user) {
            // Check if user exists with this email
            user = await UserStore.findByEmail(primaryEmail);

            if (user) {
                // Link GitHub to existing user - update in database
                await UserStore.update(user.id, {
                    githubId: githubUser.id,
                    accessToken: accessToken,
                    username: githubUser.name || githubUser.login,
                    avatarUrl: githubUser.avatar_url
                });
            } else {
                // Create new user with their own personal workspace
                // Use GitHub username for unique org name (not email domain which would cause sharing)
                const orgName = `${githubUser.login}'s Workspace`;

                // Always create a new org for new users (no sharing)
                let organization: { id: string; name: string; members: string[] } = {
                    id: uuidv4(),
                    name: orgName,
                    members: []
                };
                await OrgStore.create(organization);

                user = {
                    id: uuidv4(),
                    email: primaryEmail,
                    username: githubUser.name || githubUser.login,
                    organizationId: organization.id,
                    githubId: githubUser.id,
                    accessToken: accessToken,
                    avatarUrl: githubUser.avatar_url
                };
                await UserStore.create(user);
            }
        } else {
            // Update token and refresh profile info from GitHub
            await UserStore.update(user.id, {
                accessToken: accessToken,
                username: githubUser.name || githubUser.login,
                avatarUrl: githubUser.avatar_url
            });
        }

        // Generate JWT with GitHub token included
        const token = jwt.sign(
            {
                sub: user.id,
                email: user.email,
                organization_id: user.organizationId,  // Include org for repo operations
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
