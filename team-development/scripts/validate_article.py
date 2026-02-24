"""
Stage ⑦: 自動品質チェック

記事ドラフトの構造・フロントマター・リンク・必須セクションを検証する。

Usage:
    python validate_article.py --article output/drafts/article_draft.md
"""

import argparse
import os
import re
import sys

import frontmatter


REQUIRED_SECTIONS = ["概要", "開発したもの", "会議の様子", "活用した技術", "総括"]

REQUIRED_FRONTMATTER_KEYS = ["title", "emoji", "type", "topics", "published"]

REQUIRED_LINKS = [
    "github.com/Singuralitylabs/portal-site",
    "sinlab.future-tech-association.org/join",
]

REQUIRED_FOOTER_MARKERS = [
    "プログラミングイベントのご案内",
    "GASアプリ開発サービス",
    "シンギュラリティ・ラボのご案内",
]


def validate_frontmatter(post: frontmatter.Post) -> list[str]:
    """フロントマターの検証。"""
    errors = []

    for key in REQUIRED_FRONTMATTER_KEYS:
        if key not in post.metadata:
            errors.append(f"フロントマター: '{key}' が欠落しています")

    if "title" in post.metadata:
        title = post.metadata["title"]
        if not title.startswith("チーム開発記録"):
            errors.append(f"タイトル形式: 'チーム開発記録N：...' の形式ではありません: {title}")

    if "type" in post.metadata:
        if post.metadata["type"] != "tech":
            errors.append(f"type は 'tech' である必要があります: {post.metadata['type']}")

    if "topics" in post.metadata:
        topics = post.metadata["topics"]
        if "チーム開発" not in topics:
            errors.append("topics に 'チーム開発' が含まれていません")

    if "published" in post.metadata:
        if post.metadata["published"] is True:
            errors.append("WARNING: published が true です。レビュー前は false にしてください")

    return errors


def validate_sections(content: str) -> list[str]:
    """必須セクションの検証。"""
    errors = []

    for section in REQUIRED_SECTIONS:
        pattern = rf"^##\s+{re.escape(section)}"
        if not re.search(pattern, content, re.MULTILINE):
            errors.append(f"必須セクション '## {section}' が見つかりません")

    return errors


def validate_links(content: str) -> list[str]:
    """必須リンクの検証。"""
    errors = []

    for link in REQUIRED_LINKS:
        if link not in content:
            errors.append(f"必須リンクが欠落: {link}")

    return errors


def validate_footer(content: str) -> list[str]:
    """フッターの検証。"""
    errors = []

    for marker in REQUIRED_FOOTER_MARKERS:
        if marker not in content:
            errors.append(f"フッター要素が欠落: {marker}")

    return errors


def validate_code_blocks(content: str) -> list[str]:
    """コードブロックの整合性チェック。"""
    warnings = []

    open_blocks = content.count("```")
    if open_blocks % 2 != 0:
        warnings.append("コードブロック(```)の開閉が一致しません")

    return warnings


def validate_todo_placeholders(content: str) -> list[str]:
    """TODOプレースホルダーのリスト。"""
    info = []

    todo_matches = re.findall(r"<!--\s*TODO:.*?-->", content)
    if todo_matches:
        for match in todo_matches:
            info.append(f"TODO: {match}")

    return info


def validate_article(article_path: str) -> dict:
    """記事ドラフトの総合検証。"""
    with open(article_path, "r", encoding="utf-8") as f:
        raw = f.read()

    post = frontmatter.loads(raw)

    results = {
        "errors": [],
        "warnings": [],
        "info": [],
    }

    # フロントマター検証
    results["errors"].extend(validate_frontmatter(post))

    # セクション検証
    results["errors"].extend(validate_sections(post.content))

    # リンク検証
    results["warnings"].extend(validate_links(post.content))

    # フッター検証
    results["errors"].extend(validate_footer(post.content))

    # コードブロック検証
    results["warnings"].extend(validate_code_blocks(post.content))

    # TODOプレースホルダー
    results["info"].extend(validate_todo_placeholders(post.content))

    return results


def print_results(results: dict) -> bool:
    """検証結果を表示する。成功時Trueを返す。"""
    has_errors = len(results["errors"]) > 0

    if results["errors"]:
        print("\n[ERRORS]")
        for e in results["errors"]:
            print(f"  x {e}")

    if results["warnings"]:
        print("\n[WARNINGS]")
        for w in results["warnings"]:
            print(f"  ! {w}")

    if results["info"]:
        print("\n[INFO]")
        for i in results["info"]:
            print(f"  i {i}")

    if not has_errors:
        print("\n[OK] Validation passed.")
    else:
        print(f"\n[FAIL] {len(results['errors'])} error(s) found.")

    return not has_errors


def main():
    parser = argparse.ArgumentParser(description="記事ドラフトの品質チェック")
    parser.add_argument("--article", required=True,
                        help="記事ドラフトのMarkdownファイルパス")
    args = parser.parse_args()

    if not os.path.exists(args.article):
        print(f"Error: Article file not found: {args.article}", file=sys.stderr)
        sys.exit(1)

    results = validate_article(args.article)
    passed = print_results(results)

    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
