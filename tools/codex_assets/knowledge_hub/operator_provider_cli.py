"""Opt-in CLI for bounded read-only Operator provider discovery."""

from __future__ import annotations

import json
from typing import Sequence

from .common import KnowledgeHubError
from .operator_provider_cli_support import (
    build_parser,
    execute_command,
    exit_code,
    render_text,
    validate_args,
)


def main(argv: Sequence[str] = ()) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv else None)
    machine_outputs = validate_args(parser, args)
    try:
        provider, payload = execute_command(
            args,
            machine_outputs=machine_outputs,
        )
    except (KnowledgeHubError, OSError, UnicodeError) as exc:
        parser.error(str(exc))
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        render_text(args, payload)
    return exit_code(args, provider, payload)


if __name__ == "__main__":
    raise SystemExit(main())
