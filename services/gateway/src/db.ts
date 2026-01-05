/**
 * Database Connection and Helpers
 * 
 * PostgreSQL connection for production persistence.
 * Falls back to in-memory store if DATABASE_URL is not set.
 */

import { Pool, PoolClient } from 'pg';

// Create connection pool (only if DATABASE_URL is set)
const pool = process.env.DATABASE_URL
    ? new Pool({
        connectionString: process.env.DATABASE_URL,
        ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : false,
        max: 10,
        idleTimeoutMillis: 30000,
        connectionTimeoutMillis: 2000,
    })
    : null;

// Check if we're using database or in-memory
export const isUsingDatabase = () => !!pool;

// Initialize database schema
export async function initializeDatabase(): Promise<void> {
    if (!pool) {
        console.log('⚠️  No DATABASE_URL - using in-memory store (data will not persist)');
        return;
    }

    const client = await pool.connect();
    try {
        await client.query(`
            CREATE TABLE IF NOT EXISTS organizations (
                id UUID PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS users (
                id UUID PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                username VARCHAR(255),
                password_hash VARCHAR(255),
                organization_id UUID REFERENCES organizations(id),
                github_id INTEGER,
                access_token TEXT,
                avatar_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS repositories (
                id UUID PRIMARY KEY,
                organization_id UUID REFERENCES organizations(id),
                name VARCHAR(255) NOT NULL,
                full_name VARCHAR(255),
                url TEXT,
                status VARCHAR(50) DEFAULT 'pending',
                api_count INTEGER DEFAULT 0,
                last_scanned TIMESTAMP,
                health_score INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS endpoints (
                id UUID PRIMARY KEY,
                repository_id UUID REFERENCES repositories(id),
                path VARCHAR(500) NOT NULL,
                method VARCHAR(10) NOT NULL,
                summary TEXT,
                description TEXT,
                parameters JSONB DEFAULT '[]',
                request_body JSONB,
                responses JSONB DEFAULT '[]',
                tags TEXT[] DEFAULT '{}',
                auth_required BOOLEAN DEFAULT false,
                deprecated BOOLEAN DEFAULT false,
                source_file VARCHAR(500),
                line_number INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
            CREATE INDEX IF NOT EXISTS idx_users_github_id ON users(github_id);
            CREATE INDEX IF NOT EXISTS idx_repositories_org ON repositories(organization_id);
            CREATE INDEX IF NOT EXISTS idx_endpoints_repo ON endpoints(repository_id);
        `);
        console.log('✅ Database schema initialized');
    } catch (error) {
        console.error('❌ Database initialization failed:', error);
        throw error;
    } finally {
        client.release();
    }
}

// Query helper
export async function query<T = any>(text: string, params?: any[]): Promise<T[]> {
    if (!pool) throw new Error('Database not configured');
    const result = await pool.query(text, params);
    return result.rows;
}

// Single row query
export async function queryOne<T = any>(text: string, params?: any[]): Promise<T | null> {
    const rows = await query<T>(text, params);
    return rows[0] || null;
}

// Execute (insert/update/delete)
export async function execute(text: string, params?: any[]): Promise<number> {
    if (!pool) throw new Error('Database not configured');
    const result = await pool.query(text, params);
    return result.rowCount || 0;
}

// Transaction helper
export async function withTransaction<T>(
    callback: (client: PoolClient) => Promise<T>
): Promise<T> {
    if (!pool) throw new Error('Database not configured');
    const client = await pool.connect();
    try {
        await client.query('BEGIN');
        const result = await callback(client);
        await client.query('COMMIT');
        return result;
    } catch (error) {
        await client.query('ROLLBACK');
        throw error;
    } finally {
        client.release();
    }
}

// Graceful shutdown
export async function closeDatabase(): Promise<void> {
    if (pool) {
        await pool.end();
        console.log('Database connection closed');
    }
}

export default pool;
