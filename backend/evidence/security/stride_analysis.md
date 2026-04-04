# STRIDE Threat Model Analysis - Simple Budget API

**Date**: March 2026 (Sprint 2)  
**System**: Cross-Platform Budgeting Application Backend (FastAPI + PostgreSQL)  
**Scope**: REST API endpoints for authentication, budgets, expenses, incomes, and reports

---

## System Architecture Overview

```
Client (React Native / Web) 
  ↓ HTTPS/TLS
  ↓ REST API (Bearer Token in Authorization header)
FastAPI Backend (Port 8000)
  ├─ Controllers (routers)
  ├─ Service Layer (business logic)
  ├─ Repository Layer (data access)
  └─ Middleware (auth, error handling, rate limiting)
  ↓ TCP/TLS
PostgreSQL Database (Port 5432)
```

**Trust Boundaries:**
1. Client ↔ API (Internet-exposed, HTTPS required)
2. API ↔ Database (Internal, assumed trusted network or TCP/TLS)
3. API ↔ External services (none in current version)

---

## STRIDE Analysis by Threat Category

### 1. **Spoofing** (Impersonation / Authentication)

**Definition**: Attacker pretends to be someone else or something else.

#### 1.1 Spoofing User Identity

**Threat**: Attacker obtains valid JWT token and uses it to make requests as another user.

