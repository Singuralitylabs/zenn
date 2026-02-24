"""
Stage ②③: 動画から音声抽出 + Whisper APIで文字起こし

Usage:
    python transcribe.py --video path/to/meeting.mp4 --output output/transcript.json
"""

import argparse
import json
import math
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(Path(__file__).resolve().parent.parent / "config" / ".env")

WHISPER_MAX_SIZE_MB = 25
CHUNK_DURATION_SEC = 600  # 10 minutes


def extract_audio(video_path: str, audio_path: str) -> None:
    """ffmpegでMP4からMP3を抽出する。"""
    cmd = [
        "ffmpeg", "-i", video_path,
        "-vn", "-acodec", "libmp3lame", "-q:a", "4",
        "-y", audio_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"ffmpeg error: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    print(f"Audio extracted: {audio_path}")


def get_audio_duration(audio_path: str) -> float:
    """ffprobeで音声ファイルの長さ（秒）を取得する。"""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        audio_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip())


def split_audio(audio_path: str, chunk_dir: str) -> list[str]:
    """音声ファイルをチャンクに分割する（25MB制限対応）。"""
    file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)

    if file_size_mb <= WHISPER_MAX_SIZE_MB:
        return [audio_path]

    duration = get_audio_duration(audio_path)
    num_chunks = math.ceil(file_size_mb / WHISPER_MAX_SIZE_MB)
    chunk_duration = duration / num_chunks

    chunks = []
    for i in range(num_chunks):
        start = i * chunk_duration
        chunk_path = os.path.join(chunk_dir, f"chunk_{i:03d}.mp3")
        cmd = [
            "ffmpeg", "-i", audio_path,
            "-ss", str(start), "-t", str(chunk_duration),
            "-acodec", "libmp3lame", "-q:a", "4",
            "-y", chunk_path,
        ]
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        chunks.append(chunk_path)

    print(f"Split into {len(chunks)} chunks")
    return chunks


def transcribe_chunk(client: OpenAI, audio_path: str, model: str) -> dict:
    """Whisper APIで1チャンクを文字起こしする。"""
    with open(audio_path, "rb") as f:
        response = client.audio.transcriptions.create(
            model=model,
            file=f,
            language="ja",
            response_format="verbose_json",
            timestamp_granularities=["segment"],
        )
    return response


def merge_transcripts(results: list[dict], chunk_offsets: list[float]) -> dict:
    """複数チャンクの文字起こし結果を結合する。"""
    merged_text = ""
    merged_segments = []

    for i, result in enumerate(results):
        offset = chunk_offsets[i]
        merged_text += result.text + " "

        if hasattr(result, "segments") and result.segments:
            for seg in result.segments:
                merged_segments.append({
                    "start": seg["start"] + offset,
                    "end": seg["end"] + offset,
                    "text": seg["text"],
                })

    return {
        "text": merged_text.strip(),
        "segments": merged_segments,
    }


def transcribe(video_path: str, output_path: str) -> dict:
    """メイン処理: 動画→音声抽出→文字起こし。"""
    client = OpenAI()
    model = os.getenv("WHISPER_MODEL", "whisper-1")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Stage ②: 音声抽出
        audio_path = os.path.join(tmpdir, "audio.mp3")
        extract_audio(video_path, audio_path)

        # チャンク分割（必要な場合のみ）
        chunks = split_audio(audio_path, tmpdir)

        # Stage ③: Whisper APIで文字起こし
        results = []
        chunk_offsets = []
        current_offset = 0.0

        for i, chunk_path in enumerate(chunks):
            print(f"Transcribing chunk {i + 1}/{len(chunks)}...")
            result = transcribe_chunk(client, chunk_path, model)
            results.append(result)
            chunk_offsets.append(current_offset)

            if len(chunks) > 1:
                duration = get_audio_duration(chunk_path)
                current_offset += duration

        # 結果の結合
        if len(results) == 1:
            transcript = {
                "text": results[0].text,
                "segments": [
                    {"start": s["start"], "end": s["end"], "text": s["text"]}
                    for s in (results[0].segments or [])
                ],
            }
        else:
            transcript = merge_transcripts(results, chunk_offsets)

        transcript["source_video"] = os.path.basename(video_path)

    # 出力
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(transcript, f, ensure_ascii=False, indent=2)

    print(f"Transcript saved: {output_path}")
    print(f"Total segments: {len(transcript['segments'])}")
    print(f"Total text length: {len(transcript['text'])} chars")

    return transcript


def main():
    parser = argparse.ArgumentParser(description="会議動画の文字起こし")
    parser.add_argument("--video", required=True, help="入力動画ファイルパス (MP4)")
    parser.add_argument("--output", default="output/drafts/transcript.json",
                        help="出力先 (default: output/drafts/transcript.json)")
    args = parser.parse_args()

    if not os.path.exists(args.video):
        print(f"Error: Video file not found: {args.video}", file=sys.stderr)
        sys.exit(1)

    transcribe(args.video, args.output)


if __name__ == "__main__":
    main()
