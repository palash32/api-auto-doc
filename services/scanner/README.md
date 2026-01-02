# API Discovery Engine (Go Scanner)

High-performance repository scanner for API endpoint detection.

## Features

- 🚀 Written in Go for maximum performance
- 🔍 Regex-based endpoint detection
- 📦 Supports Python, JavaScript/TypeScript, Go, Java
- ⚡ Parallel file processing
- 🐳 Docker-ready

## Supported Frameworks

| Language | Frameworks |
|----------|------------|
| Python | FastAPI, Flask, Django |
| JavaScript | Express.js, Fastify, NestJS |
| Go | Gin, Echo, Fiber |
| Java | Spring Boot |

## Quick Start

```bash
# Development
go run ./cmd/server

# Production
go build -o scanner ./cmd/server
./scanner
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /health | Health check |
| POST | /scan | Start a repository scan |
| GET | /scan/:id | Get scan status |
| GET | /scan/:id/endpoints | Get detected endpoints |

## Example Request

```bash
curl -X POST http://localhost:3001/scan \
  -H "Content-Type: application/json" \
  -d '{"url": "https://github.com/user/repo"}'
```
