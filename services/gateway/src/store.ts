import { v4 as uuidv4 } from 'uuid';

// Types
export interface User {
    id: string;
    githubId: number;
    username: string;
    description?: string;
    email?: string;
    avatarUrl?: string;
    accessToken: string;
    organizationId: string;
    passwordHash?: string; // For demo login
}


export interface Organization {
    id: string;
    name: string;
    members: string[]; // User IDs
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
    codeSnippet?: string; // Needed for AI generation
}

// Data Stores
export const users = new Map<string, User>();
export const organizations = new Map<string, Organization>();
export const repositories = new Map<string, Repository>();
export const endpoints = new Map<string, Endpoint>();

// Helper to seed demo data
export function seedDemoData() {
    // Demo Org
    const demoOrgId = 'org-demo';
    organizations.set(demoOrgId, {
        id: demoOrgId,
        name: 'Demo Organization',
        members: []
    });

    // Demo Repo
    const demoRepoId = 'demo';
    repositories.set(demoRepoId, {
        id: demoRepoId,
        name: 'demo-api',
        fullName: 'palash32/demo-api',
        url: 'https://github.com/palash32/demo-api',
        organizationId: demoOrgId,
        scanStatus: 'completed',
        apiCount: 2,
        lastScanned: new Date(),
        createdAt: new Date()
    });

    // Demo Endpoints
    endpoints.set('ep-1', {
        id: 'ep-1',
        repositoryId: 'demo',
        path: '/api/users',
        method: 'GET',
        summary: 'List all users',
        description: 'Returns a paginated list of users in the organization',
        tags: ['users'],
        parameters: [{ name: 'page', in: 'query', type: 'integer' }],
        requestBody: null,
        responses: [{ status: 200, description: 'Success' }],
        authRequired: true,
        filePath: 'src/routes/users.ts',
        codeSnippet: 'router.get("/users", (req, res) => { ... })'
    });

    endpoints.set('ep-2', {
        id: 'ep-2',
        repositoryId: 'demo',
        path: '/api/users/{id}',
        method: 'GET',
        summary: 'Get user by ID',
        description: 'Returns details of a specific user',
        tags: ['users'],
        parameters: [{ name: 'id', in: 'path', type: 'string', required: true }],
        requestBody: null,
        responses: [{ status: 200, description: 'Success' }, { status: 404, description: 'Not found' }],
        authRequired: true,
        filePath: 'src/routes/users.ts',
        codeSnippet: 'router.get("/users/:id", (req, res) => { ... })'
    });

    // Demo User
    const demoUserId = 'user-1';
    users.set(demoUserId, {
        id: demoUserId,
        email: 'demo@example.com',
        username: 'Demo User',
        githubId: 0,
        accessToken: '',
        organizationId: demoOrgId,
        passwordHash: 'password' // Mock password
    });

    console.log('🌱 Demo data seeded (User: demo@example.com / password)');
}
