# Cross-Platform Budgeting Application — Backend

## Architecture

```
app/
  main.py             # FastAPI application factory: middleware, routers, exception handlers
  config.py           # Pydantic Settings — all config via environment variables
  rate_limiter.py     # Shared slowapi Limiter instance
  controllers/        # HTTP layer — request/response only, no business logic
  services/           # Business logic — validation, rules, orchestration
  repositories/       # Data access — SQLAlchemy queries, one class per model
  models/             # SQLAlchemy ORM models
  schemas/            # Pydantic request/response schemas and error codes
  middleware/
    error_handler.py  # All exception handlers → standard error envelope
  utils/
    security.py       # JWT encode/decode, bcrypt helpers
    validators.py     # Month format validation and date-range utilities
```

### Layer contract

| Layer          | Raises                              | Returns                  |
| -------------- | ----------------------------------- | ------------------------ |
| Repository     | `SQLAlchemyError`, `IntegrityError` | ORM model or `None`      |
| Service        | `ValueError("CODE:message")`        | ORM model or scalar      |
| Controller     | delegates to service                | Pydantic response schema |
| Error handlers | —                                   | Standard JSON envelope   |

---

## Quick Start (Docker Compose)

```bash
docker compose up --build       # build and start
docker compose up --build -d    # detached
docker compose logs -f          # stream logs
docker compose down             # stop and remove containers
```

Dependency files:

- `requirements.txt` — runtime dependencies.
- `requirements-dev.txt` — test and development dependencies (extends `requirements.txt`).

---

## Configuration

All settings are read from environment variables (or `.env`).
Override any value by setting the corresponding variable before starting the app.

| Variable                       | Default                                               | Description                                              |
| ------------------------------ | ----------------------------------------------------- | -------------------------------------------------------- |
| `DATABASE_URL`                 | `postgresql://postgres:budget_pass@db:5432/budget_db` | PostgreSQL connection string                             |
| `SECRET_KEY`                   | `dev-only-secret-...`                                 | JWT signing key — **always override in production**      |
| `ACCESS_TOKEN_EXPIRE_MINUTES`  | `30`                                                  | JWT lifetime                                             |
| `RATE_LIMIT_ENABLED`           | `true`                                                | Set `false` in `.env.test` to disable SlowAPI middleware |
| `GLOBAL_RATE_LIMIT`            | `60/minute`                                           | Per-IP global throttle                                   |
| `REGISTER_RATE_LIMIT`          | `3/minute`                                            | Per-IP register throttle                                 |
| `LOGIN_RATE_LIMIT`             | `5/minute`                                            | Per-IP login throttle                                    |
| `REPORT_RATE_LIMIT`            | `10/minute`                                           | Per-IP report throttle                                   |
| `LOGIN_LOCKOUT_MAX_ATTEMPTS`   | `5`                                                   | Failed attempts before lockout                           |
| `LOGIN_LOCKOUT_WINDOW_MINUTES` | `15`                                                  | Lockout and rolling-window duration                      |

Generate a secure `SECRET_KEY`:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## Security Controls

### Authentication

- `POST /api/v1/auth/register` and `POST /api/v1/auth/login` are public.
- All other routes require `Authorization: Bearer <token>`.
- Tokens are signed HS256 JWTs.

### Login abuse protection (two layers)

1. **Per-IP rate limiting** — slowapi enforces `LOGIN_RATE_LIMIT` at the network edge.
2. **Per-email DB lockout** — after `LOGIN_LOCKOUT_MAX_ATTEMPTS` failed attempts the
   `login_attempts` table records a `locked_until` timestamp. The auth service checks
   this before any credential work. State persists across processes and restarts.

### Error response envelope

Every error response uses the same JSON shape:

```json
{
  "timestamp": "2026-03-28T10:21:15Z",
  "status": 429,
  "error": "Too Many Requests",
  "errorCode": "SYS-003",
  "message": "5 per 1 minute",
  "path": "/api/v1/auth/login"
}
```

Common error codes:

| Code       | Meaning                                    |
| ---------- | ------------------------------------------ |
| `VAL-001`  | Invalid input (schema validation failure)  |
| `AUTH-001` | Missing or invalid JWT token               |
| `AUTH-004` | Invalid login credentials / account locked |
| `USR-001`  | Email already registered                   |
| `BUD-001`  | Budget not found                           |
| `BUD-002`  | Budget already exists for this month       |
| `BUD-003`  | Unauthorized access to budget              |
| `SYS-001`  | Internal server error                      |
| `SYS-002`  | Database error                             |
| `SYS-003`  | Rate limit exceeded                        |

