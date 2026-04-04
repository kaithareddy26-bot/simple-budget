# Cross-Platform Budgeting Application Backend

## Quick Start (Docker Compose)

Dependency files:

- `requirements.txt`: runtime dependencies for app containers.
- `requirements-dev.txt`: test and development dependencies (extends `requirements.txt`).

Start (build + run):

```bash
docker compose up --build
```

Start detached:

```bash
docker compose up --build -d
```

Show logs:

```bash
docker compose logs -f
```

Bring down:

```bash
docker compose down
```

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

Run backend tests from the `backend/` directory:

```bash
pytest -q
```

Current consolidated test architecture:

- `tests/test_http_controllers.py`: endpoint/controller coverage for auth, budgets, expenses, incomes, and reports.
- `tests/test_error_handlers.py`: middleware and dependency error handling coverage, including auth failure paths.
- `tests/test_auth_service.py`, `tests/test_budget_service.py`, `tests/test_expense_service.py`, `tests/test_income_service.py`, `tests/test_report_service.py`: service-layer unit tests.