"""
Stage ⑤: GitHub APIでコードスニペットを収集

トランスクリプトの構造化データからPR番号やファイル名の言及を検出し、
GitHub APIで実際のコードを取得する。

Usage:
    python fetch_code.py --structure output/drafts/structure.json --output output/drafts/code_snippets.json
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv
from github import Github

load_dotenv(Path(__file__).resolve().parent.parent / "config" / ".env")


def get_github_client() -> Github:
    """GitHub APIクライアントを取得する。"""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("Warning: GITHUB_TOKEN not set. Skipping code fetch.", file=sys.stderr)
        return None
    return Github(token)


def get_repo(client: Github):
    """対象リポジトリを取得する。"""
    repo_name = os.getenv("GITHUB_REPO", "Singuralitylabs/portal-site")
    return client.get_repo(repo_name)


def extract_pr_numbers(code_mentions: list[dict]) -> list[int]:
    """構造化データからPR番号を抽出する。"""
    pr_numbers = set()
    for mention in code_mentions:
        if mention.get("type") == "pr_number":
            value = mention["value"]
            # 数字のみ抽出
            nums = re.findall(r"\d+", str(value))
            for n in nums:
                pr_numbers.add(int(n))
    return sorted(pr_numbers)


def extract_file_paths(code_mentions: list[dict]) -> list[str]:
    """構造化データからファイルパスを抽出する。"""
    paths = set()
    for mention in code_mentions:
        if mention.get("type") == "file_path":
            paths.add(mention["value"])
    return sorted(paths)


def fetch_pr_files(repo, pr_number: int) -> list[dict]:
    """PRの変更ファイルとdiffを取得する。"""
    try:
        pr = repo.get_pull(pr_number)
        files = []
        for f in pr.get_files():
            file_info = {
                "filename": f.filename,
                "status": f.status,
                "additions": f.additions,
                "deletions": f.deletions,
                "patch": f.patch[:2000] if f.patch else None,  # パッチサイズ制限
            }
            files.append(file_info)
        return {
            "pr_number": pr_number,
            "title": pr.title,
            "body": pr.body[:1000] if pr.body else None,
            "files": files,
        }
    except Exception as e:
        print(f"Warning: Could not fetch PR #{pr_number}: {e}", file=sys.stderr)
        return None


def fetch_file_content(repo, file_path: str) -> dict | None:
    """リポジトリからファイル内容を取得する。"""
    try:
        content = repo.get_contents(file_path)
        if content.size > 50000:  # 50KB制限
            print(f"Warning: File too large, skipping: {file_path}",
                  file=sys.stderr)
            return None
        decoded = content.decoded_content.decode("utf-8")
        return {
            "path": file_path,
            "content": decoded,
            "size": content.size,
        }
    except Exception as e:
        print(f"Warning: Could not fetch file {file_path}: {e}", file=sys.stderr)
        return None


def fetch_code_snippets(structure_path: str, output_path: str) -> dict:
    """構造化データを元にコードスニペットを収集する。"""
    # 構造化データ読み込み
    with open(structure_path, "r", encoding="utf-8") as f:
        structure = json.load(f)

    code_mentions = structure.get("code_mentions", [])
    if not code_mentions:
        print("No code mentions found in structure data.")
        result = {"pr_data": [], "file_data": [], "note": "No code mentions detected"}
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        return result

    client = get_github_client()
    if not client:
        result = {"pr_data": [], "file_data": [], "note": "GITHUB_TOKEN not configured"}
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        return result

    repo = get_repo(client)

    # PR情報の取得
    pr_numbers = extract_pr_numbers(code_mentions)
    pr_data = []
    for pr_num in pr_numbers:
        print(f"Fetching PR #{pr_num}...")
        data = fetch_pr_files(repo, pr_num)
        if data:
            pr_data.append(data)

    # ファイル内容の取得
    file_paths = extract_file_paths(code_mentions)
    file_data = []
    for fpath in file_paths:
        print(f"Fetching file: {fpath}...")
        data = fetch_file_content(repo, fpath)
        if data:
            file_data.append(data)

    # developed_features内のcode_referencesも処理
    for feature in structure.get("developed_features", []):
        for ref in feature.get("code_references", []):
            if ref["type"] == "pr" and ref["reference"]:
                nums = re.findall(r"\d+", str(ref["reference"]))
                for n in nums:
                    pr_num = int(n)
                    if pr_num not in [p["pr_number"] for p in pr_data]:
                        print(f"Fetching PR #{pr_num} (from feature refs)...")
                        data = fetch_pr_files(repo, pr_num)
                        if data:
                            pr_data.append(data)

    result = {
        "pr_data": pr_data,
        "file_data": file_data,
    }

    # 出力
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"Code snippets saved: {output_path}")
    print(f"PRs fetched: {len(pr_data)}")
    print(f"Files fetched: {len(file_data)}")

    return result


def main():
    parser = argparse.ArgumentParser(description="GitHub APIでコードスニペット収集")
    parser.add_argument("--structure", required=True,
                        help="構造化データJSONファイルパス")
    parser.add_argument("--output", default="output/drafts/code_snippets.json",
                        help="出力先 (default: output/drafts/code_snippets.json)")
    args = parser.parse_args()

    if not os.path.exists(args.structure):
        print(f"Error: Structure file not found: {args.structure}",
              file=sys.stderr)
        sys.exit(1)

    fetch_code_snippets(args.structure, args.output)


if __name__ == "__main__":
    main()
