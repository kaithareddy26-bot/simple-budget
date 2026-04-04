
# Load Test Report - 2026-03-29T19:27:54.179715

## Test Configuration
- Duration per endpoint: 60s
- Concurrency: 50 concurrent connections
- Host: http://localhost:8000

## Results Summary


### Health Check
- **Total Requests**: 23504
- **Success Rate**: 100.0%
- **Throughput**: 521.53 req/s
- **Response Time (p50 / p95 / p99)**: 88.0 / 223.5 / 368.2 ms
- **Status Codes**: {200: 23504}


### POST /register
- **Total Requests**: 15752
- **Success Rate**: 100.0%
- **Throughput**: 349.48 req/s
- **Response Time (p50 / p95 / p99)**: 131.9 / 189.4 / 235.7 ms
- **Status Codes**: {400: 15752}


### POST /login
- **Total Requests**: 15161
- **Success Rate**: 100.0%
- **Throughput**: 336.20 req/s
- **Response Time (p50 / p95 / p99)**: 138.9 / 222.3 / 370.0 ms
- **Status Codes**: {401: 5, 429: 15156}


## Observations

1. **Throughput**: Measure of requests per second under load.
2. **P95 Latency**: 95th percentile response time (industry standard).
3. **P99 Latency**: 99th percentile response time (outlier response times).

## Recommendations

- If p95 > 500ms or p99 > 2000ms, consider optimizing database queries or adding caching.
- If success rate < 99%, investigate error logs for patterns.
- Monitor rate-limit headers (429 responses) to validate rate limiting is working.

