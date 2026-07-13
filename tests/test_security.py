from tools.codex_assets.knowledge_hub.security import scan_secret_text


def test_secret_scanner_detects_credentials_without_echoing_value():
    value = "this-is-a-real-looking-password"
    findings = scan_secret_text("password={}".format(value))
    assert findings
    assert value not in str(findings)
    assert findings[0]["rule"] == "credential-assignment"


def test_secret_scanner_ignores_explicit_placeholder():
    assert scan_secret_text("token=<token-placeholder>") == []
