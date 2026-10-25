"""Exercise the real corpus header gate, without hashing or exporting bodies."""
from pathlib import Path

import pytest


_SAFE_CODES = frozenset({
    "invalid-body-path", "reserved-private-body", "unsupported-safe-file-open",
    "not-a-regular-body", "ambiguous-header-byte-order-mark",
    "header-event-or-alias-budget", "header-depth-budget",
    "header-must-be-a-mapping", "unsupported-header-key", "duplicate-header-key",
    "ambiguous-privacy-value", "unknown-privacy-classification", "first-line-budget",
    "ambiguous-header-delimiter", "header-incomplete-or-over-budget",
})


def _safe_reason(error):
    """Project fixed diagnostic codes only, never exception details or paths."""
    seen = set()
    current = error
    for _ in range(8):
        if current is None or id(current) in seen:
            break
        seen.add(id(current))
        if type(current).__name__ == "BodyPrivacyError" and current.args:
            code = current.args[0]
            if type(code) is str and code in _SAFE_CODES:
                return code
        if type(current).__module__.startswith("yaml."):
            return "invalid-header-yaml"
        current = current.__cause__ or current.__context__
    return "unclassified-privacy-preflight-error"


@pytest.mark.parametrize("code", [
    "duplicate-header-key", "unknown-privacy-classification", "first-line-budget",
    "header-incomplete-or-over-budget", "header-event-or-alias-budget",
])
def test_safe_reason_preserves_only_fixed_codes(code):
    error_type = type("BodyPrivacyError", (ValueError,), {})
    inner = error_type(code)
    outer = RuntimeError("SYNTHETIC_PRIVATE_DETAIL")
    outer.__context__ = inner
    assert _safe_reason(outer) == code


@pytest.mark.parametrize("detail", [
    "SYNTHETIC_PRIVATE_DETAIL", "duplicate-header-key: private/path", "",
])
def test_safe_reason_never_projects_arbitrary_exception_text(detail):
    error_type = type("BodyPrivacyError", (ValueError,), {})
    assert _safe_reason(error_type(detail)) == "unclassified-privacy-preflight-error"


def test_safe_reason_limits_exception_cycles():
    error = ValueError("SYNTHETIC_PRIVATE_DETAIL")
    error.__context__ = error
    assert _safe_reason(error) == "unclassified-privacy-preflight-error"


def test_real_corpus_headers_pass_privacy_preflight():
    from tools.codex_assets.knowledge_hub.content_convergence import private_body_paths

    root = Path(__file__).resolve().parents[1]
    paths = []
    excluded = "projects/pcr02-ssc305/archive/engineering-archive/pcr02/decision-index.md"
    for prefix in ("projects", "domains", "governance", "notes"):
        for path in (root / prefix).rglob("*.md"):
            relative = path.relative_to(root).as_posix()
            if path.name != "README.md" and relative != excluded:
                paths.append(relative)
    if not paths or len(paths) > 5000:
        pytest.fail("corpus-privacy-preflight:invalid-scope-budget", pytrace=False)
    reason = None
    try:
        private_body_paths(root, sorted(set(paths)))
    except Exception as error:
        reason = _safe_reason(error)
    # Raise outside the handler so pytest cannot display the original exception.
    if reason is not None:
        pytest.fail("corpus-privacy-preflight:" + reason, pytrace=False)
