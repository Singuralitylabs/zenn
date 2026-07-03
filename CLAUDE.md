# Zenn記事リポジトリ — シンギュラリティ・ラボ

## 概要

オンラインサロン「シンギュラリティ・ラボ」のチーム開発活動を記録するZenn記事リポジトリ。
GitHubのmainブランチへのpushで自動デプロイされる（Zenn GitHub連携）。

## ディレクトリ構成

```
Zenn/
├── articles/              # Zenn記事（14文字英数字ID.md）
├── src-data/              # NotebookLM出力の元データ（YYYYMMDD_*.md）
│   └── archived/          # 記事化済みの元データ（処理対象外）
├── team-development/      # 記事生成パイプライン
│   ├── pipeline.py        # メイン実行スクリプト（実装予定）
│   └── templates/
│       └── footer.md      # 共通フッター（全記事で共通）
└── package.json           # zenn-cli
```

## 記事生成ワークフロー

1. 会議動画 → NotebookLM で記事草稿を生成
2. NotebookLMの出力を `src-data/YYYYMMDD_*.md` として保存（手動）
3. `/zenn-article` コマンドで記事ドラフトを自動生成
4. `articles/<ID>.md`（`published: false`）が生成される
5. コードスニペット・画像を確認・補完
6. `published: true` に変更してmainマージ → 自動デプロイ

## src-dataの命名規則

```
形式: YYYYMMDD_<任意の説明>.md
例:   20260108_ver6_カレンダー追加.md
```

- `YYYYMMDD` は**会議の日付**（GitHubのPR日付範囲算出に使用）
- 説明部分は自由記述（記事タイトルとは独立）

## チーム開発定例の参加者（文字起こしの名寄せ）

定例の**司会は山田**。発言者ラベルや「〇〇さん」表記を整えるときの正しい氏名は次のとおり（敬称略）。

- 山田、宮澤、高橋、滝口、菅原、西村、**井上**

よくある誤認・表記ゆれの例: 山本→山田、宮田・宮沢→宮澤、竹口→滝口、司会・進行役のラベル→山田（司会発言）。

## 記事における個人名の扱い

**記事本文に個人名（氏名）を掲載しない。**

- 発言者・担当者を表す場合は「チームメンバー」「担当者」「リードエンジニア」など役割・立場で表現する
- 固有名詞が必要な場合も「あるメンバー」「別のメンバー」のような匿名表現にとどめる
- この制約は「会議の様子」セクションを含む記事全体に適用する

## 記事フロントマター規則

```yaml
---
title: "チーム開発記録N：[サブタイトル]"  # N は自動採番
emoji: "[絵文字1文字]"
type: "tech"                              # 固定
topics: ["チーム開発", ...技術名]          # "チーム開発" は必ず先頭
published: false                          # ドラフト時は false
---
```

- 記事番号 N は `articles/` 内の既存記事を走査して自動採番（最大N+1）
- Zenn記事IDは `python3 -c "import secrets; print(secrets.token_hex(7))"` で生成

## 記事の必須セクション（順番厳守）

1. `## 概要` — 前回記事リンク・wiki・GitHubリポリンクを含む
2. `## 開発したもの` — 実装内容・コードスニペット
3. `## 会議の様子` — 議論・決定事項
4. `## 活用した技術` — 技術解説
5. `## 総括` — まとめと参加呼びかけ
6. `---` — 区切り線
7. フッター — `team-development/templates/footer.md` から静的結合（LLM生成不可）

## 概要セクションの必須リンク（毎記事挿入）

```markdown
* チーム開発方針については、[こちら](https://zenn.dev/singularitylabs/articles/20123b869b7e6a)をご参考ください
* 技術スタックは[こちら](https://github.com/Singuralitylabs/portal-site/wiki)をご参考ください
* 開発しているポータルサイトのGithubリポジトリは[こちら](https://github.com/Singuralitylabs/portal-site)です
```

## 重要な外部リンク

| リソース | URL |
|---|---|
| ポータルサイトGitHub | `github.com/Singuralitylabs/portal-site` |
| 技術スタックwiki | `github.com/Singuralitylabs/portal-site/wiki` |
| チーム開発方針記事 | `zenn.dev/singularitylabs/articles/20123b869b7e6a` |
| Zenn publication | `zenn.dev/singularitylabs` |

## コードスニペットのルール

- **LLMに生成させない** — GitHub APIから実際のコードを取得する
- 取得対象: `Singuralitylabs/portal-site` の main へマージ済みPR
- 日付範囲: 前回のsrc-dataファイル日付 〜 今回の日付
- 取得できない場合は `<!-- TODO: コードスニペットを追加 -->` を挿入
- コードブロックには必ず言語を指定（` ```javascript `, ` ```typescript `, ` ```sql ` 等）

## ローカルプレビュー

```bash
npm run preview  # http://localhost:8000 でZennプレビュー
```

## 公開状態の Finder タグ同期

`articles/` 配下の各記事 frontmatter `published` を読み取り、macOS Finder タグを付与する。

- `published: true` → 🟢 緑タグ
- `published: false` → 🔴 赤タグ

```bash
python3 team-development/scripts/tag_articles.py
```

`.git/hooks/post-commit` で **commit 時に articles/ の変更があれば自動実行**される（macOS のみ）。手動編集／Claude 経由の編集を問わず、commit を通せばタグが同期される。

新しい clone でフックを有効化する場合は、`.git/hooks/post-commit` を実行可能ビットつきで再配置すること（Git は hooks/ をバージョン管理対象外とするため）。

## articles-index/（公開状態つき記事一覧）

記事ファイル名（= Zennスラッグ = URL）はリネームできないため、エディタのツリーで記事番号順・公開状態を見えるようにする **シンボリックリンクの一覧** を `articles-index/` に自動生成している。

- リンク名: `<記録番号2桁>_<🟢|🔴>_<サブタイトル>.md`（シリーズ外の記事は `zz_` プレフィックス）
- 🟢 = `published: true` / 🔴 = `published: false`
- リンクを開けば `articles/` の実体をそのまま編集できる
- 生成物のため `.gitignore` 対象。Zennのデプロイには影響しない

```bash
python3 team-development/scripts/generate_article_index.py
```

post-commit フックで Finder タグと同時に自動再生成される。**記事のタイトル・published を変更したら commit すれば同期される**（即時に反映したい場合は上記を手動実行）。
