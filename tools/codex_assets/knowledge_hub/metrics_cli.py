"""CLI for privacy-preserving local Knowledge Hub metrics."""

from __future__ import annotations

import argparse
import json
from typing import Iterable

from .common import repository_root, resolve_today
from .metrics import local_metrics, local_metrics_summary


def main(argv: Iterable[str] = ()) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default="")
    output = parser.add_mutually_exclusive_group()
    output.add_argument("--json", action="store_true")
    output.add_argument("--summary-json", action="store_true")
    parser.add_argument("--as-of", default="")
    args = parser.parse_args(list(argv) if argv else None)
    today, _ = resolve_today(args.as_of)
    payload = local_metrics(repository_root(args.root), today)
    if args.json or args.summary_json:
        projection = local_metrics_summary(payload) if args.summary_json else payload
        print(json.dumps(projection, ensure_ascii=False, indent=2))
    else:
        print("# Knowledge Hub Local Metrics")
        print()
        print("- invocations: {}".format(payload["usage"]["invocation_count"]))
        print("- observation_days: {}".format(payload["usage"]["observation_days"]))
        print("- found_rate: {}".format(payload["retrieval"]["found_rate"]))
        print("- performance_status: {}".format(payload["performance"]["status"]))
        print(
            "- performance_samples: search={} context={}".format(
                payload["performance"]["search_sample_count"],
                payload["performance"]["context_sample_count"],
            )
        )
        print("- adoption_ready: {}".format(str(payload["adoption"]["ready"]).lower()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
