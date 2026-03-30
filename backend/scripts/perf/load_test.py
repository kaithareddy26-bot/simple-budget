"""
Load Testing Script for Simple Budget API

This script performs load testing on the API endpoints to establish performance baselines.
Metrics: response time (p50, p95, p99), throughput, latency distribution.

Usage:
    python load_test.py [--duration 60] [--concurrency 50] [--host http://localhost:8000]
"""

import asyncio
import time
import json
import sys
from http import HTTPStatus
from statistics import median, stdev
from typing import List, Dict, Optional
from datetime import datetime
from collections import defaultdict

import httpx
from urllib.parse import urljoin


class LoadTestResult:
    """Stores and analyzes load test results."""

    def __init__(self, name: str):
        self.name = name
        self.response_times: List[float] = []
        self.status_codes: Dict[int, int] = defaultdict(int)
        self.errors: List[str] = []
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None

    def add_response(self, response_time: float, status_code: int):
        """Record a successful response."""
        self.response_times.append(response_time)
        self.status_codes[status_code] += 1

    def add_error(self, error: str):
        """Record an error."""
        self.errors.append(error)
        self.status_codes[0] += 1  # 0 for connection/timeout errors

    def set_timing(self, start: float, end: float):
        """Set test duration."""
        self.start_time = start
        self.end_time = end

    def percentile(self, p: float) -> float:
        """Calculate percentile of response times."""
        if not self.response_times:
            return 0
        sorted_times = sorted(self.response_times)
        index = int(len(sorted_times) * (p / 100))
        return sorted_times[min(index, len(sorted_times) - 1)]

    def summary(self) -> Dict:
        """Generate test summary."""
        total_requests = len(self.response_times) + len(self.errors)
        duration = (self.end_time - self.start_time) if self.start_time else 0

        return {
            "endpoint": self.name,
            "total_requests": total_requests,
            "successful": len(self.response_times),
            "failed": len(self.errors),
            "success_rate": f"{100 * len(self.response_times) / total_requests:.1f}%" if total_requests > 0 else "0%",
            "throughput_rps": f"{total_requests / duration:.2f}" if duration > 0 else "0",
            "duration_sec": f"{duration:.1f}",
            "response_time": {
                "min_ms": f"{min(self.response_times)*1000:.1f}" if self.response_times else "0",
                "max_ms": f"{max(self.response_times)*1000:.1f}" if self.response_times else "0",
                "median_ms": f"{median(self.response_times)*1000:.1f}" if self.response_times else "0",
                "p95_ms": f"{self.percentile(95)*1000:.1f}",
                "p99_ms": f"{self.percentile(99)*1000:.1f}",
                "stdev_ms": f"{stdev(self.response_times)*1000:.1f}" if len(self.response_times) > 1 else "0",
            },
            "status_codes": dict(self.status_codes),
        }

    def __str__(self) -> str:
        """Format summary for console output."""
        summary = self.summary()
        return f"""
{summary['endpoint']}:
  Total: {summary['total_requests']} | Success: {summary['successful']} | Failed: {summary['failed']} ({summary['success_rate']})
  Throughput: {summary['throughput_rps']} req/s | Duration: {summary['duration_sec']}s
  Response Time:
    Min: {summary['response_time']['min_ms']}ms
    Median (p50): {summary['response_time']['median_ms']}ms
    P95: {summary['response_time']['p95_ms']}ms
    P99: {summary['response_time']['p99_ms']}ms
    Max: {summary['response_time']['max_ms']}ms
  Status Codes: {summary['status_codes']}
"""


async def load_test_endpoint(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    duration_sec: float,
    concurrency: int,
    headers: Dict = None,
    json_data: Dict = None,
    test_name: str = None,
) -> LoadTestResult:
    """Perform load test on a single endpoint."""

    result = LoadTestResult(test_name or url)
    start_time = time.time()
    result.set_timing(start_time, start_time)

    async def make_request():
        """Make a single request and record result."""
        try:
            request_start = time.time()
            response = await client.request(
                method,
                url,
                headers=headers,
                json=json_data,
                timeout=30.0,
            )
            request_time = time.time() - request_start
            result.add_response(request_time, response.status_code)
        except Exception as e:
            result.add_error(str(e))

    async def worker():
        """Worker task that makes requests continuously."""
        while time.time() - start_time < duration_sec:
            await make_request()
            await asyncio.sleep(0)  # Yield to event loop

    # Create concurrent workers
    tasks = [worker() for _ in range(concurrency)]
    await asyncio.gather(*tasks)

    result.set_timing(start_time, time.time())
    return result


