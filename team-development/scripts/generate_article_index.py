#!/usr/bin/env python3
"""articles/ の frontmatter から articles-index/ にシンボリックリンクの一覧を再生成する。

リンク名の形式:
  チーム開発記録シリーズ: <番号2桁>_<状態絵文字>_<サブタイトル>.md
  その他の記事:           zz_<状態絵文字>_<タイトル>.md

状態絵文字: published: true → 🟢 / false → 🔴

articles-index/ は生成物のため .gitignore 対象。実体は articles/ 側にあり、
リンクを開けばそのまま実体を編集できる。Zenn は articles/ しか参照しないため
デプロイには影響しない。
"""

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ARTICLES_DIR = REPO_ROOT / "articles"
INDEX_DIR = REPO_ROOT / "articles-index"

SERIES_RE = re.compile(r"^チーム開発記録(\d+)：(.+)$")


def parse_frontmatter(path: Path) -> dict:
    """title と published だけを素朴に読み取る。"""
    meta = {}
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return meta
    for line in lines[1:30]:
        if line.strip() == "---":
            break
        m = re.match(r'^title:\s*"(.*)"\s*$', line)
        if m:
            meta["title"] = m.group(1)
        m = re.match(r"^published:\s*(true|false)\s*$", line)
        if m:
            meta["published"] = m.group(1) == "true"
    return meta


def sanitize(name: str) -> str:
    """ファイル名に使えない文字を全角に置き換える。"""
    return name.replace("/", "／").replace(":", "：").strip()


def main() -> int:
    if not ARTICLES_DIR.is_dir():
        print(f"articles/ が見つかりません: {ARTICLES_DIR}", file=sys.stderr)
        return 1

    INDEX_DIR.mkdir(exist_ok=True)
    # 既存のシンボリックリンクのみ削除して作り直す（通常ファイルには触れない）
    for entry in INDEX_DIR.iterdir():
        if entry.is_symlink():
            entry.unlink()

    count = 0
    for md in sorted(ARTICLES_DIR.glob("*.md")):
        meta = parse_frontmatter(md)
        title = meta.get("title")
        if not title:
            continue
        mark = "🟢" if meta.get("published") else "🔴"
        m = SERIES_RE.match(title)
        if m:
            link_name = f"{int(m.group(1)):02d}_{mark}_{sanitize(m.group(2))}.md"
        else:
            link_name = f"zz_{mark}_{sanitize(title)}.md"
        link = INDEX_DIR / link_name
        if link.exists() or link.is_symlink():
            # タイトル重複時は記事IDを付けて衝突回避
            link = INDEX_DIR / f"{link_name[:-3]}_{md.stem}.md"
        link.symlink_to(Path("..") / "articles" / md.name)
        count += 1

    print(f"articles-index/ を再生成しました（{count}件）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