---

## Security Controls

### Authentication and Abuse Protection

- Public auth endpoints are `POST /api/v1/auth/register` and `POST /api/v1/auth/login`.
- All other API routes require `Authorization: Bearer <token>`.
- Login abuse protection is enforced at two layers:
	- Per-IP request throttling.
	- Per-email lockout after repeated failed login attempts.

Current defaults (configurable via environment variables):

- `GLOBAL_RATE_LIMIT=60/minute`
- `REGISTER_RATE_LIMIT=3/minute`
- `LOGIN_RATE_LIMIT=5/minute`
- `REPORT_RATE_LIMIT=10/minute`
- `LOGIN_LOCKOUT_MAX_ATTEMPTS=5`
- `LOGIN_LOCKOUT_WINDOW_MINUTES=15`

### Error Response Contract

The backend uses a standard JSON error envelope for API errors, including auth and rate-limit responses:

```json
{
	"timestamp": "2026-03-28T10:21:15Z",
	"status": 429,
	"error": "Too Many Requests",
	"errorCode": "SYS-003",
	"message": "5 per 1 minute",
	"path": "/api/v1/auth/login"
}
```

Common codes:

- `VAL-001`: Invalid input
- `AUTH-001`: Missing or invalid token
- `AUTH-004`: Invalid login credentials
- `SYS-003`: Rate limit exceeded

## Running Tests

Run all tests from the `backend/` directory:

```bash
pytest -q
```

Run only unit tests (no DB required):

```bash
pytest tests/ --ignore=tests/integration -q
```

Run only integration tests (requires Docker DB on port 5433):

```bash
docker compose -f docker-compose.test.yml up -d
pytest tests/integration/ -v -s
```

### Test suite structure

| File                                                 | What it covers                                      |
| ---------------------------------------------------- | --------------------------------------------------- |
| `tests/test_http_controllers.py`                     | Controller layer — all endpoints, auth, validation  |
| `tests/test_error_handlers.py`                       | Error handler middleware and dependency errors      |
| `tests/test_auth_service.py`                         | AuthService unit tests                              |
| `tests/test_budget_service.py`                       | BudgetService unit tests                            |
| `tests/test_expense_service.py`                      | ExpenseService unit tests                           |
| `tests/test_income_service.py`                       | IncomeService unit tests                            |
| `tests/test_report_service.py`                       | ReportService unit tests                            |
| `tests/test_security.py`                             | Rate limiting, CORS, lockout, secret key            |
| `tests/integration/test_integration_auth_lockout.py` | DB-backed lockout (real Postgres)                   |
| `tests/integration/test_integration_errors.py`       | Error contract across all endpoints (real Postgres) |
| `tests/integration/test_integration_happy_paths.py`  | Full CRUD flows (real Postgres)                     |

Current results: **228 tests, 226 passed, 2 skipped** (rate-limit tests skip when `RATE_LIMIT_ENABLED=false`), **93% coverage**.

---

## Database Migrations (Alembic)

Alembic is wired to `app.models.base.Base.metadata` via `migrations/env.py`.

```bash
# Check current revision
ENV_FILE=.env.test python -m alembic current

# Generate migration from model changes
ENV_FILE=.env.test python -m alembic revision --autogenerate -m "describe_change"

# Apply all pending migrations
ENV_FILE=.env.test python -m alembic upgrade head

# Roll back one revision
ENV_FILE=.env.test python -m alembic downgrade -1
```

PowerShell:

```powershell
$env:ENV_FILE = ".env.test"
python -m alembic upgrade head
```

---

## Integration Test Environment

Start the test database:

```bash
docker compose -f docker-compose.test.yml up -d
```

This starts a Postgres 15 instance on port **5433** with `tmpfs` (RAM-only) storage.
The integration conftest loads `.env.test`, clears the settings cache, and uses
transaction-rollback isolation so every test starts with a clean slate.

Set `RATE_LIMIT_ENABLED=false` in `.env.test` (already done) to prevent slowapi
from blocking repeated test requests against the same IP.
