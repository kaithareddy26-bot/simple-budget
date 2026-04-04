"""
Authenticated load test for business endpoints.

This script uses real API calls against a running backend instance.
It seeds one user, one budget, one income, and multiple expenses,
then benchmarks authenticated endpoints.
"""

import asyncio
import time
from datetime import date
from statistics import median, stdev
from collections import Counter

import httpx


HOST = "http://127.0.0.1:8000"
API = f"{HOST}/api/v1"


def percentile(values, p):
    if not values:
        return 0.0
    vals = sorted(values)
    i = int(len(vals) * (p / 100))
    return vals[min(i, len(vals) - 1)]


class BenchResult:
    def __init__(self, name):
        self.name = name
        self.times = []
        self.codes = Counter()
        self.errors = 0
        self.start = 0.0
        self.end = 0.0

    def add(self, sec, code):
        self.times.append(sec)
        self.codes[code] += 1

    def add_error(self):
        self.errors += 1
        self.codes[0] += 1

    def summary(self):
        total = len(self.times) + self.errors
        dur = max(self.end - self.start, 1e-9)
        return {
            "name": self.name,
            "total": total,
            "ok": len(self.times),
            "errors": self.errors,
            "throughput": total / dur,
            "p50": median(self.times) * 1000 if self.times else 0,
            "p95": percentile(self.times, 95) * 1000,
            "p99": percentile(self.times, 99) * 1000,
            "min": min(self.times) * 1000 if self.times else 0,
            "max": max(self.times) * 1000 if self.times else 0,
            "stdev": stdev(self.times) * 1000 if len(self.times) > 1 else 0,
            "codes": dict(self.codes),
            "duration": dur,
        }


async def request_with_retry(client, method, url, headers=None, body=None, max_retries=5):
    for attempt in range(max_retries + 1):
        r = await client.request(method, url, headers=headers, json=body, timeout=30)
        if r.status_code != 429:
            return r

        if attempt == max_retries:
            return r

        retry_after = r.headers.get("Retry-After")
        delay = float(retry_after) if retry_after and retry_after.isdigit() else min(2 ** attempt, 15)
        await asyncio.sleep(delay)

    return r


async def benchmark(client, name, method, url, headers, n_requests, concurrency=10, body=None):
    res = BenchResult(name)
    sem = asyncio.Semaphore(concurrency)

    async def one_call():
        async with sem:
            t0 = time.time()
            try:
                r = await client.request(method, url, headers=headers, json=body, timeout=30)
                dt = time.time() - t0
                res.add(dt, r.status_code)
            except Exception:
                res.add_error()

    res.start = time.time()
    await asyncio.gather(*[one_call() for _ in range(n_requests)])
    res.end = time.time()
    return res


async def seed_data(client, token):
    headers = {"Authorization": f"Bearer {token}"}
    month = date.today().strftime("%Y-%m")

    # Budget
    r = await request_with_retry(client, "POST", f"{API}/budgets", headers=headers, body={"month": month, "amount": 5000})
    if r.status_code not in (201, 409):
        raise RuntimeError(f"Budget seed failed: {r.status_code} {r.text}")

    # Income
    r = await request_with_retry(
        client,
        "POST",
        f"{API}/incomes",
        headers=headers,
        body={"amount": 3500, "source": "Salary", "date": str(date.today())},
    )
    if r.status_code not in (201, 400):
        raise RuntimeError(f"Income seed failed: {r.status_code} {r.text}")

    # Expenses
    for i in range(12):
        r = await request_with_retry(
            client,
            "POST",
            f"{API}/expenses",
            headers=headers,
            body={
                "amount": 25 + (i % 7),
                "category": f"Category-{i % 5}",
                "date": str(date.today()),
                "note": f"seed-{i}",
            },
        )
        if r.status_code not in (201, 400):
            raise RuntimeError(f"Expense seed failed at {i}: {r.status_code} {r.text}")

    return month


async def main():
    email = f"bizload-{int(time.time()*1000)}@test.com"
    password = "TestPassword123!"
    full_name = "Load Test User"

    async with httpx.AsyncClient(base_url=HOST, verify=False) as client:
        # Register
        r = await client.post(f"{API}/auth/register", json={"email": email, "password": password, "full_name": full_name}, timeout=30)
        if r.status_code != 201:
            raise RuntimeError(f"Register failed: {r.status_code} {r.text}")

        # Login
        r = await client.post(f"{API}/auth/login", json={"email": email, "password": password}, timeout=30)
        if r.status_code != 200:
            raise RuntimeError(f"Login failed: {r.status_code} {r.text}")
        token = r.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        month = await seed_data(client, token)

        # Authenticated business endpoints.
        # Space windows so each endpoint is measured with fresh per-minute rate limits.
        results = []
        results.append(
            await benchmark(
                client,
                "GET /api/v1/budgets/current-month (auth)",
                "GET",
                f"{API}/budgets/current-month",
                headers,
                n_requests=50,
                concurrency=10,
            )
        )
        await asyncio.sleep(65)

        results.append(
            await benchmark(
                client,
                "GET /api/v1/expenses/current-month (auth)",
                "GET",
                f"{API}/expenses/current-month",
                headers,
                n_requests=50,
                concurrency=10,
            )
        )
        await asyncio.sleep(65)

        # Respect reports endpoint limit (10/minute)
        results.append(
            await benchmark(
                client,
                "GET /api/v1/reports/summary (auth, rate-limited)",
                "GET",
                f"{API}/reports/summary?month={month}",
                headers,
                n_requests=10,
                concurrency=1,
            )
        )

    lines = []
    lines.append(f"# Authenticated Endpoint Load Test Results\n")
    lines.append(f"- Host: {HOST}")
    lines.append(f"- Date: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"- Seeded month: {month}")
    lines.append(f"- User: {email}\n")
    lines.append("| Endpoint | Total Requests | Throughput (req/s) | Median (p50) | p95 | p99 | Min | Max | Status Codes |")
    lines.append("|----------|----------------|--------------------|--------------|-----|-----|-----|-----|-------------|")

    for r in results:
        s = r.summary()
        lines.append(
            f"| {s['name']} | {s['total']} | {s['throughput']:.2f} | {s['p50']:.1f}ms | {s['p95']:.1f}ms | {s['p99']:.1f}ms | {s['min']:.1f}ms | {s['max']:.1f}ms | {s['codes']} |"
        )

    report_path = "authenticated_load_test_results.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print("\n".join(lines))
    print(f"\nReport saved to: {report_path}")


if __name__ == "__main__":
    asyncio.run(main())
