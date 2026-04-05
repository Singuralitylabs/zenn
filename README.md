# Zenn 記事管理リポジトリ

[シンギュラリティ・ラボ（singularitylabs）](https://zenn.dev/singularitylabs) の Zenn 記事を管理するリポジトリです。
GitHub 連携により、`main` ブランチへの push で記事が自動デプロイされます。

## 記事一覧

| ファイル | タイトル |
|----------|----------|
| `articles/20123b869b7e6a.md` | シンギュラリティ・ラボのチーム開発活動のご紹介 |
| `articles/0ea64a7c1f221a.md` | チーム開発記録1：コミュニティのポータルサイトを作る |
| `articles/4cbaefe0e930e2.md` | チーム開発記録2：ポータルサイト初期バージョンのリリース |
| `articles/f1ba6f8f0de4ef.md` | チーム開発記録3：動画閲覧機能への挑戦とセキュリティ基盤の強化 |
| `articles/1c164e323a2132.md` | チーム開発記録4：承認機能の設計とRLSポリシーの実装 |
| `articles/9de42fbe205409.md` | チーム開発記録5：動画詳細ページと承認機能の実装 |
| `articles/a0088b1813e327.md` | チーム開発記録6：動画詳細ページのリリースと承認機能の開発着手 |
| `articles/8afbaa059e06bd.md` | チーム開発記録7：ver2リリースと設計書のメンテナンス性向上 |
| `articles/6916687843f809.md` | チーム開発記録8：動画サムネイル表示とカテゴリーテーブル設計 |
| `articles/b74881e4420ae1.md` | チーム開発記録9：カテゴリーテーブル設計とDB設計方針の議論 |
| `articles/0d84124879cfc4.md` | チーム開発記録10：カテゴリーIDへの移行とSupabase Auth設計 |
| `articles/a732afd7564b89.md` | チーム開発記録11：動画・資料一覧のカテゴリー別表示実装 |
| `articles/fed7df1142ac29.md` | チーム開発記録12：Supabase Auth移行と承認機能の完成 |
| `articles/77e879dbeaa3f5.md` | チーム開発記録13：管理画面設計とカテゴリーページ内遷移の実装 |
| `articles/de09d4ecd1612c.md` | Googleカレンダー連携とSNS機能の拡充 |

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
