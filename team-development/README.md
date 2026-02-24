# チーム開発会議動画 → Zenn記事 自動生成パイプライン

会議動画（MP4）から Zenn 記事のドラフトを自動生成するツールです。

## パイプライン概要

```
会議動画 (MP4)
  │
  ├─ ② ffmpeg で音声抽出 (MP4 → MP3)
  ├─ ③ Whisper API で文字起こし（日本語）
  │     → transcript.json
  │
  ├─ ④ GPT-4o Pass 1: 構造化情報抽出
  │     → structure.json
  │
  ├─ ⑤ GitHub API でコードスニペット取得
  │     → code_snippets.json
  │
  ├─ ⑥ GPT-4o Pass 2: 記事ドラフト生成
  │     → article_draft.md (published: false)
  │
  └─ ⑦ 自動品質チェック（構造・リンク・フロントマター検証）
```

## セットアップ

### 1. 前提条件

- Python 3.10+
- ffmpeg（音声抽出に使用）
- OpenAI API キー
- GitHub Personal Access Token（コードスニペット取得に使用、省略可）

#### ffmpeg のインストール

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg
```

### 2. Python 依存パッケージのインストール

```bash
cd team-development
pip install -r requirements.txt
```

### 3. 環境変数の設定

```bash
cp config/.env.example config/.env
```

`config/.env` を編集し、APIキーを設定してください。

```
OPENAI_API_KEY=sk-your-openai-api-key-here
GITHUB_TOKEN=ghp_your-github-token-here
```

| 変数 | 必須 | 説明 |
|---|---|---|
| `OPENAI_API_KEY` | Yes | OpenAI API キー（Whisper + GPT-4o） |
| `GITHUB_TOKEN` | No | GitHub PAT（コードスニペット取得用） |
| `GITHUB_REPO` | No | 対象リポジトリ（デフォルト: `Singuralitylabs/portal-site`） |
| `LLM_MODEL` | No | 記事生成モデル（デフォルト: `gpt-4o`） |
| `WHISPER_MODEL` | No | 文字起こしモデル（デフォルト: `whisper-1`） |

## 使い方

### 基本: 動画から一括生成

```bash
python scripts/pipeline.py --video ~/Downloads/meeting_20260223.mp4 --number 4
```

- `--video`: 会議動画ファイル（MP4）のパス
- `--number`: 記事番号（「チーム開発記録**N**」の N）

実行すると `output/drafts/article_draft.md` にドラフトが生成されます。

### 文字起こし済みファイルから再生成

文字起こし結果を修正した場合や、プロンプト調整後に再生成したい場合:

```bash
python scripts/pipeline.py --transcript output/drafts/transcript.json --number 4
```

### コード取得をスキップ

GitHub Token が未設定の場合や、コードスニペットが不要な場合:

```bash
python scripts/pipeline.py --video meeting.mp4 --number 4 --skip-code
```

### 出力先の変更

```bash
python scripts/pipeline.py --video meeting.mp4 --number 4 --output-dir ./my_output
```

## 各スクリプトの個別実行

パイプライン全体ではなく、特定のステージだけを実行することもできます。

### 文字起こしのみ（Stage ②③）

```bash
python scripts/transcribe.py --video ~/Downloads/meeting.mp4 --output output/drafts/transcript.json
```

- 25MB を超える音声は自動的にチャンク分割されます
- 出力: タイムスタンプ付き JSON

### 構造化抽出のみ（Stage ④）

```bash
python scripts/extract_structure.py --transcript output/drafts/transcript.json --output output/drafts/structure.json
```

- トランスクリプトからトピック・決定事項・技術キーワード等を JSON で抽出

### コードスニペット取得のみ（Stage ⑤）

```bash
python scripts/fetch_code.py --structure output/drafts/structure.json --output output/drafts/code_snippets.json
```

- 構造化データ内の PR 番号・ファイルパスへの言及を検出し、GitHub API で取得

### 記事生成のみ（Stage ⑥）

```bash
python scripts/generate_article.py --structure output/drafts/structure.json \
                                    --code output/drafts/code_snippets.json \
                                    --number 4 \
                                    --output output/drafts/article_draft.md
