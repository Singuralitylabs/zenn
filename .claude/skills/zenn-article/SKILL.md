---
name: zenn-article
description: src-dataのNotebookLM出力からZenn記事ドラフトを自動生成する。「記事を作って」「チーム開発記事を生成して」「NotebookLMの文書から記事を書いて」「/zenn-article」などの指示で使用する。src-data/YYYYMMDD_*.md を入力とし、articles/ にZennフォーマットのドラフト（published: false）を出力する。
---

## 前提

- 作業ディレクトリ: Zennリポジトリのルート（`CLAUDE.md` が存在する場所）
- 入力: `src-data/YYYYMMDD_*.md`（NotebookLM出力、記事化前のファイルのみが直下に置かれる）
- 出力: `articles/<14文字ID>.md`（`published: false` のドラフト）
- アーカイブ: 記事化済みの入力ファイルは `src-data/archived/` に移動する（Step 9）

---

## ワークフロー

### Step 1: 入力ファイルの特定

ユーザーがファイルを指定していない場合は `src-data/` の最新ファイルを候補として提示し確認する。

```bash
ls -t src-data/*.md
```

ファイル名先頭8文字（`YYYYMMDD`）を会議日付として抽出する。

---

### Step 2: 記事番号の自動採番

`articles/` 内の既存記事タイトルから「チーム開発記録N」の最大Nを検出し、N+1を次の記事番号とする。

```bash
grep -h "^title:" articles/*.md | grep "チーム開発記録" | sort
```

記録が見つからない場合は1から始める。

---

### Step 3: GitHub APIでコードスニペット取得

**日付範囲の算出:**

```bash
# src-data と archived の両方を対象に、日付昇順でリスト
ls src-data/*.md src-data/archived/*.md 2>/dev/null | xargs -n1 basename | sort
```

- 開始日: 直前のsrc-dataファイル（多くの場合 `src-data/archived/` にある）の日付。なければ今回の日付 - 30日
- 終了日: 今回のsrc-dataファイルの日付

**マージ済みPRの取得:**

```bash
gh pr list \
  --repo Singuralitylabs/portal-site \
  --state merged \
  --base main \
  --search "merged:YYYY-MM-DD..YYYY-MM-DD" \
  --json number,title,mergedAt \
  --limit 30
```

**各PRのコード差分取得（関連性の高いものを選定）:**

```bash
gh pr diff <PR番号> --repo Singuralitylabs/portal-site
```

src-dataの内容（開発したもの・活用した技術のセクション）と照合し、記事に挿入するスニペットを最大10個選定する。JavaScript/TypeScript/SQLを優先する。

取得できなかった箇所には `<!-- TODO: コードスニペットを追加 -->` を挿入する。

---

### Step 4: 前回記事のURLを取得

```bash
grep -rl "チーム開発記録$((N-1))：" articles/
```

前回記事のファイルID（拡張子なし）を取得し、URL `https://zenn.dev/singularitylabs/articles/<ID>` を組み立てる。記事番号1の場合は前回記事リンクなし。

---

### Step 5: フロントマターの生成

src-dataの内容を分析して以下を決定する（Claude自身が判断）:

- `title`: `"チーム開発記録N：[内容を凝縮した15文字以内のサブタイトル]"`
- `emoji`: 記事テーマを象徴する絵文字1文字
- `topics`: `["チーム開発", ...記事内の主要技術を英小文字で最大4つ]`
- `published`: `false`（固定）

---

### Step 6: 記事本文の構築

src-dataのセクションを以下のマッピングでZenn形式に変換する:

| src-dataの見出し | Zenn記事の見出し |
|---|---|
| 導入段落（見出しなし）| ## 概要 の本文冒頭に統合 |
| ### 1. 概要 | ## 概要 |
| ### 2. 開発したもの | ## 開発したもの |
| ### 3. 会議の様子 | ## 会議の様子 |
| ### 4. 活用した技術 | ## 活用した技術 |
| ### 5. 総括 | ## 総括 |

**見出しレベルの統一:** `###` → `##`、`####` → `###`

**概要セクションに必ず挿入するリンク群:**

```markdown
* チーム開発方針については、[こちら](https://zenn.dev/singularitylabs/articles/20123b869b7e6a)をご参考ください
* 技術スタックは[こちら](https://github.com/Singuralitylabs/portal-site/wiki)をご参考ください
* 開発しているポータルサイトのGithubリポジトリは[こちら](https://github.com/Singuralitylabs/portal-site)です
```

前回記事がある場合は概要の冒頭に以下の一文を追加する:

```markdown
本記事は、[チーム開発記録N-1：前回タイトル](https://zenn.dev/singularitylabs/articles/<前回ID>)に続く最新の活動記録です。
```

**コードスニペットの挿入:** Step 3で取得したコードを「開発したもの」「活用した技術」の該当箇所に挿入する。コードブロックには必ず言語を指定する。

---

### Step 7: フッターの結合

フッターテンプレートを確認する:

```bash
cat team-development/templates/footer.md
```

ファイルが存在する場合はその内容を、存在しない場合は `articles/f1ba6f8f0de4ef.md` の274行目以降を使用する。

---

### Step 8: 記事IDの生成と出力

14文字の英数字IDを生成する:

```bash
python3 -c "import secrets; print(secrets.token_hex(7))"
```

以下の構成でファイルを組み立てて `articles/<ID>.md` として保存する:

```
[フロントマター]
[概要セクション（必須リンク含む）]
[開発したものセクション（コードスニペット含む）]
[会議の様子セクション]
[活用した技術セクション]
[総括セクション]
---
[フッター]
```

---

### Step 9: 入力ファイルをアーカイブへ移動

記事ドラフトの保存が成功したら、入力に使用した `src-data/YYYYMMDD_*.md` を `src-data/archived/` に移動する。これにより `src-data/` 直下には未記事化のファイルだけが残り、次回の Step 1（最新ファイル提示）と Step 3（日付範囲算出）が正しく動作する。

```bash
mkdir -p src-data/archived
mv "src-data/<入力ファイル名>.md" src-data/archived/
```

注意:
- `src-data/` は `.gitignore` 対象なので `git mv` は使用しない（通常の `mv` を使う）
- 記事生成に失敗した場合は移動しない。記事ファイルの存在を確認してから実行する

---

### Step 10: 完了報告

出力ファイルパスとレビューチェックリストを表示する:

```
✅ ドラフト生成完了: articles/XXXXXXXXXXXXXXX.md
📦 入力ファイルを src-data/archived/ に移動済み

📋 レビューチェックリスト:
  [ ] タイトル・サブタイトルが内容を正確に反映しているか
  [ ] コードスニペットが正しいか（TODO プレースホルダーを補完）
  [ ] スクリーンショット・ER図などの画像を追加したか
  [ ] 前回記事へのリンクが正しいか
  [ ] published: true に変更してから main マージ

💡 ローカルプレビュー: npm run preview
```
