# Contributing to API Auto-Documentation Platform

Thank you for your interest in contributing! This guide will help you get started.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)
- [Code Style](#code-style)

## 📜 Code of Conduct

This project adheres to a Code of Conduct. By participating, you are expected to uphold this code. Be respectful and inclusive.

## 🛠️ Development Setup

### Prerequisites

- Node.js >= 18.x
- Python >= 3.11
- PostgreSQL >= 14.x
- Git

### Setup Steps

1. **Fork the repository** on GitHub

2. **Clone your fork**
   ```bash
   git clone https://github.com/YOUR_USERNAME/api-auto-doc.git
   cd api-auto-doc
   ```

3. **Add upstream remote**
   ```bash
   git remote add upstream https://github.com/UniSpark/api-auto-doc.git
   ```

4. **Install dependencies**
   ```bash
   # Backend
   cd backend
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt

   # Frontend
   cd ../frontend
   npm install
   ```

5. **Configure environment**
   ```bash
   cp backend/.env.example backend/.env
   cp frontend/.env.example frontend/.env.local
   ```

6. **Run the application**
   ```bash
   # Backend (Terminal 1)
   cd backend && uvicorn app.main:app --reload

   # Frontend (Terminal 2)
   cd frontend && npm run dev
   ```

## 🔧 Making Changes

1. **Sync with upstream**
   ```bash
   git fetch upstream
   git checkout main
   git merge upstream/main
   ```

2. **Create a branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Write clean, documented code
   - Add tests for new features
   - Update documentation if needed

4. **Test your changes**
   ```bash
   # Backend
   cd backend && pytest tests/ -v

   # Frontend
   cd frontend && npm test
   ```

5. **Commit your changes** (see [Commit Guidelines](#commit-guidelines))

6. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Open a Pull Request**

## 📝 Commit Guidelines

We follow [Conventional Commits](https://www.conventionalcommits.org/):

### Types
| Type | Description |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `style` | Formatting, no code change |
| `refactor` | Code refactoring |
| `perf` | Performance improvement |
| `test` | Adding tests |
| `chore` | Maintenance tasks |

### Examples
```bash
feat(api): add endpoint discovery for Express.js
fix(auth): resolve GitHub OAuth token refresh issue
docs(readme): update installation instructions
```

## 🔀 Pull Request Process

1. Fill out the PR template completely
2. Ensure all CI checks pass
3. Request review from maintainers
4. Address feedback promptly
5. Keep PR focused - one feature/fix per PR

## 🎨 Code Style

### Python (Backend)
- Follow PEP 8
- Use type hints
- Maximum line length: 100

### TypeScript (Frontend)
- Use TypeScript strict mode
- Prefer functional components
- Use ESLint + Prettier

## ❓ Questions?

Open a [Discussion](https://github.com/UniSpark/api-auto-doc/discussions)

---

Thank you for contributing! 🎉
