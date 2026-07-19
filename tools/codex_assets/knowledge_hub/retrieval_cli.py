"""CLI for the known-answer retrieval benchmark."""

from __future__ import annotations

import argparse
import pathlib

from .common import pretty_json, repository_root
from .retrieval import run_retrieval_benchmark


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="knowledge-retrieval-benchmark.sh", description="Run known-answer top-k retrieval evaluation.")
    parser.add_argument("--cases", default="", help="Optional cases JSON path.")
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--min-hit-rate", type=float, default=0.95)
    parser.add_argument("--min-mrr", type=float, default=0.85)
    parser.add_argument("--max-p95-ms", type=float, default=500.0)
    parser.add_argument("--max-index-preparation-ms", type=float, default=5000.0)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    root = repository_root()
    cases = pathlib.Path(args.cases).expanduser().resolve() if args.cases else None
    payload = run_retrieval_benchmark(
        root,
        cases_path=cases,
        top_k=args.top_k,
        minimum_hit_rate=args.min_hit_rate,
        minimum_mrr=args.min_mrr,
        maximum_p95_ms=args.max_p95_ms,
        maximum_index_preparation_ms=args.max_index_preparation_ms,
    )
    if args.json:
        print(pretty_json(payload))
    else:
        print(
            "{}: cases={} hit_rate={:.1%} mrr={:.3f} p95_ms={} preparation_ms={}".format(
                payload["status"],
                payload["case_count"],
                payload["hit_rate"],
                payload["mrr"],
                payload["latency_ms"]["p95"],
                payload["index_preparation"]["duration_ms"],
            )
        )
    return 0 if payload["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
