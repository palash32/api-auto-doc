# Architecture Overview

## Evolution: Monolith to Microservices

The API Auto-Documentation Platform has evolved from a traditional monolithic architecture to a modern microservices-based approach organized as a monorepo.

### Previous Architecture (Monolith)

```
┌─────────────────────────────────────────────────────┐
│                    MONOLITH                         │
│              (Python/FastAPI + Next.js)             │
│                                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │         Single Backend Service                │  │
│  │  • Authentication                             │  │
│  │  • Repository Scanning                        │  │
│  │  • AI Documentation                          │  │
│  │  • API Gateway                               │  │
│  └──────────────────────────────────────────────┘  │
│                        ↓                           │
│  ┌──────────────────────────────────────────────┐  │
│  │              PostgreSQL                       │  │
│  └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

**Limitations:**
- Single point of failure
- Scaling required scaling entire application
- Technology lock-in (Python for everything)
- Slow build and deployment cycles
- Difficult to optimize performance-critical components

---

### Current Architecture (Microservices)

```
                    ┌─────────────────────────────────────┐
                    │           FRONTEND                  │
                    │        Next.js 14 / React           │
                    │       http://localhost:3000         │
                    └──────────────┬──────────────────────┘
                                   │
                    ┌──────────────▼──────────────────────┐
                    │          API GATEWAY                │
                    │     Node.js / Express / TypeScript  │
                    │       http://localhost:8000         │
                    │                                     │
                    │  ┌─────────────────────────────┐   │
                    │  │ • JWT Authentication        │   │
                    │  │ • Rate Limiting (100/min)   │   │
                    │  │ • Request Logging           │   │
                    │  │ • CORS Management           │   │
                    │  │ • Service Routing           │   │
                    │  └─────────────────────────────┘   │
                    └───────────┬────────────┬───────────┘
                                │            │
           ┌────────────────────▼─┐        ┌─▼───────────────────┐
           │   SCANNER SERVICE    │        │     AI SERVICE      │
           │      Go / Gin        │        │   Python / FastAPI  │
           │ http://localhost:3001│        │http://localhost:3002│
           │                      │        │                     │
           │ ┌──────────────────┐ │        │ ┌─────────────────┐ │
           │ │• Git Cloning     │ │        │ │• Gemini API     │ │
           │ │• File Discovery  │ │        │ │• Doc Generation │ │
           │ │• Pattern Match   │ │        │ │• Endpoint       │ │
           │ │• Endpoint Extract│ │        │ │  Analysis       │ │
           │ └──────────────────┘ │        │ └─────────────────┘ │
           └──────────────────────┘        └─────────────────────┘
```

---

## Microservices Details

### 1. Frontend (Next.js)

| Property | Value |
|----------|-------|
| **Technology** | Next.js 14, React 18, TypeScript |
| **Port** | 3000 |
| **Styling** | TailwindCSS, Glass-morphism |
| **State Management** | React Context, Custom Hooks |

**Key Features:**
- Server-side rendering for SEO
- App Router with dynamic routing
- Real-time updates via polling/WebSocket
- Responsive design with dark mode

### 2. API Gateway (Node.js/Express)

| Property | Value |
|----------|-------|
| **Technology** | Node.js 20, Express, TypeScript |
| **Port** | 8000 |
| **Authentication** | JWT, GitHub OAuth |
| **Rate Limiting** | 100 requests/minute |

**Responsibilities:**
- Authentication & Authorization
- Request routing to services
- Rate limiting & throttling
- Request/response logging
- CORS management
- Error handling & normalization

### 3. Scanner Service (Go)

| Property | Value |
|----------|-------|
| **Technology** | Go 1.21, Gin Framework |
| **Port** | 3001 |
| **Purpose** | Repository scanning & endpoint detection |

**Key Features:**
- **Two-Stage Scanning:** Identifier-first approach
- **Git Integration:** Clone with authentication
- **Multi-Framework:** Python, JS/TS, Go, Java, C#
- **Performance:** Only 5-20% of files processed

**Supported Frameworks:**
```
Python      : FastAPI, Flask, Django
JavaScript  : Express, NestJS, Fastify
TypeScript  : Express, NestJS, Fastify
Go          : Gin, Echo, Fiber, net/http
Java        : Spring Boot
C#          : ASP.NET Web API
```

### 4. AI Service (Python/FastAPI)

| Property | Value |
|----------|-------|
| **Technology** | Python 3.11, FastAPI |
| **Port** | 3002 |
| **AI Provider** | Google Gemini API |

**Responsibilities:**
- Generate API documentation from endpoints
- Analyze endpoint patterns
- Create summaries and descriptions
- Suggest improvements

---

## Communication Patterns

### Synchronous (HTTP/REST)

```
Frontend ──HTTP──> Gateway ──HTTP──> Service
         <──JSON──         <──JSON──
