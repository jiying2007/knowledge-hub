"""CLI for privacy-preserving local Knowledge Hub metrics."""

from __future__ import annotations

import argparse
import json
from typing import Iterable

from .common import repository_root
from .metrics import local_metrics


def main(argv: Iterable[str] = ()) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default="")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(list(argv) if argv else None)
    payload = local_metrics(repository_root(args.root))
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
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
