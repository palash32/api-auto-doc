# API Auto-Documentation Platform

> AI-powered API documentation generator that automatically scans repositories, discovers endpoints, and creates beautiful, interactive documentation.

[![CI Status](https://github.com/palash32/api-auto-doc/workflows/CI/badge.svg)](https://github.com/palash32/api-auto-doc/actions)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

## 🏗️ Architecture Overview

This platform follows a **microservices architecture** organized as a **monorepo**, enabling independent scaling, technology-specific optimizations, and improved maintainability.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND                                   │
│                         (Next.js 14 / React 18)                        │
│                          http://localhost:3000                          │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                            API GATEWAY                                  │
│                    (Node.js / Express / TypeScript)                     │
│                          http://localhost:8000                          │
│         • Authentication & JWT                                          │
│         • Rate Limiting & Security                                      │
│         • Request Routing                                               │
└────────────┬───────────────────────────────────────────┬────────────────┘
             │                                           │
             ▼                                           ▼
┌────────────────────────────┐              ┌────────────────────────────┐
│      SCANNER SERVICE       │              │        AI SERVICE          │
│     (Go / Gin Framework)   │              │     (Python / FastAPI)     │
│    http://localhost:3001   │              │    http://localhost:3002   │
│                            │              │                            │
│  • Git Repository Cloning  │              │  • Gemini AI Integration   │
│  • Identifier-First Scan   │              │  • Doc Generation          │
│  • Multi-Framework Support │              │  • Endpoint Analysis       │
│  • Pattern Detection       │              │                            │
└────────────────────────────┘              └────────────────────────────┘
```

## 🚀 Features

- **🔍 Automatic API Discovery** - Scans GitHub repositories to find API endpoints
- **⚡ Identifier-First Scanning** - Optimized two-stage scanning (5-20% files processed)
- **🎯 Multi-Framework Support** - Python, JavaScript, TypeScript, Go, Java, C#
- **🤖 AI-Powered Documentation** - Uses Gemini AI to generate comprehensive docs
- **🎨 Beautiful UI** - Glass-morphism design with dark mode
- **🔐 GitHub OAuth** - Secure authentication with GitHub
- **📊 Health Monitoring** - Track API health and uptime
- **🧪 API Playground** - Test endpoints directly in the browser
- **👥 Team Collaboration** - Invite team members and manage access
- **💳 Billing & Plans** - Stripe-ready subscription management

## 🛠️ Tech Stack

### Microservices Architecture

| Service | Technology | Port | Description |
|---------|------------|------|-------------|
| **Frontend** | Next.js 14, React 18, TypeScript, TailwindCSS | 3000 | User interface |
| **Gateway** | Node.js, Express, TypeScript | 8000 | API Gateway, Auth, Routing |
| **Scanner** | Go, Gin Framework | 3001 | Repository scanning, endpoint detection |
| **AI** | Python, FastAPI, Gemini API | 3002 | AI documentation generation |

### Supporting Infrastructure

| Component | Technology |
|-----------|------------|
| **Database** | PostgreSQL 16 |
| **Cache** | Redis |
| **Auth** | GitHub OAuth, JWT |
| **Deployment** | Docker, Docker Compose, Vercel, Render |

## 📁 Project Structure

```
api-auto-doc/
├── frontend/                    # Next.js 14 Frontend
│   ├── src/
│   │   ├── app/                # App router pages
│   │   ├── components/         # React components
│   │   ├── lib/                # Utilities & API clients
│   │   └── hooks/              # Custom React hooks
│   └── package.json
│
├── services/                    # Microservices
│   ├── gateway/                # API Gateway (Node.js/Express)
│   │   ├── src/
│   │   │   ├── routes/         # API route handlers
│   │   │   └── middleware/     # Auth, rate limiting, logging
│   │   └── package.json
│   │
│   ├── scanner/                # Scanner Service (Go)
│   │   ├── cmd/server/         # Entry point
│   │   ├── internal/
│   │   │   ├── scanner/        # Core scanning logic
│   │   │   └── handlers/       # HTTP handlers
│   │   └── go.mod
│   │
│   └── ai/                     # AI Service (Python/FastAPI)
│       ├── app/
│       │   ├── routes/         # API endpoints
│       │   └── services/       # Gemini AI integration
│       └── requirements.txt
│
├── docs/                        # Documentation
│   ├── architecture/           # Architecture docs
│   └── api/                    # API reference
│
├── docker-compose.yml          # Local development orchestration
├── .env.example                # Environment template
└── start.ps1                   # Windows quick start script
```

## 🚀 Quick Start

### Prerequisites

- Node.js >= 20.x
- Go >= 1.21
- Python >= 3.11
- Docker & Docker Compose (optional)
- GitHub OAuth App credentials
- Google Gemini API key

### Option 1: Start All Services Manually

```bash
# Clone repository
git clone https://github.com/palash32/api-auto-doc.git
cd api-auto-doc

# Copy environment file
cp .env.example .env
# Edit .env with your credentials (GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET, GEMINI_API_KEY)

# Terminal 1 - Scanner Service (Go)
cd services/scanner
go build -o scanner.exe ./cmd/server
./scanner.exe
# Running on http://localhost:3001

# Terminal 2 - Gateway Service (Node.js)
cd services/gateway
npm install
npm run dev
# Running on http://localhost:8000

# Terminal 3 - AI Service (Python) [Optional]
cd services/ai
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 3002
# Running on http://localhost:3002

# Terminal 4 - Frontend (Next.js)
cd frontend
npm install
npm run dev
# Running on http://localhost:3000
```

### Option 2: Docker Compose

```bash
# Clone and start all services
git clone https://github.com/palash32/api-auto-doc.git
cd api-auto-doc

# Configure environment
cp .env.example .env
# Edit .env with your credentials

# Start all services
docker-compose up -d

# Access the platform
open http://localhost:3000
```

## 🔍 Scanner Service - Identifier-First Strategy

The Go-based scanner implements an efficient **two-stage scanning** approach:

### Stage 1: Pre-filtering (Fast)
- Quickly scans files for API framework indicators
- Filters out ~80-95% of non-API files
- Supports patterns for multiple frameworks

### Stage 2: Deep Extraction (Targeted)
- Only processes files that passed Stage 1
- Extracts endpoint details: method, path, line number
- Multi-framework regex patterns

### Supported Frameworks

| Language | Frameworks |
|----------|------------|
| **Python** | FastAPI, Flask, Django |
| **JavaScript/TypeScript** | Express, NestJS, Fastify |
| **Go** | Gin, Echo, Fiber, net/http |
| **Java** | Spring Boot (@GetMapping, @PostMapping) |
| **C#** | ASP.NET ([HttpGet], [Route]) |

### Performance

- Typical scan: Only 5-20% of files processed
- Real-time progress logging
- Git repository cloning with authentication

## 🧪 Testing

```bash
# Scanner Service Tests (Go)
cd services/scanner
go test -v ./internal/scanner/...

# Gateway Service Tests (Node.js)
cd services/gateway
npm test

# Frontend Tests (React)
cd frontend
npm test
```

## 🔐 GitHub OAuth Setup

1. Go to https://github.com/settings/developers
2. Create a new OAuth App:
   - **Homepage URL**: `http://localhost:3000`
   - **Callback URL**: `http://localhost:8000/api/auth/github/callback`
3. Copy Client ID and Client Secret to your `.env` file

See [GITHUB_OAUTH_SETUP.md](GITHUB_OAUTH_SETUP.md) for detailed instructions.

## 🚢 Deployment

### Production Architecture

```
                    ┌─────────────────┐
                    │   Cloudflare    │
                    │   (CDN/SSL)     │
                    └────────┬────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
    ┌─────────▼─────────┐      ┌───────────▼──────────┐
    │      Vercel       │      │       Render         │
    │    (Frontend)     │      │     (Services)       │
    └───────────────────┘      │   ┌───────────────┐  │
                               │   │    Gateway    │  │
                               │   ├───────────────┤  │
                               │   │    Scanner    │  │
                               │   ├───────────────┤  │
                               │   │      AI       │  │
                               │   └───────────────┘  │
                               └─────────┬────────────┘
                                         │
                               ┌─────────▼─────────┐
                               │   Neon/Supabase   │
                               │   (PostgreSQL)    │
                               └───────────────────┘
```

### Deploy Commands

```bash
# Frontend to Vercel
cd frontend
vercel deploy --prod

# Services to Render
# Use render.yaml for Blueprint deployment
```

## 📚 Documentation

- [Architecture Overview](docs/ARCHITECTURE.md)
- [Scanner Service Guide](services/scanner/README.md)
- [Gateway Service Guide](services/gateway/README.md)
- [AI Service Guide](services/ai/README.md)
- [GitHub OAuth Setup](GITHUB_OAUTH_SETUP.md)

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file.

## 🙋 Support

- [Issue Tracker](https://github.com/palash32/api-auto-doc/issues)
- [Discussions](https://github.com/palash32/api-auto-doc/discussions)

---

Built with ❤️ - Microservices Architecture v2.0
