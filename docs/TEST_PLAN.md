# 🧪 Pre-Deployment Test Plan

> **Priority**: Complete all P0 tests before deployment. P1 tests recommended.

---

## P0: Critical Path Tests (MUST PASS)

### TC-001: User Authentication Flow
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Navigate to `/login` | Login page loads |
| 2 | Click "Sign in with GitHub" | Redirects to GitHub OAuth |
| 3 | Authorize app | Redirects back, user logged in |
| 4 | Check header | User avatar/name displayed |
| 5 | Refresh page | Session persists |
| 6 | Click logout | Redirects to login, session cleared |

---

### TC-002: Repository Connection
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Navigate to `/dashboard` | Dashboard loads |
| 2 | Click "Add Repository" | Modal/form appears |
| 3 | Select a GitHub repo | Repo listed in dropdown |
| 4 | Confirm add | Repository appears in list |
| 5 | Check status | Shows "Scanning..." or "Ready" |

---

### TC-003: API Endpoint Discovery
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Wait for scan to complete | Status shows "Ready" |
| 2 | Click on repository | Repository detail page loads |
| 3 | View endpoints list | Endpoints displayed with method badges |
| 4 | Filter by method (GET) | Only GET endpoints shown |
| 5 | Search for endpoint | Matching endpoints appear |

---

### TC-004: API Playground
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Navigate to `/playground` | Playground loads |
| 2 | Select an endpoint | Request form appears |
| 3 | Enter test parameters | Fields accept input |
| 4 | Click "Send Request" | Request executes |
| 5 | View response | Response body, status, time displayed |

---

### TC-005: Documentation Viewer
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Click on endpoint | Detail panel opens |
| 2 | View description | Description shown (or placeholder) |
| 3 | View parameters | Path/query params listed |
| 4 | View response schema | Schema displayed |
| 5 | Copy code example | Copies to clipboard |

---

## P0: Backend API Tests

### TC-006: Core API Endpoints
```bash
# Health check
curl http://localhost:8000/api/health/dashboard

# Auth (with token)
curl http://localhost:8000/api/auth/me -H "Authorization: Bearer TOKEN"

# Repositories
curl http://localhost:8000/api/repositories

# Endpoints
curl http://localhost:8000/api/endpoints?repository_id=XXX
```

---

## P1: Feature Tests

### TC-007: Search & Discovery
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Navigate to `/search` | Search page loads |
| 2 | Enter search query | Results appear (debounced) |
| 3 | Filter by method | Results filtered |
| 4 | Click result | Navigates to endpoint |

---

### TC-008: Analytics Dashboard
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Navigate to `/analytics` | Dashboard loads |
| 2 | View stats cards | Data displayed |
| 3 | Change time range | Data updates |

---

### TC-009: Version History
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Navigate to `/versions` | Timeline loads |
| 2 | Select a version | Changes displayed |
| 3 | Compare versions | Diff view shown |

---

### TC-010: Team Management
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Navigate to `/settings/team` | Team page loads |
| 2 | Invite member | Invitation sent |
| 3 | Change role | Role updated |

---

### TC-011: Billing Page
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Navigate to `/settings/billing` | Plans displayed |
| 2 | Toggle monthly/yearly | Prices update |
| 3 | Select plan | Subscription flow starts |

---

### TC-012: Import/Export
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Navigate to `/import-export` | Page loads |
| 2 | Paste OpenAPI JSON | Content accepted |
| 3 | Click Import | Endpoints imported |
| 4 | Click Export (Markdown) | File downloads |

---

## P1: Edge Cases

### TC-013: Error Handling
| Scenario | Expected |
|----------|----------|
| Invalid repo URL | Error message shown |
| Network failure | Retry option offered |
| 401 Unauthorized | Redirect to login |
| 404 Not Found | Friendly 404 page |
| 500 Server Error | Error boundary catches |

---

### TC-014: Empty States
| Page | Empty State |
|------|-------------|
| Dashboard (no repos) | "Add your first repository" |
| Search (no results) | "No endpoints found" |
| Analytics (no data) | "Start tracking usage" |

---

### TC-015: Responsive Design
| Breakpoint | Test |
|------------|------|
| Desktop (1920px) | Full layout |
| Laptop (1366px) | Sidebar visible |
| Tablet (768px) | Sidebar collapsed |
| Mobile (375px) | Mobile navigation |

---

## P2: Performance Tests

### TC-016: Load Times
| Page | Target |
|------|--------|
| Landing | < 2s |
| Dashboard | < 3s |
| Endpoint list (100+) | < 2s |
| Playground | < 2s |

---

### TC-017: API Response Times
| Endpoint | Target |
|----------|--------|
| GET /repositories | < 500ms |
| GET /endpoints | < 500ms |
| POST /search | < 1s |
| POST /ai/enhance | < 5s |

---

## Test Execution Tracking

| Test ID | Status | Tester | Date | Notes |
|---------|--------|--------|------|-------|
| TC-001 | ⬜ | | | |
| TC-002 | ⬜ | | | |
| TC-003 | ⬜ | | | |
| TC-004 | ⬜ | | | |
| TC-005 | ⬜ | | | |
| TC-006 | ⬜ | | | |
| TC-007 | ⬜ | | | |
| TC-008 | ⬜ | | | |
| TC-009 | ⬜ | | | |
| TC-010 | ⬜ | | | |
| TC-011 | ⬜ | | | |
| TC-012 | ⬜ | | | |
| TC-013 | ⬜ | | | |
| TC-014 | ⬜ | | | |
| TC-015 | ⬜ | | | |
| TC-016 | ⬜ | | | |
| TC-017 | ⬜ | | | |

**Legend**: ⬜ Pending | ✅ Pass | ❌ Fail | ⚠️ Blocked

---

## Quick Smoke Test (5 min)

Run before every deployment:

1. ✅ Homepage loads
2. ✅ Login works
3. ✅ Dashboard shows repos
4. ✅ Can view endpoints
5. ✅ Playground sends request
6. ✅ Logout works
