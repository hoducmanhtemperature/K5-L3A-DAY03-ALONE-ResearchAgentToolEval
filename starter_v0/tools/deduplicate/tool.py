from __future__ import annotations

from typing import Any
from tools._shared import err
from tools.research_utils import canonical_url, item_list


def deduplicate(items: list[dict[str, Any]]) -> dict[str, Any]:
    try:
        rows = item_list(items)
        seen = set()
        kept = []
        for row in rows:
            if not row.get("url"):
                raise ValueError("Every item needs a source URL")
            key = canonical_url(row["url"])
            if key not in seen:
                seen.add(key)
                kept.append(dict(row, url=key))
        return {"tool": "deduplicate", "items": kept, "removed_count": len(rows) - len(kept)}
    except Exception as exc:
        return err("deduplicate", exc)