```

All inter-service communication uses RESTful HTTP:
- Frontend calls Gateway exclusively
- Gateway routes to appropriate service
- Services return JSON responses

### Future: Asynchronous (Message Queue)

For long-running operations like large repository scans:
```
Gateway ──publish──> Message Queue ──consume──> Scanner
        <──webhook/poll──────────────────────────┘
```

---

## Data Flow

### Repository Scanning Flow

```
1. User adds repository URL
      │
      ▼
2. Frontend → Gateway: POST /api/repositories
      │
      ▼
3. Gateway → Scanner: POST /scan
      │
      ▼
4. Scanner executes:
   ┌───────────────────────────────────────┐
   │ a. Clone repository (git clone)      │
   │ b. Discover code files               │
   │ c. Pre-filter for API indicators     │
   │ d. Extract endpoints from matches    │
   │ e. Return endpoint list              │
   └───────────────────────────────────────┘
      │
      ▼
5. Gateway stores endpoints & responds
      │
      ▼
6. Frontend displays results
```

### Authentication Flow (GitHub OAuth)

```
1. User clicks "Sign in with GitHub"
      │
      ▼
2. Frontend redirects to: /api/auth/github/login
      │
      ▼
3. Gateway redirects to: github.com/login/oauth/authorize
      │
      ▼
4. User authorizes on GitHub
      │
      ▼
5. GitHub redirects to: /api/auth/github/callback
      │
      ▼
6. Gateway exchanges code for token, creates user, issues JWT
      │
      ▼
7. Redirect to Frontend with JWT token
      │
      ▼
8. Frontend stores token, user is authenticated
```

---

## Deployment Architecture

### Local Development

```bash
# All services run locally
Frontend  : http://localhost:3000
Gateway   : http://localhost:8000
Scanner   : http://localhost:3001
AI        : http://localhost:3002
```

### Production

```
             ┌───────────────────────────────────┐
             │         CLOUDFLARE CDN            │
             │    (SSL termination, caching)     │
             └─────────────────┬─────────────────┘
                               │
          ┌────────────────────┴────────────────────┐
          │                                         │
┌─────────▼──────────┐               ┌──────────────▼──────────┐
│      VERCEL        │               │         RENDER          │
│                    │               │                         │
│  ┌──────────────┐  │               │  ┌─────────────────┐   │
│  │   Frontend   │  │               │  │     Gateway     │   │
│  │   (Next.js)  │  │               │  └─────────────────┘   │
│  └──────────────┘  │               │  ┌─────────────────┐   │
│                    │               │  │     Scanner     │   │
└────────────────────┘               │  └─────────────────┘   │
                                     │  ┌─────────────────┐   │
                                     │  │       AI        │   │
                                     │  └─────────────────┘   │
                                     └────────────┬───────────┘
                                                  │
                                     ┌────────────▼───────────┐
                                     │    NEON / SUPABASE     │
                                     │     (PostgreSQL)       │
                                     └────────────────────────┘
```

---

## Scalability Considerations

### Horizontal Scaling

Each service can be scaled independently:
- **Scanner:** Scale for large repositories
- **AI:** Scale based on documentation demand
- **Gateway:** Scale for high traffic

### Caching Strategy

- **Frontend:** Next.js ISR for static pages
- **Gateway:** Redis for session & rate limiting
- **Scanner:** Cache scan results by commit hash

---

## Benefits of Microservices Architecture

| Benefit | Description |
|---------|-------------|
| **Technology Freedom** | Go for performance-critical scanning, Python for AI, Node.js for API |
| **Independent Scaling** | Scale only the services that need it |
| **Fault Isolation** | Service failure doesn't crash entire system |
| **Faster Deployments** | Deploy individual services independently |
| **Team Autonomy** | Different teams can own different services |
| **Easier Maintenance** | Smaller, focused codebases |

---

## Monorepo Structure

Using a monorepo provides:
- **Shared configuration** (.env, linting rules)
- **Atomic commits** across services
- **Simplified development** (single git clone)
- **Coordinated releases**

```
api-auto-doc/               # Monorepo root
├── frontend/               # Next.js app
├── services/               # All microservices
│   ├── gateway/           # API Gateway
│   ├── scanner/           # Go Scanner
│   └── ai/                # AI Service
├── docs/                   # Shared documentation
├── .env.example           # Shared env template
└── docker-compose.yml     # Orchestration
```
