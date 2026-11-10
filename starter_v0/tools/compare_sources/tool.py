from __future__ import annotations

from typing import Any
from tools._shared import err
from tools.research_utils import canonical_url, item_list


def compare_sources(items: list[dict[str, Any]]) -> dict[str, Any]:
    try:
        rows = item_list(items)
        if len(rows) < 2:
            raise ValueError("Provide at least two source items")
        groups: dict[str, list[str]] = {}
        for row in rows:
            summary = row.get("summary")
            if not isinstance(summary, str) or not summary.strip():
                raise ValueError("Every source needs a nonempty summary")
            url = canonical_url(row.get("url"))
            key = " ".join(summary.casefold().split())
            urls = groups.setdefault(key, [])
            if url not in urls:
                urls.append(url)
        return {"tool": "compare_sources", "groups": [
                    {"normalized_summary": text, "urls": urls} for text, urls in groups.items()],
                "distinct_summaries": len(groups),
                "note": "Exact normalized text comparison; differing summaries are not proof of contradiction."}
    except Exception as exc:
        return err("compare_sources", exc)
