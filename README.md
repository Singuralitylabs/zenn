# Zenn 記事管理リポジトリ

[シンギュラリティ・ラボ（singularitylabs）](https://zenn.dev/singularitylabs) の Zenn 記事を管理するリポジトリです。
GitHub 連携により、`main` ブランチへの push で記事が自動デプロイされます。

## 記事生成ワークフロー

チーム定例会議の内容を Zenn 記事化する手順です。

### 1. 文字起こし

会議の録画・録音から手動で文字起こしを行い、`src-data/` ディレクトリに保存します。

```
ファイル名形式: YYYYMMDD_<任意の説明>.md
例: 20260108_ver6_カレンダー追加.md
```

`YYYYMMDD` は会議の日付です（GitHub の PR 日付範囲の算出に使用されます）。

### 2. 記事ドラフトの自動生成

Claude Code 上で `/zenn-article` コマンドを実行すると、以下が自動で行われます。

- 記事番号の自動採番
- 対象期間のマージ済み PR からコードスニペットを取得
- src-data の内容を Zenn 記事形式に変換
- `articles/<ID>.md`（`published: false`）として出力

### 3. レビューと公開

生成されたドラフトを確認・補完し、問題なければ `published: true` に変更して `main` ブランチへマージすると自動デプロイされます。

```
[ ] タイトル・サブタイトルが内容を正確に反映しているか
[ ] コードスニペットが正しいか
[ ] 個人名が含まれていないか（役割表現に置換）
[ ] 前回記事へのリンクが正しいか
[ ] published: true に変更してから main マージ
```

## セットアップ

```bash
npm install
```

## ローカルプレビュー

```bash
npm run preview
# http://localhost:8000 でプレビューが開きます
```

## ディレクトリ構成

```
Zenn/
├── articles/              # Zenn 記事（14文字英数字ID.md）
├── src-data/              # 会議の文字起こしデータ（YYYYMMDD_*.md）
├── team-development/      # 記事生成パイプライン
│   └── templates/
│       └── footer.md      # 共通フッター
└── package.json           # zenn-cli
```

## 参考

- [Zenn CLI ガイド](https://zenn.dev/zenn/articles/zenn-cli-guide)
- [Zenn GitHub 連携](https://zenn.dev/zenn/articles/connect-to-github)
