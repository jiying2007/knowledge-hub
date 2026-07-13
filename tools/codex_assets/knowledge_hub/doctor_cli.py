"""Read-only aggregate diagnostics for Knowledge Hub."""

from __future__ import annotations

import argparse
import pathlib
import sys
from typing import Iterable, List, Sequence, Tuple

from .common import run_rtk


def _run_step(root: pathlib.Path, title: str, command: Sequence[str]) -> int:
    print("\n## {}\n".format(title))
    result = run_rtk(root, command, accepted_exit_codes=(0, 1, 2, 3))
    if result["stdout"]:
        print(result["stdout"], end="" if result["stdout"].endswith("\n") else "\n")
    if result["stderr"]:
        print(result["stderr"], file=sys.stderr, end="" if result["stderr"].endswith("\n") else "\n")
    print("\nstatus: {}".format(result["exit_code"]))
    return int(result["exit_code"])


def main(argv: Iterable[str] = ()) -> int:
    values = list(argv) if argv else sys.argv[1:]
    if not values:
        raise SystemExit("Knowledge Hub root argument is required")
    root = pathlib.Path(values.pop(0)).resolve()
    parser = argparse.ArgumentParser(
        description="Run diagnostics, optional item explain/search and optional owner gate board. This command is read-only."
    )
    parser.add_argument("--id", default="")
    parser.add_argument("--owner-gates", default="", metavar="SOURCE_ID")
    args = parser.parse_args(values)
    steps: List[Tuple[str, Sequence[str]]] = [
        ("全仓诊断", ["bash", "tools/knowledge-check.sh", "--dry-run", "--json", "--diagnostics"]),
    ]
    if args.id:
        steps.extend(
            [
                ("条目解释: {}".format(args.id), ["bash", "tools/knowledge-check.sh", "--dry-run", "--json", "--explain", args.id]),
                ("可检索性: {}".format(args.id), ["bash", "tools/knowledge-search.sh", args.id, "--json"]),
            ]
        )
    if args.owner_gates:
        steps.append(
            (
                "Owner gate 看板: {}".format(args.owner_gates),
                ["bash", "tools/knowledge-owner-gates.sh", "--source-id", args.owner_gates],
            )
        )
    final_status = 0
    for title, command in steps:
        status = _run_step(root, title, command)
        if status and not final_status:
            final_status = status
    print("\n## 下一步\n")
    if final_status == 0:
        print("诊断通过。若刚新增或修改条目，仍需确认 registry、核心索引、owner gate 和正文已经人工复核。")
    else:
        print("诊断未通过。优先按 diagnostics.category 的 action_zh 修复；若提供了 --id 或 --owner-gates，再参考 explain、search 和 owner gate 看板定位具体条目。")
    return final_status


if __name__ == "__main__":
    raise SystemExit(main())
