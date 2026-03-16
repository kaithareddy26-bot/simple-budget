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