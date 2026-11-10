from __future__ import annotations

from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


def item_list(items: Any) -> list[dict[str, Any]]:
    if not isinstance(items, list) or any(not isinstance(x, dict) for x in items):
        raise ValueError("items must be an array of objects")
    return items


def canonical_url(url: Any) -> str:
    if not isinstance(url, str):
        raise ValueError("url must be a string")
    parsed = urlsplit(url.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("url must be an absolute HTTP(S) URL without credentials")
    port = parsed.port
    host = parsed.hostname.lower()
    if ":" in host:
        host = "[" + host + "]"
    if port and (parsed.scheme, port) not in {("https", 443), ("http", 80)}:
        host += ":" + str(port)
    query = urlencode(sorted((k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=True)
                             if not k.lower().startswith("utm_") and k.lower() not in {"fbclid", "gclid"}))
    return urlunsplit((parsed.scheme, host, parsed.path.rstrip("/"), query, ""))