async def run_load_tests(
    host: str = "http://localhost:8000",
    duration_sec: float = 60,
    concurrency: int = 50,
) -> List[LoadTestResult]:
    """Run comprehensive load tests."""

    results = []

    # Test configurations: (method, endpoint, name)
    test_configs = [
        ("GET", "/health", "Health Check"),
        ("POST", "/api/v1/auth/register", "POST /register"),
        ("POST", "/api/v1/auth/login", "POST /login"),
    ]

    print(f"\nStarting Load Tests")
    print(f"  Host: {host}")
    print(f"  Duration: {duration_sec}s per endpoint")
    print(f"  Concurrency: {concurrency} concurrent connections")
    print(f"  Start time: {datetime.now().isoformat()}\n")

    async with httpx.AsyncClient(base_url=host, verify=False) as client:
        for method, endpoint, name in test_configs:
            print(f"Testing {name} ({method} {endpoint})...")

            # Prepare request data
            json_data = None
            if method == "POST":
                if "register" in endpoint:
                    json_data = {
                        "email": f"loadtest-{int(time.time()*1000)}@test.com",
                        "password": "TestPassword123!",
                    }
                elif "login" in endpoint:
                    json_data = {
                        "email": "test@example.com",
                        "password": "password123",
                    }

            result = await load_test_endpoint(
                client,
                method,
                endpoint,
                duration_sec=duration_sec,
                concurrency=concurrency,
                json_data=json_data,
                test_name=name,
            )

            print(result)
            results.append(result)

    return results


def generate_report(results: List[LoadTestResult]) -> str:
    """Generate a formatted load test report."""

    report = f"""
# Load Test Report - {datetime.now().isoformat()}

## Test Configuration
- Duration per endpoint: 60s
- Concurrency: 50 concurrent connections
- Host: http://localhost:8000

## Results Summary

"""

    for result in results:
        summary = result.summary()
        report += f"""
### {summary['endpoint']}
- **Total Requests**: {summary['total_requests']}
- **Success Rate**: {summary['success_rate']}
- **Throughput**: {summary['throughput_rps']} req/s
- **Response Time (p50 / p95 / p99)**: {summary['response_time']['median_ms']} / {summary['response_time']['p95_ms']} / {summary['response_time']['p99_ms']} ms
- **Status Codes**: {summary['status_codes']}

"""

    report += """
## Observations

1. **Throughput**: Measure of requests per second under load.
2. **P95 Latency**: 95th percentile response time (industry standard).
3. **P99 Latency**: 99th percentile response time (outlier response times).

## Recommendations

- If p95 > 500ms or p99 > 2000ms, consider optimizing database queries or adding caching.
- If success rate < 99%, investigate error logs for patterns.
- Monitor rate-limit headers (429 responses) to validate rate limiting is working.

"""

    return report


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Load test Simple Budget API")
    parser.add_argument("--duration", type=float, default=60, help="Test duration per endpoint (seconds)")
    parser.add_argument("--concurrency", type=int, default=50, help="Concurrent connections")
    parser.add_argument("--host", default="http://localhost:8000", help="API host URL")

    args = parser.parse_args()

    try:
        results = asyncio.run(
            run_load_tests(
                host=args.host,
                duration_sec=args.duration,
                concurrency=args.concurrency,
            )
        )

        print("\n" + "=" * 80)
        print("LOAD TEST SUMMARY")
        print("=" * 80)
        for result in results:
            print(result)

        # Save report
        report = generate_report(results)
        report_file = "load_test_results.md"
        with open(report_file, "w") as f:
            f.write(report)
        print(f"\nReport saved to: {report_file}")

    except KeyboardInterrupt:
        print("\nTest interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
