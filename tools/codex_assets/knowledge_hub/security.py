"""Shared, non-echoing secret detection for Hub gates and exports."""

from __future__ import annotations

import hashlib
import re
from typing import Any, Dict, List, Pattern, Tuple


SCANNER_VERSION = "knowledge-secret-scanner-v2"
_ATTESTATION_CONFIRMATION_TOKEN = re.compile(r"KH-ATTEST-[0-9a-f]{20}")
_PATTERNS: Tuple[Tuple[str, Pattern[str]], ...] = (
    (
        "private-key",
        re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----"),
    ),
    ("aws-access-key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("github-token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b")),
    ("openai-token", re.compile(r"\bsk-[A-Za-z0-9_-]{24,}\b")),
    (
        "credential-assignment",
        re.compile(
            r"(?i)\b(?:api[_-]?key|access[_-]?token|auth[_-]?token|token|password|passwd|secret|cookie)\b"
            r"\s*[:=]\s*['\"]?([^'\"\s]{12,})"
        ),
    ),
)
_PLACEHOLDER_MARKERS = (
    "example",
    "placeholder",
    "redacted",
    "changeme",
    "replace-me",
    "<secret",
    "<token",
    "<password",
    "${",
    "{{",
)


def _is_placeholder(value: str) -> bool:
    lowered = value.casefold()
    if any(marker in lowered for marker in _PLACEHOLDER_MARKERS):
        return True
    stripped = value.strip("*xX_-")
    return not stripped


def _is_attestation_confirmation_token(value: str) -> bool:
    normalized = value.rstrip(".,;:!?)]}")
    return _ATTESTATION_CONFIRMATION_TOKEN.fullmatch(normalized) is not None


def scan_secret_text(text: str) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []
    for name, pattern in _PATTERNS:
        for match in pattern.finditer(text):
            matched = match.group(1) if match.lastindex else match.group(0)
            if name == "credential-assignment":
                if _is_placeholder(matched) or _is_attestation_confirmation_token(matched):
                    continue
            line = text.count("\n", 0, match.start()) + 1
            findings.append(
                {
                    "rule": name,
                    "line": line,
                    "fingerprint": hashlib.sha256(matched.encode("utf-8")).hexdigest()[:16],
                }
            )
    return findings
