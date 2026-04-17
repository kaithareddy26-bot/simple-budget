#!/usr/bin/env python3
"""
Deployment smoke test — Sprint 5.

Validates the minimum set of API contracts that must hold after every
deployment. Run this against a live stack (local Docker Compose or staging)
before declaring a release candidate healthy.

Usage:
    # Against local Docker Compose stack
    python scripts/smoke_test.py

    # Against a remote host
    BASE_URL=https://your-staging-host python scripts/smoke_test.py

Exit codes:
    0  all checks passed
    1  one or more checks failed
"""

import os
import sys
import json
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000").rstrip("/")
_PASS = "\033[32mPASS\033[0m"
_FAIL = "\033[31mFAIL\033[0m"
_results: list[tuple[str, bool, str]] = []


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _request(method: str, path: str, body=None, token: str | None = None):
    url = BASE_URL + path
    data = json.dumps(body).encode() if body else None
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def check(name: str, condition: bool, detail: str = ""):
    label = _PASS if condition else _FAIL
    print(f"  [{label}] {name}" + (f" — {detail}" if detail else ""))
    _results.append((name, condition, detail))


def section(title: str):
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print(f"{'─' * 60}")


# ---------------------------------------------------------------------------
# Smoke checks
# ---------------------------------------------------------------------------

def check_health():
    section("1. Health check")
    status, body = _request("GET", "/health")
    check("GET /health returns 200", status == 200, f"got {status}")
    check("/health.status == healthy", body.get("status") == "healthy", str(body))


def check_root():
    section("2. Root endpoint")
    status, body = _request("GET", "/")
    check("GET / returns 200", status == 200)
    check("/ contains version", "version" in body)


def check_auth_validation():
    section("3. Auth — schema validation")
    status, body = _request("POST", "/api/v1/auth/register", {"email": "not-an-email", "password": "x"})
    check("Register with invalid email returns 400", status == 400, f"got {status}")
    check("Error envelope has errorCode", "errorCode" in body)

    status, body = _request("POST", "/api/v1/auth/login", {})
    check("Login with empty body returns 400", status == 400, f"got {status}")


def check_no_token_returns_401():
    section("4. Auth — protected endpoints require token")
    for path in ["/api/v1/expenses/current-month", "/api/v1/budgets/current-month"]:
        status, body = _request("GET", path)
        check(f"GET {path} without token → 401", status == 401, f"got {status}")
        check(f"  envelope shape valid", all(k in body for k in ("timestamp", "status", "errorCode", "path")))


def check_e2e_flow():
    section("5. End-to-end: register → login → budget → expense → summary")

    # Use a unique email per run so repeated smoke tests don't collide
    ts = int(time.time())
    email = f"smoke_{ts}@example.com"
    password = "SmokeTest123"
    month = datetime.now(timezone.utc).strftime("%Y-%m")

    status, body = _request("POST", "/api/v1/auth/register",
                             {"email": email, "password": password, "full_name": "Smoke Test"})
    check("Register new user → 201", status == 201, f"got {status}")
    if status != 201:
        check("(E2E aborted — register failed)", False)
        return

    status, body = _request("POST", "/api/v1/auth/login",
                             {"email": email, "password": password})
    check("Login → 200 with access_token", status == 200 and "access_token" in body, f"got {status}")
    if status != 200:
        return
    token = body["access_token"]

    status, body = _request("POST", "/api/v1/budgets",
                             {"month": month, "amount": "2000.00"}, token=token)
    check(f"Create budget for {month} → 201", status == 201, f"got {status}")

    status, body = _request("POST", "/api/v1/expenses",
                             {"amount": "50.00", "category": "Transport",
                              "date": f"{month}-01", "note": "smoke"}, token=token)
    check("Add expense → 201", status == 201, f"got {status}")

    status, body = _request("GET", f"/api/v1/reports/summary?month={month}", token=token)
    check("Monthly summary → 200", status == 200, f"got {status}")
    if status == 200:
        check("Summary.totalExpenses == 50.0",
              float(body.get("totalExpenses", -1)) == 50.0,
              f"got {body.get('totalExpenses')}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print(f"\nSmoke test target: {BASE_URL}")
    print(f"Started: {datetime.now(timezone.utc).isoformat()}Z")

    check_health()
    check_root()
    check_auth_validation()
    check_no_token_returns_401()
    check_e2e_flow()

    total = len(_results)
    passed = sum(1 for _, ok, _ in _results if ok)
    failed = total - passed

    print(f"\n{'═' * 60}")
    print(f"  Results: {passed}/{total} passed", end="")
    if failed:
        print(f", {failed} FAILED")
    else:
        print(" — all checks passed")
    print(f"{'═' * 60}\n")

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()