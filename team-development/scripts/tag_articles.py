#!/usr/bin/env python3
"""
articles/ 配下の各記事の frontmatter `published` を読み取り、
macOS Finder タグを付与する。

  published: true  → 緑タグ (Green)
  published: false → 赤タグ (Red)

使い方:
  python3 team-development/scripts/tag_articles.py
"""

import plistlib
import re
import subprocess
import sys
from pathlib import Path

ARTICLES_DIR = Path(__file__).resolve().parents[2] / "articles"

TAG_PUBLISHED = "Green\n2"
TAG_DRAFT = "Red\n6"

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)
PUBLISHED_RE = re.compile(r"^published:\s*(true|false)\s*$", re.MULTILINE)


def read_published(path: Path) -> bool | None:
    text = path.read_text(encoding="utf-8")
    fm_match = FRONTMATTER_RE.search(text)
    if not fm_match:
        return None
    pub_match = PUBLISHED_RE.search(fm_match.group(1))
    if not pub_match:
        return None
    return pub_match.group(1) == "true"


def set_finder_tag(path: Path, tag_value: str) -> None:
    plist_bytes = plistlib.dumps([tag_value], fmt=plistlib.FMT_BINARY)
    subprocess.run(
        [
            "xattr",
            "-wx",
            "com.apple.metadata:_kMDItemUserTags",
            plist_bytes.hex(),
            str(path),
        ],
        check=True,
    )


def main() -> int:
    if sys.platform != "darwin":
        print("このスクリプトは macOS 専用です (Finder タグ)", file=sys.stderr)
        return 1

    if not ARTICLES_DIR.is_dir():
        print(f"articles ディレクトリが見つかりません: {ARTICLES_DIR}", file=sys.stderr)
        return 1

    published_count = 0
    draft_count = 0
    skipped: list[str] = []

    for article in sorted(ARTICLES_DIR.glob("*.md")):
        status = read_published(article)
        if status is None:
            skipped.append(article.name)
            continue
        tag = TAG_PUBLISHED if status else TAG_DRAFT
        set_finder_tag(article, tag)
        marker = "🟢" if status else "🔴"
        print(f"{marker} {article.name}")
        if status:
            published_count += 1
        else:
            draft_count += 1

    print()
    print(f"公開済み: {published_count} 件 / ドラフト: {draft_count} 件")
    if skipped:
        print(f"スキップ ({len(skipped)} 件): {', '.join(skipped)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
