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

## セットアップ

```bash
npm install
```

## ローカルプレビュー

```bash
npm run preview
# http://localhost:8000 でプレビューが開きます
```

## 新規記事の作成

```bash
npx zenn new:article
```

## 参考

- [Zenn CLI ガイド](https://zenn.dev/zenn/articles/zenn-cli-guide)
- [Zenn GitHub 連携](https://zenn.dev/zenn/articles/connect-to-github)