| Aspect | Details |
|--------|---------|
| **Attack Vector** | JWT token theft (network interception, client storage compromise, token leakage in logs) |
| **Likelihood** | Medium (if HTTPS not enforced or tokens stored insecurely on client) |
| **Impact** | High (attacker can read/modify user's budgets, expenses, incomes) |
| **Evidence** | JWT stored in client state without secure storage; no token expiration documented |
| **Mitigation** (Sprint 2) | See Finding 2 below (hardcoded secrets fixed). Short-lived tokens recommended for Sprint 3. |

#### 1.2 Spoofing API (Man-in-the-Middle)

**Threat**: Attacker intercepts API traffic and impersonates backend.

| Aspect | Details |
|--------|---------|
| **Attack Vector** | Unencrypted HTTP, DNS spoofing, ARP spoofing |
| **Likelihood** | Low (if HTTPS enforced) |
| **Impact** | Critical (attacker gains access to all user data, can modify database) |
| **Mitigation** | Deploy with HTTPS/TLS; document HTTPS as mandatory. Verify in Sprint 3 deployment. |

#### 1.3 API Endpoint Impersonation (Internal)

**Threat**: Attacker accesses internal admin endpoints without authentication.

| Aspect | Details |
|--------|---------|
| **Attack Vector** | Direct HTTP requests to `/admin/*` endpoints if they exist; unauthenticated access |
| **Likelihood** | Medium |
| **Impact** | Critical (admin functionality exposed) |
| **Current Status** | No admin endpoints currently exposed. If added, require explicit role-based access control. |

---

### 2. **Tampering** (Data Modification / Integrity)

**Definition**: Attacker modifies data in transit or at rest.

#### 2.1 Tampering with API Requests (Request Body Manipulation)

**Threat**: Attacker modifies request body (e.g., expense amount, budget limit) during transmission.

| Aspect | Details |
|--------|---------|
| **Attack Vector** | Unencrypted HTTP, MITM attack, compromised client |
| **Likelihood** | Low (mitigated by HTTPS) |
| **Impact** | Medium (attacker could record false expenses, manipulate budgets) |
| **Mitigation** | HTTPS enforced. FastAPI request validation on all endpoints (Pydantic schemas). |

#### 2.2 Tampering with Database Records

**Threat**: Attacker gains direct database access and modifies records (bypassing API validation).

| Aspect | Details |
|--------|---------|
| **Attack Vector** | SQL injection, stolen DB credentials, unknown vulns in SQLAlchemy |
| **Likelihood** | Low (no direct SQL in current codebase, using SQLAlchemy ORM) |
| **Impact** | Critical (all financial data compromised) |
| **Evidence** | Code uses parameterized queries via SQLAlchemy; DB credentials in .env (not in repo). |
| **Mitigation** | Continue using ORM; rotate DB credentials regularly; restrict network access to DB. |

#### 2.3 Tampering with Stored Financial Records

**Threat**: Attacker modifies expense, budget, or income records to manipulate financial view.

| Aspect | Details |
|--------|---------|
| **Attack Vector** | API endpoint abuse (if authorization not enforced on budget/expense endpoints) |
| **Likelihood** | Medium (if endpoint auth middleware is weak or missing) |
| **Impact** | High (user's financial data becomes unreliable) |
| **Evidence** | Controllers validate user_id in request; services check ownership. See Sprint 2 test additions. |
| **Status** | Mitigated: Resource ownership checks in place; see test_http_controllers.py. |

#### 2.4 Tampering with JWT Tokens

**Threat**: Attacker modifies JWT payload (e.g., change user_id claim) without valid signature.

| Aspect | Details |
|--------|---------|
| **Attack Vector** | JWT with weak/hardcoded secret, unsigned JWT accepted, algorithm confusion |
| **Likelihood** | Medium→Low (Finding 2 fixed this in Sprint 2) |
| **Impact** | Critical (full authentication bypass) |
| **Sprint 2 Fix** | Secret key hardening: removed insecure defaults, enforced .env-based config. Changed from default to envvar; validated in config.py. |
| **Residual Risk** | Low if HTTPS enforced and .env secrets are rotated. |

---

### 3. **Repudiation** (Denial of Action / Audit Trail)

**Definition**: Attacker denies performing an action and there's no proof they did.

#### 3.1 Deleted Expenses Not Audited

**Threat**: User deletes an expense, system has no audit trail to prove who deleted what.

| Aspect | Details |
|--------|---------|
| **Attack Vector** | Attacker user deletes expense records; admin cannot prove who or when |
| **Likelihood** | Medium |
| **Impact** | Medium (financial reconciliation issues, dispute resolution difficult) |
| **Current Status** | DELETE endpoints exist but no audit log is kept. |
| **Recommendation** | Implement audit logging (Sprint 3): log user_id, timestamp, action, affected resource_id before deletion. |

#### 3.2 No Login Audit Trail

**Threat**: Attacker logs in as a user; no log records which IP, when, or result.

| Aspect | Details |
|--------|---------|
| **Attack Vector** | Brute-force login attempts, insider threat investigating access |
| **Likelihood** | Medium |
| **Impact** | Medium (incident investigation hindered) |
| **Current Status** | Login lockout is per-email, but no persistent audit log. Lockout state in-memory or Redis (Sprint 3). |
| **Recommendation** | Log authentication events: failed attempts, lockout triggers, successful logins (IP, timestamp). |

---

### 4. **Information Disclosure** (Data Leakage / Privacy)

**Definition**: Attacker reads data they shouldn't have access to.

#### 4.1 Leaking Other Users' Financial Data

**Threat**: Attacker calls `/api/v1/budgets`, receives another user's budgets.

| Aspect | Details |
|--------|---------|
| **Attack Vector** | Missing or weak authorization checks; user_id not validated; direct SQL queries with insufficient WHERE clause |
| **Likelihood** | Medium (common in OWASP Top 10) |
| **Impact** | Critical (privacy violation, financial data of all users exposed) |
| **Evidence** | Sprint 2 test: test_http_controllers.py includes authorization tests. Endpoints check user_id from JWT. |
| **Status** | Mitigated: Authorization middleware and service-layer ownership checks in place. All endpoints require Bearer token + ownership validation (see test_http_controllers.py). |
| **Test Coverage** | Multiple test cases verify `user_id_from_jwt == resource.user_id` check. |

#### 4.2 Leaking Sensitive Data in Error Responses

**Threat**: API returns stack traces, SQL errors, or internal paths in HTTP responses.

| Aspect | Details |
|--------|---------|
| **Attack Vector** | Unhandled exceptions, verbose error logging |
| **Likelihood** | Low→Medium |
| **Impact** | Medium (information gathering for attacker) |
| **Sprint 2 Fix** | Error handler middleware implemented (app/middleware/error_handler.py). Generic error messages returned; stack traces hidden from clients. |
| **Status** | Mitigated: Custom exception handlers catch and sanitize errors. See test_error_handlers.py. |

#### 4.3 JWT Token Leakage in Logs

**Threat**: Full JWT token appears in application logs or access logs.

| Aspect | Details |
|--------|---------|
| **Attack Vector** | Logging request headers verbatim, stack traces in errors |
| **Likelihood** | Medium |
| **Impact** | High (JWT token exposed in log files) |
| **Mitigation** | Do not log Authorization header; mask tokens in logs. Recommend in Sprint 3 deployment guide. |

#### 4.4 Credentials / Secrets in Code or Version Control

**Threat**: Database password, API keys, JWT secret hardcoded or committed.

| Aspect | Details |
|--------|---------|
| **Attack Vector** | Hardcoded secrets, secrets in .env committed to git, decompiled/leaked source code |
| **Likelihood** | Low→Medium |
| **Impact** | Critical (full system compromise) |
| **Sprint 2 Fix** | Secret Key Hardening: removed insecure default JWT secret, enforced .env-based config, updated .gitignore. Documented in Finding 2. |
| **Status** | Mitigated: .env.example provided (no real secrets); .gitignore updated to exclude .env. |
| **Verification** | Run: `git log --all -S "SECRET" -- '*.py' | head -5` to check for past commits. |

#### 4.5 API Responses Contain Unnecessary Data

**Threat**: API returns fields (e.g., password_hash, internal IDs) that shouldn't be exposed.

| Aspect | Details |
|--------|---------|
| **Attack Vector** | Overly permissive schemas in Pydantic responses |
| **Likelihood** | Low |
| **Impact** | Low→Medium (depends on what's exposed) |
| **Current Status** | Schemas in app/schemas/ define explicit response models (TokenResponse, UserResponse, BudgetResponse). Review to ensure sensitive fields are excluded. |
| **Recommendation** | Audit response schemas; ensure password_hash, email (if sensitive), internal audit fields are not in responses. |

---

### 5. **Denial of Service (DoS)** (Resource Exhaustion)

**Definition**: Attacker makes system unavailable to legitimate users.

#### 5.1 Brute-Force Login Attack (HTTP-level DoS)

**Threat**: Attacker sends thousands of login requests to exhaust the service.

| Aspect | Details |
|--------|---------|
| **Attack Vector** | Rapid-fire POST /api/v1/auth/login requests from many IPs |
| **Likelihood** | High (common attack) |
| **Impact** | High (legitimate users cannot log in) |
| **Sprint 2 Fix** | IP-Based Rate Limiting (slowapi): Login endpoint 5 req/min per IP. Per-email lockout after 5 failures in 15 min. |
| **Status** | Mitigated (Finding 1 & 3 addressed). See test_security.py::TestRateLimiting for evidence. |

#### 5.2 Expensive Database Query / Resource Exhaustion (Logic DoS)

**Threat**: Attacker calls expensive endpoint (e.g., generate large report) repeatedly.

| Aspect | Details |
|--------|---------|
| **Attack Vector** | Repeated requests to `/api/v1/reports/summary` without rate limit |
| **Likelihood** | Medium |
| **Impact** | Medium (database or API server CPU exhausted) |
| **Sprint 2 Fix** | Global rate limit: 60 req/min. Report endpoint: 10 req/min (more restrictive). |
| **Status** | Mitigated: Rate-limit enforced at middleware. See main.py and rate_limiter.py. |

#### 5.3 Large Request Payload DoS

**Threat**: Attacker sends a massive JSON body to exhaust memory or parsing resources.

| Aspect | Details |
|--------|---------|
| **Attack Vector** | POST /api/v1/expenses with 100MB JSON body |
| **Likelihood** | Low |
| **Impact** | Medium (server memory exhausted, process crashed) |
| **Mitigation** | FastAPI/Starlette should have default limits. Configure max_request_size in deployment (not in code). Recommend in Sprint 3 deployment guide. |

#### 5.4 Connection Exhaustion

**Threat**: Attacker opens thousands of connections without completing requests.

| Aspect | Details |
|--------|---------|
| **Attack Vector** | Slowloris, connection pooling attacks |
| **Likelihood** | Low |
| **Impact** | High (server cannot accept new connections) |
| **Mitigation** | Reverse proxy / load balancer should handle (nginx connection limits). Set in deployment, not in app code. |

---

### 6. **Elevation of Privilege** (Unauthorized Access to Higher-Privilege Features)

**Definition**: Attacker gains higher-level permissions than they should have.

#### 6.1 JWT Token Validation Bypass

**Threat**: Attacker forges or modifies JWT token without valid signature; API accepts it.

| Aspect | Details |
|--------|---------|
| **Attack Vector** | Weak secret, algorithm confusion (JWT library accepts "none"), unvalidated token |
| **Likelihood** | Low→Medium (depends on config) |
| **Impact** | Critical (attacker can be any user) |
| **Sprint 2 Fix** | Secret key hardening: enforced strong, environment-based secret. Documented in Finding 2. |
| **Status** | Mitigated: config.py validates SECRET_KEY is set; raises error if missing or default. |

#### 6.2 Missing Admin Endpoint Authorization

**Threat**: Admin endpoint (e.g., DELETE /api/v1/users/{id}) accessible to any authenticated user.

| Aspect | Details |
|--------|---------|
| **Attack Vector** | No role-based access control (RBAC); missing HTTP 403 response |
| **Likelihood** | Medium (common OWASP A01 issue) |
| **Impact** | Critical (attacker deletes any user) |
| **Current Status** | No admin endpoints currently exist. If added, must include role-based auth checks. |
| **Recommendation** | If admin features added: implement role column (user.role = 'admin'/'user'), check in middleware/decorator before calling service. |

#### 6.3 Service-Level Authorization Bypass

**Threat**: Authentication middleware validates JWT, but service layer doesn't re-check user_id ownership.

| Aspect | Details |
|--------|---------|
| **Attack Vector** | Service method called with user_id_A but modifies data for user_id_B; no ownership check |
| **Likelihood** | Medium (depends on code QA) |
| **Impact** | High (unauthorized data modification) |
| **Sprint 2 Test Evidence** | test_http_controllers.py includes tests like `test_budget_not_found_for_other_user` verifying ownership check. |
| **Status** | Mitigated: Service layer checks ownership before returning/modifying resources. All tests pass. |

---

## Summary Risk Matrix

| Finding | Threat Category | Severity (Before Sprint 2) | Sprint 2 Mitigation | Residual Risk |
|---------|-----------------|----------------------------|---------------------|----------------|
| **Finding 1** | Spoofing + DoS | High | Login lockout + rate limiting | Low (assuming DB connectivity) |
| **Finding 2** | Tampering + Spoofing | **Critical** | Secret key hardening (.env-based) | Low (if .env rotated) |
| **Finding 3** | DoS + Information Disclosure | High | Global & endpoint rate limits | Low (with slowapi working) |
| **Finding 4** | Elevation of Privilege (CORS) | Medium | CORS methods restricted | Low |
| **Finding 5** | Scalability / Denial of Service | Medium | In-memory lockout state → Redis (Sprint 3) | Medium (planned Sprint 3) |
| **Audit Logging** | Repudiation | Medium | Not addressed | Medium (Sprint 3 recommended) |
| **Secrets in Logs** | Information Disclosure | Medium | Not addressed | Medium (deployment practice) |

---

## Prioritization & Remediation Plan

### Critical (Fix immediately or before production)
- ✅ **Finding 2 - Hardcoded Secrets** (FIXED Sprint 2): Secret key must be randomized, environment-based, rotated regularly.

### High (Fix in Sprint 3)
- ✅ **Finding 1 - Login Brute-Force** (FIXED Sprint 2): Sliding-window lockout + rate limiting implemented.
- ✅ **Finding 3 - API Rate Limiting** (FIXED Sprint 2): Global + endpoint-specific limits applied.
- ⏳ **Audit Logging** (Sprint 3): Log authentication events, data modifications, deletions.
- ⏳ **Redis Migration** (Sprint 3): Lockout state to Redis for distributed system support.

### Medium (Fix in Sprint 3 or later)
- ⏳ **Token Expiration Strategy** (Sprint 3): Implement short-lived tokens + refresh token mechanism.
- ⏳ **Secrets in Logs** (Sprint 3 / Deployment): Configure logging to mask tokens, passwords.
- ⏳ **Max Request Size** (Sprint 3 / Deployment): Configure in nginx/load balancer.

### Low / Accepted Risk
- **No admin endpoints** (current design): No elevation needed. If future feature, implement RBAC at that time.
- **Database network isolation** (infrastructure): Assume trusted network or TCP/TLS in deployment.

---

## Deployment Verification Checklist (For Sprint 3)

- [ ] HTTPS/TLS enforced in production; verify certificate validity
- [ ] JWT secret is NOT hardcoded; verify .env is not in repository, is rotated regularly
- [ ] Rate limiter is functional; test with `ab` or `locust` to confirm 429 responses
- [ ] Error responses are generic (no stack traces, SQL errors, file paths visible)
- [ ] Authorization header not logged in access logs
- [ ] Database credentials not in code or logs
- [ ] Firewall restricts DB access to API server only
- [ ] Run `npm audit` (frontend) and `pip-audit` (backend) before release

---

## References

- OWASP Top 10 2021: https://owasp.org/www-project-top-ten/
- OWASP STRIDE Threat Modeling: https://owasp.org/www-community/attacks/STRIDE_model
- CWE Top 25: https://cwe.mitre.org/top25/
- NIST Secure Software Development Framework: https://csrc.nist.gov/projects/secure-software-development-framework
