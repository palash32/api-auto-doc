/**
 * API Gateway - Main Entry Point
 * 
 * Node.js + Express API Gateway for Auto-Documentation Platform
 * Handles: Authentication, Rate Limiting, Request Routing
 */

import express, { Express, Request, Response, NextFunction } from 'express';
import cors from 'cors';
import helmet from 'helmet';
import morgan from 'morgan';
import rateLimit from 'express-rate-limit';
import dotenv from 'dotenv';
import path from 'path';

// Load environment variables from root .env file
const rootEnvPath = path.resolve(__dirname, '..', '..', '..', '.env');
dotenv.config({ path: rootEnvPath });
console.log(`📁 Loading .env from: ${rootEnvPath}`);

// Default service URLs for local development
const SCANNER_URL = process.env.SCANNER_URL || 'http://localhost:3001';
const AI_SERVICE_URL = process.env.AI_SERVICE_URL || 'http://localhost:3002';

// Import routes
import authRoutes from './routes/auth';
import repositoryRoutes from './routes/repositories';
import endpointRoutes from './routes/endpoints';
import healthRoutes from './routes/health';
import playgroundRoutes from './routes/playground';

// Import middleware
import { errorHandler } from './middleware/errorHandler';
import { requestLogger } from './middleware/requestLogger';

const app: Express = express();
const PORT = process.env.PORT || 8000;

// =============================================================================
// MIDDLEWARE
// =============================================================================

// Security headers
app.use(helmet());

// CORS configuration
app.use(cors({
    origin: process.env.FRONTEND_URL || 'http://localhost:3000',
    credentials: true,
    methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
    allowedHeaders: ['Content-Type', 'Authorization'],
}));

// Body parsing
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true }));

// Request logging
app.use(morgan('combined'));
app.use(requestLogger);

// Rate limiting
const limiter = rateLimit({
    windowMs: 60 * 1000, // 1 minute
    max: 100, // 100 requests per minute
    message: { error: 'Too many requests, please try again later.' },
    standardHeaders: true,
    legacyHeaders: false,
});
app.use('/api/', limiter);

// =============================================================================
// ROUTES
// =============================================================================

// Health check (no auth required)
app.use('/health', healthRoutes);

// API routes
app.use('/api/auth', authRoutes);
app.use('/api/repositories', repositoryRoutes);
app.use('/api', endpointRoutes);
app.use('/api/playground', playgroundRoutes);

// Root endpoint
app.get('/', (req: Request, res: Response) => {
    res.json({
        name: 'API Auto-Documentation Platform',
        version: '2.0.0',
        status: 'operational',
        environment: process.env.NODE_ENV || 'development',
        services: {
            gateway: 'healthy',
            scanner: SCANNER_URL ? 'connected' : 'not configured',
            ai: AI_SERVICE_URL ? 'connected' : 'not configured',
        },
        endpoints: {
            scanner: SCANNER_URL,
            ai: AI_SERVICE_URL,
        }
    });
});

// =============================================================================
// ERROR HANDLING
// =============================================================================

// 404 handler
app.use((req: Request, res: Response) => {
    res.status(404).json({ error: 'Not found', path: req.path });
});

// Global error handler
app.use(errorHandler);

// =============================================================================
// SERVER START
// =============================================================================

app.listen(PORT, () => {
    console.log(`
╔═══════════════════════════════════════════════════════════╗
║         API Auto-Documentation Platform - Gateway          ║
╠═══════════════════════════════════════════════════════════╣
║  🚀 Server:     http://localhost:${PORT}                      ║
║  📚 API Docs:   http://localhost:${PORT}/docs                 ║
║  🔧 Environment: ${(process.env.NODE_ENV || 'development').padEnd(35)}║
╚═══════════════════════════════════════════════════════════╝
  `);
});

export default app;
