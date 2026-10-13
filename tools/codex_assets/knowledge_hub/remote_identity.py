"""Exact host and repository identity; path-only names are not identities."""

import hashlib
import json
import re
import urllib.parse


def parse_remote(value):
    text = str(value or "").strip()
    scp = re.fullmatch(r"(?:[^/@:\s]+@)?([^/:\s]+):([^\s]+)", text)
    if scp and "://" not in text:
        host, path, port = scp.group(1).lower(), scp.group(2), None
    else:
        parsed = urllib.parse.urlsplit(text)
        if parsed.scheme not in {"https", "ssh", "git", "http"} or not parsed.hostname or parsed.password or parsed.query or parsed.fragment:
            return None
        host, path = parsed.hostname.lower(), parsed.path
        try:
            port = parsed.port
        except ValueError:
            return None
        if port == {"ssh": 22, "https": 443, "http": 80, "git": 9418}.get(parsed.scheme):
            port = None
    path = path.strip("/")
    if path.endswith(".git"):
        path = path[:-4]
    if (not path or len(path) > 256 or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/-]*", path) is None
            or any(part in {"", ".", ".."} for part in path.split("/"))):
        return None
    if host in {"github.com", "gitee.com"} and port is None:
        provider, path = host, path.lower()
    else:
        authority = host + (":" + str(port) if port else "")
        provider = "host-" + hashlib.sha256(authority.encode()).hexdigest()
    return {"provider_id": provider, "repository_path": path}


def identity_key(value):
    if not isinstance(value, dict) or set(value) != {"provider_id", "repository_path"}:
        return ""
    provider, path = value["provider_id"], value["repository_path"]
    if (not isinstance(provider, str) or re.fullmatch(r"github\.com|gitee\.com|host-[a-f0-9]{64}", provider) is None
            or not isinstance(path, str) or not path or len(path) > 256
            or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/-]*", path) is None
            or any(part in {"", ".", ".."} for part in path.split("/"))):
        return ""
    return json.dumps(value, sort_keys=True, separators=(",", ":"))
