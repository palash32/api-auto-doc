/**
 * Hybrid Data Store
 * 
 * Uses PostgreSQL in production, falls back to in-memory Maps in development.
 * This allows seamless local development without database setup.
 */

import { v4 as uuidv4 } from 'uuid';
import { isUsingDatabase, query, queryOne, execute, initializeDatabase } from './db';

// Types
export interface User {
    id: string;
    githubId?: number;
    username: string;
    description?: string;
    email?: string;
    avatarUrl?: string;
    accessToken?: string;
    organizationId: string;
    passwordHash?: string;
}

export interface Organization {
    id: string;
    name: string;
    members: string[];
}

export interface Repository {
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

export interface Endpoint {
    id: string;
    repositoryId: string;
    path: string;
    method: string;
    summary: string;
    description: string;
    tags: string[];
    parameters: any[];
    requestBody: any | null;
    responses: any[];
    authRequired: boolean;
    filePath: string;
    codeSnippet?: string;
}

// In-Memory Fallback Stores
const memUsers = new Map<string, User>();
const memOrganizations = new Map<string, Organization>();
const memRepositories = new Map<string, Repository>();
const memEndpoints = new Map<string, Endpoint>();

// Legacy exports for compatibility
export const users = memUsers;
export const organizations = memOrganizations;
export const repositories = memRepositories;
export const endpoints = memEndpoints;

// =============================================================================
// STORE OPERATIONS (Database or In-Memory)
// =============================================================================

// --- Users ---
export const UserStore = {
    async findById(id: string): Promise<User | null> {
        if (!isUsingDatabase()) return memUsers.get(id) || null;
        const row = await queryOne<any>('SELECT * FROM users WHERE id = $1', [id]);
        return row ? mapDbUser(row) : null;
    },

    async findByEmail(email: string): Promise<User | null> {
        if (!isUsingDatabase()) {
            return Array.from(memUsers.values()).find(u => u.email === email) || null;
        }
        const row = await queryOne<any>('SELECT * FROM users WHERE email = $1', [email]);
        return row ? mapDbUser(row) : null;
    },

    async findByGithubId(githubId: number): Promise<User | null> {
        if (!isUsingDatabase()) {
            return Array.from(memUsers.values()).find(u => u.githubId === githubId) || null;
        }
        const row = await queryOne<any>('SELECT * FROM users WHERE github_id = $1', [githubId]);
        return row ? mapDbUser(row) : null;
    },

    async create(user: User): Promise<User> {
        if (!isUsingDatabase()) {
            memUsers.set(user.id, user);
            return user;
        }
        await execute(
            `INSERT INTO users (id, email, username, password_hash, organization_id, github_id, access_token, avatar_url)
             VALUES ($1, $2, $3, $4, $5, $6, $7, $8)`,
            [user.id, user.email, user.username, user.passwordHash, user.organizationId, user.githubId, user.accessToken, user.avatarUrl]
        );
        return user;
    },

    async update(id: string, updates: Partial<User>): Promise<void> {
        if (!isUsingDatabase()) {
            const existing = memUsers.get(id);
            if (existing) memUsers.set(id, { ...existing, ...updates });
            return;
        }
        const fields: string[] = [];
        const values: any[] = [];
        let i = 1;

        if (updates.username !== undefined) { fields.push(`username = $${i++}`); values.push(updates.username); }
        if (updates.accessToken !== undefined) { fields.push(`access_token = $${i++}`); values.push(updates.accessToken); }
        if (updates.avatarUrl !== undefined) { fields.push(`avatar_url = $${i++}`); values.push(updates.avatarUrl); }
        if (updates.githubId !== undefined) { fields.push(`github_id = $${i++}`); values.push(updates.githubId); }

        if (fields.length > 0) {
            values.push(id);
            await execute(`UPDATE users SET ${fields.join(', ')} WHERE id = $${i}`, values);
        }
    }
};

// --- Organizations ---
export const OrgStore = {
    async findById(id: string): Promise<Organization | null> {
        if (!isUsingDatabase()) return memOrganizations.get(id) || null;
        const row = await queryOne<any>('SELECT * FROM organizations WHERE id = $1', [id]);
        return row ? { id: row.id, name: row.name, members: [] } : null;
    },

    async create(org: Organization): Promise<Organization> {
        if (!isUsingDatabase()) {
            memOrganizations.set(org.id, org);
            return org;
        }
        await execute('INSERT INTO organizations (id, name) VALUES ($1, $2)', [org.id, org.name]);
        return org;
    },

    async findByName(name: string): Promise<Organization | null> {
        if (!isUsingDatabase()) {
            return Array.from(memOrganizations.values()).find(o => o.name.includes(name)) || null;
        }
        const row = await queryOne<any>('SELECT * FROM organizations WHERE name ILIKE $1', [`%${name}%`]);
        return row ? { id: row.id, name: row.name, members: [] } : null;
    }
};

// --- Repositories ---
export const RepoStore = {
    async findById(id: string): Promise<Repository | null> {
        if (!isUsingDatabase()) return memRepositories.get(id) || null;
        const row = await queryOne<any>('SELECT * FROM repositories WHERE id = $1', [id]);
        return row ? mapDbRepo(row) : null;
    },

    async findByOrg(orgId: string): Promise<Repository[]> {
        if (!isUsingDatabase()) {
            return Array.from(memRepositories.values()).filter(r => r.organizationId === orgId);
        }
        const rows = await query<any>('SELECT * FROM repositories WHERE organization_id = $1', [orgId]);
        return rows.map(mapDbRepo);
    },

    async findByFullName(fullName: string, orgId: string): Promise<Repository | null> {
        if (!isUsingDatabase()) {
            return Array.from(memRepositories.values()).find(
                r => r.fullName === fullName && r.organizationId === orgId
            ) || null;
        }
        const row = await queryOne<any>(
            'SELECT * FROM repositories WHERE full_name = $1 AND organization_id = $2',
            [fullName, orgId]
        );
        return row ? mapDbRepo(row) : null;
    },

    async findAll(): Promise<Repository[]> {
        if (!isUsingDatabase()) return Array.from(memRepositories.values());
        const rows = await query<any>('SELECT * FROM repositories ORDER BY created_at DESC');
        return rows.map(mapDbRepo);
    },

    async create(repo: Repository): Promise<Repository> {
        if (!isUsingDatabase()) {
            memRepositories.set(repo.id, repo);
            return repo;
        }
        await execute(
            `INSERT INTO repositories (id, organization_id, name, full_name, url, status, api_count, last_scanned, health_score)
             VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)`,
            [repo.id, repo.organizationId, repo.name, repo.fullName, repo.url, repo.scanStatus, repo.apiCount, repo.lastScanned, 85]
        );
        return repo;
    },

    async update(id: string, updates: Partial<Repository>): Promise<void> {
        if (!isUsingDatabase()) {
            const existing = memRepositories.get(id);
            if (existing) memRepositories.set(id, { ...existing, ...updates });
            return;
        }
        const fields: string[] = [];
        const values: any[] = [];
        let i = 1;

        if (updates.scanStatus !== undefined) { fields.push(`status = $${i++}`); values.push(updates.scanStatus); }
        if (updates.apiCount !== undefined) { fields.push(`api_count = $${i++}`); values.push(updates.apiCount); }
        if (updates.lastScanned !== undefined) { fields.push(`last_scanned = $${i++}`); values.push(updates.lastScanned); }

        if (fields.length > 0) {
            values.push(id);
            await execute(`UPDATE repositories SET ${fields.join(', ')} WHERE id = $${i}`, values);
        }
    },

    async delete(id: string): Promise<void> {
        if (!isUsingDatabase()) {
            memRepositories.delete(id);
            return;
        }
        await execute('DELETE FROM endpoints WHERE repository_id = $1', [id]);
        await execute('DELETE FROM repositories WHERE id = $1', [id]);
    }
};

// --- Endpoints ---
export const EndpointStore = {
    async findById(id: string): Promise<Endpoint | null> {
        if (!isUsingDatabase()) return memEndpoints.get(id) || null;
        const row = await queryOne<any>('SELECT * FROM endpoints WHERE id = $1', [id]);
        return row ? mapDbEndpoint(row) : null;
    },

    async findByRepo(repoId: string): Promise<Endpoint[]> {
        if (!isUsingDatabase()) {
            return Array.from(memEndpoints.values()).filter(e => e.repositoryId === repoId);
        }
        const rows = await query<any>('SELECT * FROM endpoints WHERE repository_id = $1', [repoId]);
        return rows.map(mapDbEndpoint);
    },

    async findAll(): Promise<Endpoint[]> {
        if (!isUsingDatabase()) return Array.from(memEndpoints.values());
        const rows = await query<any>('SELECT * FROM endpoints');
        return rows.map(mapDbEndpoint);
    },

    async create(endpoint: Endpoint): Promise<Endpoint> {
        if (!isUsingDatabase()) {
            memEndpoints.set(endpoint.id, endpoint);
            return endpoint;
        }
        await execute(
            `INSERT INTO endpoints (id, repository_id, path, method, summary, description, parameters, request_body, responses, tags, auth_required, source_file)
             VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)`,
            [endpoint.id, endpoint.repositoryId, endpoint.path, endpoint.method, endpoint.summary, endpoint.description,
            JSON.stringify(endpoint.parameters), JSON.stringify(endpoint.requestBody), JSON.stringify(endpoint.responses),
            endpoint.tags, endpoint.authRequired, endpoint.filePath]
        );
        return endpoint;
    },

    async update(id: string, updates: Partial<Endpoint>): Promise<void> {
        if (!isUsingDatabase()) {
            const existing = memEndpoints.get(id);
            if (existing) memEndpoints.set(id, { ...existing, ...updates });
            return;
        }
        const fields: string[] = [];
        const values: any[] = [];
        let i = 1;

        if (updates.summary !== undefined) { fields.push(`summary = $${i++}`); values.push(updates.summary); }
        if (updates.description !== undefined) { fields.push(`description = $${i++}`); values.push(updates.description); }
        if (updates.parameters !== undefined) { fields.push(`parameters = $${i++}`); values.push(JSON.stringify(updates.parameters)); }
        if (updates.requestBody !== undefined) { fields.push(`request_body = $${i++}`); values.push(JSON.stringify(updates.requestBody)); }
        if (updates.responses !== undefined) { fields.push(`responses = $${i++}`); values.push(JSON.stringify(updates.responses)); }
        if (updates.tags !== undefined) { fields.push(`tags = $${i++}`); values.push(updates.tags); }

        if (fields.length > 0) {
            fields.push(`updated_at = CURRENT_TIMESTAMP`);
            values.push(id);
            await execute(`UPDATE endpoints SET ${fields.join(', ')} WHERE id = $${i}`, values);
        }
    },

    async deleteByRepo(repoId: string): Promise<void> {
        if (!isUsingDatabase()) {
            for (const [id, ep] of memEndpoints) {
                if (ep.repositoryId === repoId) memEndpoints.delete(id);
            }
            return;
        }
        await execute('DELETE FROM endpoints WHERE repository_id = $1', [repoId]);
    }
};

// =============================================================================
// MAPPERS (Database rows to TypeScript objects)
// =============================================================================

function mapDbUser(row: any): User {
    return {
        id: row.id,
        email: row.email,
        username: row.username,
        passwordHash: row.password_hash,
        organizationId: row.organization_id,
        githubId: row.github_id,
        accessToken: row.access_token,
        avatarUrl: row.avatar_url
    };
}

function mapDbRepo(row: any): Repository {
    return {
        id: row.id,
        name: row.name,
        fullName: row.full_name,
        url: row.url,
        organizationId: row.organization_id,
        scanStatus: row.status,
        apiCount: row.api_count || 0,
        lastScanned: row.last_scanned,
        createdAt: row.created_at
    };
}

function mapDbEndpoint(row: any): Endpoint {
    return {
        id: row.id,
        repositoryId: row.repository_id,
        path: row.path,
        method: row.method,
        summary: row.summary || '',
        description: row.description || '',
        parameters: row.parameters || [],
        requestBody: row.request_body,
        responses: row.responses || [],
        tags: row.tags || [],
        authRequired: row.auth_required || false,
        filePath: row.source_file || ''
    };
}

// =============================================================================
// INITIALIZATION
// =============================================================================

export async function initializeStore(): Promise<void> {
    await initializeDatabase();

    if (!isUsingDatabase()) {
        seedDemoData();
    }
}

// Demo data seeding for in-memory mode
export function seedDemoData() {
    const demoOrgId = 'org-demo';
    memOrganizations.set(demoOrgId, {
        id: demoOrgId,
        name: 'Demo Organization',
        members: []
    });

    const demoUserId = 'user-1';
    memUsers.set(demoUserId, {
        id: demoUserId,
        email: 'demo@example.com',
        username: 'Demo User',
        githubId: 0,
        accessToken: '',
        organizationId: demoOrgId,
        passwordHash: 'password'
    });

    console.log('🌱 Demo data seeded (User: demo@example.com / password)');
}
