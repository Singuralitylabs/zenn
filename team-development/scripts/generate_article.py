"""
Stage ⑥: LLM Pass 2 - テンプレート＋構造化データから記事を生成

Usage:
    python generate_article.py --structure output/drafts/structure.json \
                               --code output/drafts/code_snippets.json \
                               --number 4 \
                               --output output/drafts/article_draft.md
"""

import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(Path(__file__).resolve().parent.parent / "config" / ".env")

PROMPT_PATH = Path(__file__).resolve().parent.parent / "templates" / "prompts" / "generation.txt"
FOOTER_PATH = Path(__file__).resolve().parent.parent / "templates" / "footer.md"

# 既存記事のID（前回記事リンク用）
ARTICLE_IDS = {
    1: "0ea64a7c1f221a",
    2: "4cbaefe0e930e2",
    3: "f1ba6f8f0de4ef",
}


def load_prompt() -> str:
    """生成プロンプトテンプレートを読み込む。"""
    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read()


def load_footer() -> str:
    """フッターテンプレートを読み込む。"""
    with open(FOOTER_PATH, "r", encoding="utf-8") as f:
        return f.read()


def format_code_snippets(code_data: dict) -> str:
    """コードスニペットをLLMに渡せる形式にフォーマットする。"""
    parts = []

    for pr in code_data.get("pr_data", []):
        parts.append(f"### PR #{pr['pr_number']}: {pr['title']}")
        if pr.get("body"):
            parts.append(f"説明: {pr['body'][:500]}")
        for f in pr.get("files", [])[:10]:
            parts.append(f"\n#### {f['filename']} ({f['status']})")
            if f.get("patch"):
                parts.append(f"```diff\n{f['patch'][:1500]}\n```")

    for file_info in code_data.get("file_data", []):
        parts.append(f"\n### ファイル: {file_info['path']}")
        content = file_info["content"]
        if len(content) > 3000:
            content = content[:3000] + "\n... (truncated)"
        ext = Path(file_info["path"]).suffix.lstrip(".")
        lang = {"ts": "typescript", "tsx": "typescript", "js": "javascript",
                "jsx": "javascript", "sql": "sql", "py": "python"}.get(ext, ext)
        parts.append(f"```{lang}\n{content}\n```")

    if not parts:
        return "コードスニペットは検出されませんでした。"

    return "\n\n".join(parts)


def generate_article(
    structure_path: str,
    code_path: str,
    article_number: int,
    output_path: str,
) -> str:
    """記事ドラフトを生成する。"""
    client = OpenAI()
    model = os.getenv("LLM_MODEL", "gpt-4o")

    # データ読み込み
    with open(structure_path, "r", encoding="utf-8") as f:
        structure = json.load(f)

    code_data = {"pr_data": [], "file_data": []}
    if code_path and os.path.exists(code_path):
        with open(code_path, "r", encoding="utf-8") as f:
            code_data = json.load(f)

    # 前回記事ID
    prev_number = article_number - 1
    previous_article_id = ARTICLE_IDS.get(prev_number, "")

    # プロンプト構築
    prompt_template = load_prompt()
    prompt = prompt_template.replace("{number}", str(article_number))
    prompt = prompt.replace("{previous_article_id}", previous_article_id)
    prompt = prompt.replace("{structured_data}", json.dumps(structure, ensure_ascii=False, indent=2))
    prompt = prompt.replace("{code_snippets}", format_code_snippets(code_data))

    # LLM呼び出し
    print(f"Generating article #{article_number}...")
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "あなたはシンギュラリティ・ラボのチーム開発記録の技術記事ライターです。"
                           "Markdownで記事を出力してください。"
                           "コードスニペットは提供されたものだけを使用し、独自に生成しないでください。",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
        max_tokens=8000,
    )

    article = response.choices[0].message.content

    # フッター追加
    footer = load_footer()
    full_article = article.rstrip() + "\n\n" + footer

    # 出力
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(full_article)

    print(f"Article draft saved: {output_path}")
    print(f"Total length: {len(full_article)} chars")

    return full_article


def main():
    parser = argparse.ArgumentParser(description="記事ドラフト生成")
    parser.add_argument("--structure", required=True,
                        help="構造化データJSONファイルパス")
    parser.add_argument("--code", default=None,
                        help="コードスニペットJSONファイルパス")
    parser.add_argument("--number", type=int, required=True,
                        help="記事番号 (例: 4)")
    parser.add_argument("--output", default="output/drafts/article_draft.md",
                        help="出力先 (default: output/drafts/article_draft.md)")
    args = parser.parse_args()

    if not os.path.exists(args.structure):
        print(f"Error: Structure file not found: {args.structure}",
              file=sys.stderr)
        sys.exit(1)

    generate_article(args.structure, args.code, args.number, args.output)


if __name__ == "__main__":
    main()
