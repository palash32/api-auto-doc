# Contributing to API Auto-Documentation Platform

Thank you for your interest in contributing to the API Auto-Documentation Platform! This document provides guidelines for contributing to the project.

## 🚀 Getting Started

1. **Fork the repository**
2. **Clone your fork**:
   ```bash
   git clone https://github.com/yourusername/api-autodoc-platform.git
   cd api-autodoc-platform
   ```
3. **Set up the development environment**:
   ```bash
   docker-compose up -d
   ```

## 📝 Development Workflow

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following our code style
3. **Write tests** for new functionality
4. **Ensure all tests pass**:
   ```bash
   # Backend
   cd backend && pytest
   
   # Frontend
   cd frontend && npm test
   ```

5. **Commit your changes** using conventional commits:
   ```bash
   git commit -m "feat: add new API parser for Django"
   git commit -m "fix: resolve dependency graph rendering issue"
   git commit -m "docs: update README with deployment instructions"
   ```

6. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Create a Pull Request**

## 🎨 Code Style

### Python (Backend)
- Follow PEP 8
- Use Black for formatting
- Use type hints
- Maximum line length: 100 characters
- Write docstrings for all public functions and classes

### TypeScript (Frontend)
- Follow the Airbnb style guide
- Use ESLint and Prettier
- Use TypeScript strict mode
- Write JSDoc comments for complex functions

## 🧪 Testing

- Write unit tests for business logic
- Write integration tests for API endpoints
- Aim for >80% code coverage
- Test edge cases and error handling

## 📦 Pull Request Guidelines

### PR Title
Use conventional commit format:
- `feat: description` - New feature
- `fix: description` - Bug fix
- `docs: description` - Documentation change
- `style: description` - Code style change
- `refactor: description` - Code refactoring
- `test: description` - Test updates
- `chore: description` - Build/tooling changes

### PR Description
Include:
- **What**: Brief description of changes
- **Why**: Reason for the change
- **How**: Technical approach
- **Testing**: How you tested the changes
- **Screenshots**: For UI changes

### Before Submitting
- [ ] Tests pass locally
- [ ] Code is properly formatted
- [ ] Documentation is updated
- [ ] No merge conflicts
- [ ] PR is focused on a single concern

## 🐛 Reporting Bugs

Use the GitHub issue tracker and include:
- Clear, descriptive title
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, versions, etc.)
- Screenshots or error logs

## 💡 Suggesting Features

Open an issue with:
- Clear use case
- Expected behavior
- Potential implementation approach
- Mockups or diagrams (if UI-related)

## 📜 Code of Conduct

- Be respectful and inclusive
- Welcome newcomers
- Focus on constructive feedback
- Accept criticism gracefully
- Prioritize community well-being

## 📧 Questions?

- Open a GitHub Discussion
- Join our Discord (link-to-discord)
- Email: devs@apidocplatform.com

Thank you for contributing! 🎉
