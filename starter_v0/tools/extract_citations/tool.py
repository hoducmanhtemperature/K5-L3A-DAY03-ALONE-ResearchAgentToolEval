from __future__ import annotations

import re
from typing import Any
from tools._shared import err
from tools.research_utils import canonical_url


def extract_citations(text: str) -> dict[str, Any]:
    try:
        if not isinstance(text, str) or not text.strip():
            raise ValueError("text must be a nonempty string")
        urls = []
        for match in re.finditer(r"https?://[^\s<>\[\]\"']+", text):
            url = canonical_url(match.group().rstrip(".,;:!?)"))
            if url not in urls:
                urls.append(url)
        return {"tool": "extract_citations", "urls": urls, "count": len(urls)}
    except Exception as exc:
        return err("extract_citations", exc)
