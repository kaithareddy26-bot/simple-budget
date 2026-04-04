# Authenticated Endpoint Load Test Results

- Host: http://127.0.0.1:8000
- Date: 2026-03-29 19:39:36
- Seeded month: 2026-03
- User: bizload-1774827430678@test.com

| Endpoint | Total Requests | Throughput (req/s) | Median (p50) | p95 | p99 | Min | Max | Status Codes |
|----------|----------------|--------------------|--------------|-----|-----|-----|-----|-------------|
| GET /api/v1/budgets/current-month (auth) | 50 | 213.31 | 44.3ms | 67.0ms | 68.8ms | 21.4ms | 68.8ms | {200: 50} |
| GET /api/v1/expenses/current-month (auth) | 50 | 198.10 | 47.1ms | 66.3ms | 67.6ms | 22.6ms | 67.6ms | {200: 50} |
| GET /api/v1/reports/summary (auth, rate-limited) | 10 | 110.49 | 8.6ms | 13.6ms | 13.6ms | 7.3ms | 13.6ms | {200: 10} |
