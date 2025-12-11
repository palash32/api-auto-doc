# API Auto-Documentation Platform

> AI-powered API documentation generator that automatically scans repositories, discovers endpoints, and creates beautiful, interactive documentation.

[![CI Status](https://github.com/UniSpark/api-auto-doc/workflows/CI/badge.svg)](https://github.com/UniSpark/api-auto-doc/actions)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

## 🚀 Features

- **🔍 Automatic API Discovery** - Scans GitHub repositories to find API endpoints
- **🤖 AI-Powered Documentation** - Uses Gemini AI to generate comprehensive docs
- **🎨 Beautiful UI** - Glass-morphism design with dark mode
- **🔐 GitHub OAuth** - Secure authentication with GitHub
- **📊 Health Monitoring** - Track API health and uptime
- **🧪 API Playground** - Test endpoints directly in the browser
- **👥 Team Collaboration** - Invite team members and manage access
- **💳 Billing & Plans** - Stripe-ready subscription management

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | Next.js 14, React 18, TypeScript, TailwindCSS |
| **Backend** | FastAPI, Python 3.11, SQLAlchemy, Alembic |
| **Database** | PostgreSQL 16 |
| **AI** | Google Gemini API |
| **Auth** | GitHub OAuth, JWT |
| **Deployment** | Vercel (Frontend), Render (Backend), Neon (Database) |

## 📋 Prerequisites

- Node.js >= 18.x
- Python >= 3.11
- PostgreSQL >= 14.x
- GitHub OAuth App credentials
- Google Gemini API key

## 🚀 Quick Start

### 1. Clone & Install

```bash
# Clone repository
git clone https://github.com/UniSpark/api-auto-doc.git
cd api-auto-doc

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Frontend setup
cd ../frontend
npm install
```

### 2. Configure Environment

```bash
# Backend
cp backend/.env.example backend/.env
# Edit backend/.env with your credentials

# Frontend
cp frontend/.env.example frontend/.env.local
# Edit frontend/.env.local with your API URL
```

### 3. Run Development Servers

```bash
# Terminal 1 - Backend
cd backend
uvicorn app.main:app --reload --port 8000

# Terminal 2 - Frontend
cd frontend
npm run dev
```

Visit http://localhost:3000

## 📁 Project Structure

```
api-auto-doc/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── core/           # Core config, auth, database
│   │   ├── models/         # SQLAlchemy models
│   │   └── services/       # Business logic services
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/               # Next.js frontend
│   ├── src/
│   │   ├── app/           # App router pages
│   │   ├── components/    # React components
│   │   └── lib/           # Utilities
│   ├── package.json
│   └── Dockerfile
│
├── .github/workflows/      # CI/CD pipelines
├── render.yaml            # Render deployment config
└── docker-compose.yml     # Local development
```

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest tests/ -v

# Frontend tests
cd frontend
npm test

# E2E tests
npm run test:e2e
```

## 🚢 Deployment

### Option 1: One-Click Deploy

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/UniSpark/api-auto-doc)

### Option 2: Manual Deployment

See [Deployment Guide](docs/deployment/README.md)

## 📚 Documentation

- [API Reference](docs/api/)
- [Architecture Overview](docs/architecture/)
- [Development Guide](docs/development/)
- [Deployment Guide](docs/deployment/)

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file.

## 🙋 Support

- [Issue Tracker](https://github.com/UniSpark/api-auto-doc/issues)
- [Discussions](https://github.com/UniSpark/api-auto-doc/discussions)

---

Built with ❤️ by UniSpark
