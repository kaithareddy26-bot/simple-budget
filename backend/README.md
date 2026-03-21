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

## Running Tests

Run backend tests from the `backend/` directory:

```bash
pytest -q
```

Current consolidated test architecture:

- `tests/test_http_controllers.py`: endpoint/controller coverage for auth, budgets, expenses, incomes, and reports.
- `tests/test_error_handlers.py`: middleware and dependency error handling coverage, including auth failure paths.
- `tests/test_auth_service.py`, `tests/test_budget_service.py`, `tests/test_expense_service.py`, `tests/test_income_service.py`, `tests/test_report_service.py`: service-layer unit tests.