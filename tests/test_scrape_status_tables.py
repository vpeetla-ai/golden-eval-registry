"""Unit tests for status-table scraper (no sibling clones required)."""

from __future__ import annotations

from pathlib import Path

from scripts.scrape_status_tables import scrape


def test_scrape_ok_and_forbidden(tmp_path: Path):
    good = tmp_path / "good" / "README.md"
    good.parent.mkdir()
    good.write_text(
        "## Implementation status\n\n| Component | Status |\n| A | ✅ |\n",
        encoding="utf-8",
    )
    bad = tmp_path / "aegis" / "README.md"
    bad.parent.mkdir()
    bad.write_text(
        "## Implementation status\n\n| ai-content-factory publish | 🟡 Planned |\n",
        encoding="utf-8",
    )
    summary = scrape(
        {
            "good-repo": good,
            "aegisai-enterprise-agent-platform": bad,
            "missing-repo": tmp_path / "nope" / "README.md",
        }
    )
    assert summary["ok"] is False
    assert any("Planned" in f for f in summary["failures"])
    by_repo = {r["repo"]: r for r in summary["results"]}
    assert by_repo["good-repo"]["status"] == "ok"
    assert by_repo["missing-repo"]["status"] == "skip"


def test_scrape_all_ok(tmp_path: Path):
    readme = tmp_path / "README.md"
    readme.write_text("## Implementation Status\n\n🟡 partial\n", encoding="utf-8")
    summary = scrape({"demo": readme})
    assert summary["ok"] is True
    assert summary["results"][0]["yellow_rows"] == 1
