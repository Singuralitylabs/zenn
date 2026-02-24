"""
Stage ④: LLM Pass 1 - トランスクリプトから構造化情報を抽出

Usage:
    python extract_structure.py --transcript output/drafts/transcript.json --output output/drafts/structure.json
"""

import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(Path(__file__).resolve().parent.parent / "config" / ".env")

PROMPT_PATH = Path(__file__).resolve().parent.parent / "templates" / "prompts" / "extraction.txt"


def load_prompt() -> str:
    """抽出プロンプトテンプレートを読み込む。"""
    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read()


def extract_structure(transcript_path: str, output_path: str) -> dict:
    """トランスクリプトから構造化情報を抽出する。"""
    client = OpenAI()
    model = os.getenv("LLM_MODEL", "gpt-4o")

    # トランスクリプト読み込み
    with open(transcript_path, "r", encoding="utf-8") as f:
        transcript_data = json.load(f)

    transcript_text = transcript_data["text"]

    # プロンプト構築
    prompt_template = load_prompt()
    prompt = prompt_template.replace("{transcript}", transcript_text)

    # LLM呼び出し
    print("Extracting structured information...")
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "あなたはチーム開発会議の内容を正確に構造化する専門家です。"
                           "JSONのみを出力してください。説明文は不要です。",
            },
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.1,
    )

    result_text = response.choices[0].message.content
    structure = json.loads(result_text)

    # 出力
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(structure, f, ensure_ascii=False, indent=2)

    print(f"Structure saved: {output_path}")
    print(f"Features found: {len(structure.get('developed_features', []))}")
    print(f"Discussions found: {len(structure.get('meeting_discussions', []))}")
    print(f"Technologies: {len(structure.get('technologies_used', []))}")
    print(f"Code mentions: {len(structure.get('code_mentions', []))}")

    return structure


def main():
    parser = argparse.ArgumentParser(description="トランスクリプトの構造化抽出")
    parser.add_argument("--transcript", required=True,
                        help="トランスクリプトJSONファイルパス")
    parser.add_argument("--output", default="output/drafts/structure.json",
                        help="出力先 (default: output/drafts/structure.json)")
    args = parser.parse_args()

    if not os.path.exists(args.transcript):
        print(f"Error: Transcript file not found: {args.transcript}",
              file=sys.stderr)
        sys.exit(1)

    extract_structure(args.transcript, args.output)


if __name__ == "__main__":
    main()
