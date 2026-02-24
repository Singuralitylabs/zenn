"""
全ステージ統合オーケストレーター

会議動画からZenn記事ドラフトを生成するパイプラインを一括実行する。

Usage:
    python pipeline.py --video ~/Downloads/meeting_20260223.mp4 --number 4
    python pipeline.py --video meeting.mp4 --number 4 --skip-code
    python pipeline.py --transcript output/drafts/transcript.json --number 4  # 文字起こし済みの場合
"""

import argparse
import os
import shutil
import sys
import time
from pathlib import Path

# scriptsディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).resolve().parent))

from transcribe import transcribe
from extract_structure import extract_structure
from fetch_code import fetch_code_snippets
from generate_article import generate_article
from validate_article import validate_article, print_results


ARTICLES_DIR = Path(__file__).resolve().parent.parent.parent / "articles"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output" / "drafts"


def run_pipeline(
    video_path: str | None,
    transcript_path: str | None,
    article_number: int,
    skip_code: bool = False,
    output_dir: str | None = None,
) -> None:
    """パイプライン全体を実行する。"""
    out = Path(output_dir) if output_dir else OUTPUT_DIR
    out.mkdir(parents=True, exist_ok=True)

    start_time = time.time()

    # ──── Stage ②③: 文字起こし ────
    transcript_out = str(out / "transcript.json")
    if transcript_path and os.path.exists(transcript_path):
        print(f"\n{'='*60}")
        print("Stage ②③: Skipping transcription (using provided transcript)")
        print(f"{'='*60}")
        if str(Path(transcript_path).resolve()) != str(Path(transcript_out).resolve()):
            shutil.copy2(transcript_path, transcript_out)
    elif video_path:
        print(f"\n{'='*60}")
        print("Stage ②③: Audio extraction + Whisper transcription")
        print(f"{'='*60}")
        transcribe(video_path, transcript_out)
    else:
        print("Error: Either --video or --transcript is required.", file=sys.stderr)
        sys.exit(1)

    # ──── Stage ④: 構造化抽出 ────
    print(f"\n{'='*60}")
    print("Stage ④: LLM Pass 1 - Structured extraction")
    print(f"{'='*60}")
    structure_out = str(out / "structure.json")
    extract_structure(transcript_out, structure_out)

    # ──── Stage ⑤: コードスニペット取得 ────
    code_out = str(out / "code_snippets.json")
    if skip_code:
        print(f"\n{'='*60}")
        print("Stage ⑤: Skipping code fetch (--skip-code)")
        print(f"{'='*60}")
        code_out = None
    else:
        print(f"\n{'='*60}")
        print("Stage ⑤: GitHub API code snippet fetch")
        print(f"{'='*60}")
        fetch_code_snippets(structure_out, code_out)

    # ──── Stage ⑥: 記事生成 ────
    print(f"\n{'='*60}")
    print("Stage ⑥: LLM Pass 2 - Article generation")
    print(f"{'='*60}")
    article_out = str(out / "article_draft.md")
    generate_article(structure_out, code_out, article_number, article_out)

    # ──── Stage ⑦: 品質チェック ────
    print(f"\n{'='*60}")
    print("Stage ⑦: Quality validation")
    print(f"{'='*60}")
    results = validate_article(article_out)
    passed = print_results(results)

    # ──── 完了サマリー ────
    elapsed = time.time() - start_time
    print(f"\n{'='*60}")
    print("Pipeline complete!")
    print(f"{'='*60}")
    print(f"  Time elapsed: {elapsed:.1f}s")
    print(f"  Draft saved:  {article_out}")
    print(f"  Validation:   {'PASSED' if passed else 'FAILED (review errors above)'}")
    print()
    print("Next steps:")
    print(f"  1. Review the draft: {article_out}")
    print("  2. Add screenshots and images where <!-- TODO --> markers exist")
    print("  3. Verify code snippets are accurate")
    print(f"  4. Copy to articles/ directory and rename")
    print("  5. Set published: true when ready")


def main():
    parser = argparse.ArgumentParser(
        description="会議動画 → Zenn記事ドラフト生成パイプライン",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # 動画から一括生成
  python pipeline.py --video ~/Downloads/meeting.mp4 --number 4

  # 文字起こし済みファイルから生成
  python pipeline.py --transcript output/drafts/transcript.json --number 4

  # コード取得をスキップ
  python pipeline.py --video meeting.mp4 --number 4 --skip-code
        """,
    )
    parser.add_argument("--video", help="入力動画ファイルパス (MP4)")
    parser.add_argument("--transcript", help="既存のトランスクリプトJSONファイルパス")
    parser.add_argument("--number", type=int, required=True,
                        help="記事番号 (例: 4)")
    parser.add_argument("--skip-code", action="store_true",
                        help="GitHub APIでのコード取得をスキップ")
    parser.add_argument("--output-dir", help="出力ディレクトリ (default: output/drafts/)")
    args = parser.parse_args()

    if not args.video and not args.transcript:
        parser.error("Either --video or --transcript is required.")

    if args.video and not os.path.exists(args.video):
        print(f"Error: Video file not found: {args.video}", file=sys.stderr)
        sys.exit(1)

    if args.transcript and not os.path.exists(args.transcript):
        print(f"Error: Transcript file not found: {args.transcript}",
              file=sys.stderr)
        sys.exit(1)

    run_pipeline(
        video_path=args.video,
        transcript_path=args.transcript,
        article_number=args.number,
        skip_code=args.skip_code,
        output_dir=args.output_dir,
    )


if __name__ == "__main__":
    main()
