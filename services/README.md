# API Auto-Documentation Platform - Services

This folder contains the microservices that power the platform:

## Architecture

```
services/
├── gateway/    # Node.js + Express - API Gateway & Orchestration
├── scanner/    # Go + Gin - High-Performance Discovery Engine
└── ai/         # Python + FastAPI - AI Documentation Service
```

## Service Communication

- **External → Gateway**: REST API over HTTPS
- **Gateway ↔ Services**: gRPC with Protocol Buffers
- **Services → Databases**: Native drivers

## Quick Start

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f gateway
```
