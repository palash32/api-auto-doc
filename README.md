# API Auto-Documentation Platform

> **Automatically discover, document, and monitor all APIs across your organization's codebase in real-time.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Node.js 20+](https://img.shields.io/badge/node-20+-green.svg)](https://nodejs.org/)

## 🎯 Overview

API Auto-Documentation Platform is an enterprise SaaS product that eliminates API sprawl by automatically discovering, documenting, and monitoring APIs across your codebase. Reduce developer time waste by 40% with AI-powered documentation and real-time health monitoring.

### Key Features

- 🔍 **Automatic API Discovery**: Scan GitHub repositories to find all API endpoints
- 🤖 **AI-Powered Documentation**: Generate comprehensive API docs using Google Gemini AI
- 📊 **Real-time Updates**: Automatic re-scanning via GitHub webhooks
- 🔒 **GitHub OAuth**: Secure authentication and repository access
- 🎨 **Beautiful UI**: Apple-inspired design with smooth animations
- ⚡ **Fast & Efficient**: Optimized scanning and caching

## 📚 Documentation

- [Quick Start Guide](docs/QUICK_TEST.md) - Test the platform in 10 minutes
- [Deployment Guide](docs/DEPLOYMENT.md) - Deploy to production
- [Testing Checklist](docs/TESTING_CHECKLIST.md) - Comprehensive testing
- [Production Checklist](docs/PRODUCTION_CHECKLIST.md) - Pre-launch verification

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (Next.js)                       │
│  Dashboard | API Browser | Dependency Graph | Monitoring    │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      │ REST API
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                   Backend (FastAPI)                          │
│  Auth | Repository Scanner | AI Doc Generator | Monitoring   │
└─────────┬───────────┬───────────┬────────────────────────────┘
          │           │           │
          │           │           │
┌─────────▼───┐  ┌────▼─────┐  ┌─▼──────────┐
│  PostgreSQL │  │  Redis   │  │  Celery    │
│  (Database) │  │  (Cache) │  │  (Workers) │
└─────────────┘  └──────────┘  └────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Node.js 20+ (for local frontend development)
- Python 3.11+ (for local backend development)
- Google Gemini API key (free with JIO subscription)
- GitHub OAuth App credentials (optional for repository integration)

### Local Development Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/api-autodoc-platform.git
   cd api-autodoc-platform
   ```

2. **Set up environment variables**:
   ```bash
   # Copy example files
   cp .env.example .env
   cp frontend/.env.example frontend/.env.local
   cp backend/.env.example backend/.env
   
   # Edit .env files with your API keys and credentials
   ```

3. **Start all services with Docker Compose**:
   ```bash
   docker-compose up -d
   ```

4. **Run database migrations**:
   ```bash
   docker-compose exec backend alembic upgrade head
   ```

5. **Access the application**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### Development Without Docker

**Backend**:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend**:
```bash
cd frontend
npm install
npm run dev
```

## 📚 Documentation

- [Architecture Guide](docs/ARCHITECTURE.md)
- [API Reference](docs/API.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Contributing Guidelines](CONTRIBUTING.md)

## 🧪 Testing

**Backend Tests**:
```bash
cd backend
pytest --cov=app tests/
```

**Frontend Tests**:
```bash
cd frontend
npm run test
npm run test:e2e
```

## 🔒 Security

- All sensitive data encrypted at rest and in transit
- OAuth2 authentication with JWT tokens
- Role-based access control (RBAC)
- Regular security audits and dependency updates
- See [SECURITY.md](SECURITY.md) for reporting vulnerabilities

## 📊 Tech Stack

### Frontend
- Next.js 14 (App Router)
- TypeScript
- TailwindCSS + shadcn/ui
- React Query, React Flow, Recharts

### Backend
- Python 3.11+
- FastAPI
- SQLAlchemy + Alembic
- Celery + Redis
- Google Gemini Pro (AI Documentation)

### Infrastructure
- Docker & Kubernetes
- PostgreSQL
- Redis
- GitHub Actions (CI/CD)
- Terraform

## 🗺️ Roadmap

- [x] Phase 1: Foundation & Setup
- [ ] Phase 2: Backend Core Services
- [ ] Phase 3: Frontend Application
- [ ] Phase 4: Monitoring & Health Checks
- [ ] Phase 5: Advanced Features
- [ ] Phase 6: Security & Compliance
- [ ] Phase 7: Testing & QA
- [ ] Phase 8: DevOps & Deployment
- [ ] Phase 9: Go-to-Market
- [ ] Phase 10: Launch

## 💰 Pricing

- **Team Plan**: $49/month per developer (minimum 5 developers)
- **Enterprise Plan**: Custom pricing for 100+ developers

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## 📧 Support

- Email: support@apidocplatform.com
- Documentation: https://docs.apidocplatform.com
- Issues: [GitHub Issues](https://github.com/yourusername/api-autodoc-platform/issues)

---

**Built with ❤️ by developers, for developers.**
