from __future__ import annotations

from typing import Any
from tools._shared import err
from tools.research_utils import canonical_url, item_list


def source_audit(items: list[dict[str, Any]]) -> dict[str, Any]:
    try:
        rows = item_list(items)
        issues = []
        valid = 0
        for index, row in enumerate(rows):
            if not row.get("url"):
                issues.append({"index": index, "issue": "missing_url"})
                continue
            try:
                canonical_url(row["url"])
            except ValueError:
                issues.append({"index": index, "issue": "invalid_url"})
                continue
            valid += 1
            if not row.get("title"):
                issues.append({"index": index, "issue": "missing_title"})
        return {"tool": "source_audit", "item_count": len(rows), "valid_url_count": valid,
                "issues": issues, "ready": bool(rows) and not issues,
                "note": "Checks citation completeness only; does not verify claims or fetch URLs."}
    except Exception as exc:
        return err("source_audit", exc)
