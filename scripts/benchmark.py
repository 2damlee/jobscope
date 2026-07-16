"""Reproducible latency benchmark for JobScope API endpoints.

Measures p50/p95/p99 latency for the keyword search and recommendation
endpoints against a running instance. Results are printed as a markdown
table row so they can be pasted directly into docs/benchmarks.md.

Usage:
    python scripts/benchmark.py --base-url http://localhost:8000 \
        --requests 200 --concurrency 8 --label "before (120k rows)"
"""

from __future__ import annotations

import argparse
import json
import random
import statistics
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

import httpx

DEFAULT_KEYWORDS = ["python", "data engineer", "backend", "aws", "sql"]


@dataclass
class EndpointResult:
    name: str
    latencies_ms: list[float]
    errors: int

    def percentile(self, p: float) -> float:
        if not self.latencies_ms:
            return float("nan")
        ordered = sorted(self.latencies_ms)
        k = (len(ordered) - 1) * p
        lower = int(k)
        upper = min(lower + 1, len(ordered) - 1)
        return ordered[lower] + (ordered[upper] - ordered[lower]) * (k - lower)

    def summary(self) -> dict:
        return {
            "endpoint": self.name,
            "requests": len(self.latencies_ms),
            "errors": self.errors,
            "p50_ms": round(self.percentile(0.50), 1),
            "p95_ms": round(self.percentile(0.95), 1),
            "p99_ms": round(self.percentile(0.99), 1),
            "mean_ms": (
                round(statistics.fmean(self.latencies_ms), 1)
                if self.latencies_ms
                else float("nan")
            ),
        }


def fetch_sample_job_ids(client: httpx.Client, sample_size: int) -> list[int]:
    """Collect job ids to use as recommendation targets."""
    resp = client.get("/jobs", params={"limit": min(sample_size, 100)})
    resp.raise_for_status()
    payload = resp.json()
    items = payload.get("items", payload if isinstance(payload, list) else [])
    ids = [item["id"] for item in items if "id" in item]
    if not ids:
        raise RuntimeError("No job ids found — is the database populated?")
    return ids


def run_endpoint(
    client: httpx.Client,
    name: str,
    build_request,
    n_requests: int,
    concurrency: int,
    warmup: int = 5,
) -> EndpointResult:
    for _ in range(warmup):
        try:
            client.send(build_request())
        except httpx.HTTPError:
            pass

    latencies: list[float] = []
    errors = 0

    def one_call() -> tuple[float, bool]:
        request = build_request()
        start = time.perf_counter()
        try:
            resp = client.send(request)
            elapsed = (time.perf_counter() - start) * 1000
            return elapsed, resp.status_code >= 400
        except httpx.HTTPError:
            return (time.perf_counter() - start) * 1000, True

    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        for elapsed, failed in pool.map(lambda _: one_call(), range(n_requests)):
            latencies.append(elapsed)
            if failed:
                errors += 1

    return EndpointResult(name=name, latencies_ms=latencies, errors=errors)


def main() -> None:
    parser = argparse.ArgumentParser(description="JobScope API latency benchmark")
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--requests", type=int, default=200)
    parser.add_argument("--concurrency", type=int, default=8)
    parser.add_argument("--label", default="unlabeled run")
    parser.add_argument("--output", default=None, help="Optional JSON output path")
    args = parser.parse_args()

    client = httpx.Client(base_url=args.base_url, timeout=60.0)

    job_ids = fetch_sample_job_ids(client, sample_size=100)
    keywords = DEFAULT_KEYWORDS

    results = [
        run_endpoint(
            client,
            name="GET /jobs?keyword=",
            build_request=lambda: client.build_request(
                "GET", "/jobs", params={"keyword": random.choice(keywords), "limit": 20}
            ),
            n_requests=args.requests,
            concurrency=args.concurrency,
        ),
        run_endpoint(
            client,
            name="GET /jobs/{id}/recommendations",
            build_request=lambda: client.build_request(
                "GET", f"/jobs/{random.choice(job_ids)}/recommendations"
            ),
            n_requests=args.requests,
            concurrency=args.concurrency,
        ),
    ]

    summaries = [r.summary() for r in results]

    print(f"\n## Benchmark: {args.label}")
    print(f"requests={args.requests} concurrency={args.concurrency}\n")
    print("| Endpoint | p50 (ms) | p95 (ms) | p99 (ms) | mean (ms) | errors |")
    print("|---|---|---|---|---|---|")
    for s in summaries:
        print(
            f"| {s['endpoint']} | {s['p50_ms']} | {s['p95_ms']} "
            f"| {s['p99_ms']} | {s['mean_ms']} | {s['errors']} |"
        )

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump({"label": args.label, "results": summaries}, f, indent=2)
        print(f"\nSaved: {args.output}")


if __name__ == "__main__":
    main()