```

- `--code` は省略可能

### 品質チェックのみ（Stage ⑦）

```bash
python scripts/validate_article.py --article output/drafts/article_draft.md
```

チェック項目:
- フロントマター（title, emoji, type, topics, published）
- 必須セクション（概要 / 開発したもの / 会議の様子 / 活用した技術 / 総括）
- 必須リンク（GitHub リポジトリ、シンラボ HP）
- フッター（プログラミングイベント案内 / GAS サービス / シンラボ案内）
- コードブロックの開閉一致

## ドラフト生成後の作業

パイプラインが出力するのは **`published: false` のドラフト** です。公開前に以下を確認してください。

1. **内容の確認** — タイトル・サブタイトルが会議内容を正確に反映しているか
2. **コードスニペットの確認** — GitHub API で取得できなかったコードがあれば手動で補完
3. **画像の追加** — `<!-- TODO: 画像を追加 -->` の箇所にスクリーンショット等を挿入
4. **前回記事リンクの確認** — 概要セクションのリンクが正しいか
5. **`articles/` への配置** — ドラフトを `articles/` ディレクトリにコピーし、Zenn のファイル名規則に従ってリネーム
6. **`published: true` に変更** — レビュー完了後にフロントマターを更新
7. **main へマージ** — Zenn の GitHub 連携で自動デプロイ

## コスト目安

60 分の会議動画 1 本あたり:

| 項目 | コスト |
|---|---|
| Whisper API（文字起こし） | ~$0.36 |
| GPT-4o（2 パス記事生成） | ~$0.30 |
| GitHub API | $0 |
| **合計** | **~$0.66（約100円）** |

## ディレクトリ構成

```
team-development/
├── scripts/
│   ├── transcribe.py          # ②③ 音声抽出 + Whisper 文字起こし
│   ├── extract_structure.py   # ④  LLM Pass 1 構造化抽出
│   ├── fetch_code.py          # ⑤  GitHub API コード取得
│   ├── generate_article.py    # ⑥  LLM Pass 2 記事生成
│   ├── validate_article.py    # ⑦  自動品質チェック
│   └── pipeline.py            # 全ステージ統合オーケストレーター
├── templates/
│   ├── footer.md              # 共通フッター
│   └── prompts/
│       ├── extraction.txt     # Pass 1 用プロンプト
│       └── generation.txt     # Pass 2 用プロンプト
├── config/
│   └── .env.example           # 環境変数テンプレート
├── output/drafts/             # 生成物の一時保管
├── requirements.txt           # Python 依存パッケージ
└── README.md                  # 本ドキュメント
```

## トラブルシューティング

### ffmpeg が見つからない

```
ffmpeg error: ...
```

→ `brew install ffmpeg` または `sudo apt install ffmpeg` でインストールしてください。

### Whisper API の 25MB 制限エラー

通常は自動チャンク分割で対処されます。それでもエラーが出る場合は、ffmpeg で音声品質を下げてください:

```bash
ffmpeg -i meeting.mp4 -vn -acodec libmp3lame -q:a 6 -y audio.mp3
```

### GitHub API のレート制限

認証なしでは 60 req/h、Token ありでは 5,000 req/h です。
`GITHUB_TOKEN` を設定するか、`--skip-code` でスキップしてください。

### 品質チェックで FAIL が出る

`validate_article.py` のエラーメッセージに従って、ドラフトの該当箇所を手動修正してください。よくある原因:

- フロントマターのキー欠落 → LLM の出力形式がずれた場合。手動でフロントマターを追加
- 必須セクション欠落 → `## 概要` 等の見出しが微妙に異なる場合。正確な見出しに修正
- フッター欠落 → 生成時にフッターテンプレートの結合に失敗した場合。`templates/footer.md` を末尾に手動追加
