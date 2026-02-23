---
title: "チーム開発記録3：動画閲覧機能への挑戦とセキュリティ基盤の強化"
emoji: "🎬"
type: "tech"
topics: ["チーム開発", "nextjs", "typescript", "supabase", "react"]
published: true
publication_name: "singularitylabs"
---

## 概要

オンラインサロン「シンギュラリティ・ラボ（通称シンラボ）」のポータルサイト開発チームは、初期バージョン（資料一覧機能と認証機能）のリリースを経て、次の大きな目標である**動画閲覧機能**（Phase 2）の実装に精力的に取り組んでいます。

本記事は、[チーム開発記録2：ポータルサイト初期バージョンのリリース](https://zenn.dev/singularitylabs/articles/4cbaefe0e930e2)に続く最新の活動記録です。私たちは、Next.js、TypeScript、Supabase、Clerkといったモダンな技術スタックに触れながら、実践的なチーム開発の経験を積んでいます。開発者のスキルレベルは様々ですが、学びを深め、**技術的な背景に関わらず全員が楽しく開発に参加できる環境**を構築しています。

今回の開発サイクルでは、動画の一覧ページと詳細ページの実装をメインに進めました。特に、新たな技術的な課題に挑戦し、システムのセキュリティ強化に不可欠なデータベース設計の整理、そして次期機能（ユーザー承認機能）に向けた計画策定を行いました。

* チーム開発方針については、[こちら](https://zenn.dev/singularitylabs/articles/20123b869b7e6a)をご参考ください
* 技術スタックは[こちら](https://github.com/Singuralitylabs/portal-site/wiki)をご参考ください
* 開発しているポータルサイトのGithubリポジトリは[こちら](https://github.com/Singuralitylabs/portal-site)です

## 開発したもの

Phase 2の主要目標である「動画閲覧機能」（一覧と詳細ページ）の実装が本格化しました。動画閲覧機能は、初期フェーズで完了した資料一覧機能とほぼ同じ構造で実装可能な部分が多く、効率的な開発が進んでいます。

### 動画一覧ページの完成とデータ連携の準備

#### 動画一覧ページの実装

動画一覧ページ（フロントエンド）の実装は一通り完了し、プルリクエスト（PR）にて画面のスクリーンショットが共有されました。画面は、データベースから実際にデータを取得し、カードコンポーネントで表示できる実装にしました。

##### カードコンポーネントでの動画一覧表示
```javascript
export function VideosPageTemplate({ videos }: VideosPageTemplateProps) {
  return (
    <Paper m="0 2rem">
      <PageTitle>動画一覧</PageTitle>

      <Paper>
        <Grid>
          {videos.map((video) => (
            <Grid.Col span={{ base: 12, md: 6, lg: 4 }} key={video.id + '_grid'}>
              <VideoCard video={video} />
            </Grid.Col>
          ))}
        </Grid>
      </Paper>
    </Paper>
  );
}
```

##### カードコンポーネント
```javascript
export function VideoCard({ video }: VideoCardProps) {
  return (
    <Card component="a" href={`/videos/${video.id}`} shadow="sm" padding="0" radius="md" w="100%" withBorder className="hover:shadow-lg transition-shadow">
      <Card.Section>
        <div style={{ position: 'relative', width: '100%', height: '12rem' }}>
          <Image
            src={video.thumbnail_path || '/default_video_thumbnail.png'}
            alt={video.name}
            fill
            style={{ objectFit: 'cover', borderTopLeftRadius: '8px', borderTopRightRadius: '8px' }}
          />
        </div>
      </Card.Section>
      <Card.Section p="md">
        <Text fw={700} size="lg" mb="xs">{video.name}</Text>
        <Text component="div" lineClamp={2} c="dimmed" mb="md">
          {video.description}
        </Text>
        <Button component="div" radius="md" size="compact-sm" c="rgb(23,23,23)" bg="gray.2" fs="0.875rem">
          {video.category}
        </Button>
      </Card.Section>
    </Card>
  );
}
```

#### サムネイル表示ロジックの設計

一覧ページには動画のサムネイル画像を表示しますが、そのデータが欠けている場合の振る舞いを明確にする必要がありました。動画のデータベーステーブルには、以下の2つのカラムが存在します。

*   **サムネイルパス**：画像ファイルへのパス。
*   **サムネイルタイム**：動画内の特定の時間（秒換算）を指定し、その時点の画面をサムネイルとして利用するためのカラム。

チームは、サムネイル表示の優先順位を以下の3段階で決定しました。

1.  **サムネイルタイム**：時間情報が指定されていれば、それを最優先で利用します。
2.  **サムネイルパス**：時間情報がなければ、画像パスを確認します。
3.  **デフォルトイメージ**：どちらも存在しない場合、事前に用意したデフォルト画像を表示します。

この優先順位は、データベースへのアクセス負荷を考慮し、ファイルパスの確認（ファイルシステムへのアクセス）よりも、データベース内のシンプルな時間情報（テキストデータ）の有無を先に判定する方が効率的であるという判断に基づいています。

![動画データのER図](https://storage.googleapis.com/zenn-user-upload/d476d632f421-20251130.png)

##### supabaseからの動画データ取得処理

```javascript
export async function fetchVideos() {
  const supabase = await createServerSupabaseClient();
  const { data, error } = await supabase
    .from("videos")
    .select("*")
    .eq("is_deleted", false);

  if (error) {
    console.error("Supabase 動画一覧データ取得エラー:", error.message);
    return { data: null, error };
  }

  return { data, error: null };
}
```

#### 開発環境での画像の取り扱い

開発初期段階では、動画データが揃っていないため、ランダムな画像を生成する外部APIサービス（`picsum.photos`）を利用し、**ダミー画像**として画面に表示させました。Next.jsでは、セキュリティ上の理由から、外部ドメインの画像を利用する際は設定ファイルにそのドメインを登録する必要があることも確認しました。

また、Next.jsでは、アイコンや画像などのアセットをアプリケーション内の**パブリック（public）ディレクトリー**に配置し、それを読み込むのが一般的な手法であることも再確認されました。

### 動画詳細ページの動的ルーティング実装

動画の詳細ページは、ユーザーが一覧画面で特定の動画カードをクリックした際に、個別の動画IDに基づいて内容を表示するページです。

#### Next.jsの動的ルーティングの活用

この実装では、Next.jsの**動的ルーティング**の仕組みを活用しました。詳細ページのディレクトリー名には、`[id]`のように**鍵括弧**が用いられています。この構造により、`videos/1`、`videos/2`といった任意のIDがパスに入力された場合でも、そのIDをパラメータとして受け取り、同一のコンポーネントで処理することが可能になります。

```
portal-site/
├── app/                       # Next.js App Router
|   ├── (authenticated)/
|   |    ├── videos/
|   |    |   ├── components/
|   |    |   ├── [id]/         # 動的ルーティング
|   |    |   |   └── page.tsx
|   |    |   └── page.tsx
|   |    :
|   |    ├ page.tsx
|   |    └ layout.tsx
|   :
├── docs/                      # プロジェクトドキュメント
└── supabase/                  # Supabaseマイグレーション
```

#### YouTube動画の組み込み

動画の再生には、`react-youtube`ライブラリを使用しました。しかし、このライブラリには、動画再生画面のサイズが固定化され、通常のCSSでは柔軟なサイズ変更ができないという技術的課題が判明しました。このため、DOMのサイズ情報を取得し、それをコンポーネントに渡してサイズを計算させるための処理（`useRef`などの利用）が必要となることが共有されました。

```javascript
<div className="max-w-[800px] w-full shadow-md rounded-b-md">
  <div className="relative w-full" style={{ aspectRatio: "16/9" }}>
    <YouTube
      videoId={video.url.replace(/(?:https?:\/\/)?(?:www\.)?(?:m\.)?(?:youtu\.be\/|youtube\.com\/(?:embed\/|v\/|watch\?v=|watch\?.+&v=))([\w-]{11})(?:\S+)?$/, "$1")}
      title={video.name}
      opts={{
        width: "100%",
        height: "100%",
      }}
      className="absolute inset-0 w-full h-full"
      iframeClassName="w-full h-full"
    />
  </div>
<div>
```

### バックエンドの技術基盤強化

セキュリティ強化とメンテナンス性向上を目的として、バックエンドの技術基盤の整備を進めました。

#### RLS（Row-Level Security）ポリシーの明確化

Supabaseの**ローレベルセキュリティ（RLS）**は、データへのアクセス制限を強化するための重要な機能です。データベース設計書には、RLSポリシーの項目が新たに追加され、ユーザーテーブル、ドキュメントテーブル、そして今回追加されたビデオズテーブルのポリシー設定内容が詳細に記述されました。

RLSポリシーの具体的な設定では、ログイン中のユーザーが資料や動画を閲覧する権限があるかをチェックするため、SQLの`EXISTS`句を利用し、ユーザーがSupabaseのユーザーテーブルに存在し、必要なロールを持っているかを確認する複雑な処理が採用されています。

```sql
-- 登録済みユーザーは全てのvideosを閲覧可能
DROP POLICY IF EXISTS "registered_users_can_read_videos" ON "videos";
CREATE POLICY "registered_users_can_read_videos" ON "videos"
  FOR SELECT
  USING (
    is_registered_user()
    AND is_deleted = FALSE
  );

ALTER TABLE "videos" ENABLE ROW LEVEL SECURITY;
```

#### SQLファイルの管理と整理

Supabaseで使用するSQLクエリ（テーブル作成、トリガー、関数、ポリシー）について、GitHubリポジトリ内での管理方法が議論されました。現在、マイグレーションファイルはいくつかのテーブルや機能のSQLをまとめた形になっていますが、今後は、変更履歴の管理を容易にするため、トリガーやポリシーなどを機能単位（例：トリガー、ファンクション、ポリシー）やテーブル単位でファイルを分割する構成案が提案され、議論が進められました。

```
portal-site/
├── app/                   # Next.js App Router
├── docs/                  # プロジェクトドキュメント
└── supabase/              # Supabaseマイグレーション
    ├── migrations/        # DBマイグレーションファイル
    |   ├── 01_tables/     # テーブル設計
    |   ├── 02_triggers/   # トリガー設定
    |   ├── 03_functions/  # 関数設定
    |   └── 04_policies/   # ポリシー設定
    └── README.md          # Supabase設定ガイド
```

また、チームメンバーがSupabaseのSQLエディターで作成したクエリを共有するためには、クエリをプライベート設定から**シェアード（共有）**設定に変更する必要があることが確認されました。

## 会議の様子

定例ミーティングでは、開発の進捗確認だけでなく、コードの品質や今後のロードマップに関する活発な議論が交わされました。

### コード品質とコーディング規約

コードの品質と保守性を高めるため、以下の規約や改善点の適用が確認されました。

*   **リンクコンポーネントの推奨:** Next.jsでは、パフォーマンスの最適化処理や可読性の観点から、Aタグよりも**リンクコンポーネント**（`Link`）の利用が推奨されています。動画一覧の実装でAタグが使われていた箇所について、リンクコンポーネントへの修正が指示されました。
*   **キャメルケースの徹底:** JavaScript/TypeScriptにおける標準的な命名規約である**キャメルケース**（camelCase）を徹底する方針が再確認され、詳細ページの実装における修正点が洗い出されました。

### AI技術の活用と開発プロセス

開発チームは、AIを開発プロセスに取り込む機会を常に探っています。

*   **GitHub Copilotの応用:** プルリクエストのデフォルトテンプレートに特定のコメントを追記することで、GitHub Copilot Code Review機能によるレビュー文章を自動的に**日本語化**できるという応用的な活用方法が共有されました。
*   **設計ドキュメントの扱い:** ロジックが複雑化する際、そのロジックの詳細（フローチャートなど）をどこまで設計書に起こすべきか議論されました。コードを見れば分かるという意見も出ましたが、後からシステム全体や意図を正確に理解するため、ウェブアプリ開発においても**設計ドキュメント（特にロジック）を残すべき**という意見で一致しました。

### 次期開発テーマ「ユーザー承認機能」の計画策定

Phase 2（動画閲覧機能）の完了後、次の主要な開発目標として**ユーザー承認機能**（Phase 3）の実装が決定しました。現在、Googleログインボタンを押せば誰でもログインできてしまうというセキュリティ上の課題があるため、この機能はセキュリティ強化の核心となります。

**【承認機能の要件と優先度設定】**

承認機能の実装に必要なタスクは、GitHub Project上で洗い出され、以下の通り**優先度（Priority P1, P2）**が設定されました。

| タスク | 概要 | 優先度 |
| :--- | :--- | :--- |
| **未承認ユーザーのルーティング** | 管理者に承認されていないユーザーが、ポータルサイトの主要ページにアクセスできないように設定する。 | P1（必須） |
| **RLSの追加** | ユーザーの承認ステータスを要件に含めるよう、SupabaseのRLSポリシーを修正・追加する。 | P1（必須） |
| **承認待ち画面の作成** | 未承認ユーザーをリダイレクトし、承認待ちであることを通知する画面を作成する。 | P1（必須に近い） |
| **ユーザー通知の仕組み** | 新規ユーザー登録時や承認完了時に、管理者やユーザーに通知が届く仕組みを検討する。 | P2（改善） |
| **ステータスの追加** | ユーザーのステータスに「拒否（Rejected）」を追加する。 | P2（改善） |

特に、承認機能の実装によってセキュリティを担保しつつ、並行してコードの快適性やレンダリング速度の向上といった**リファクタリング**要素にも着手していく方針が確認されました。

## 活用した技術

今回の開発サイクルを通じて、チームは技術的な適用力と管理能力を向上させました。

### Supabaseのセキュリティ応用

Row-Level Security（RLS）は、Supabaseの重要なセキュリティ機能です。設計書において、ログイン中のClerk IDとSupabaseのユーザーテーブルの情報を照合し、アクセスを制御する複雑なポリシーが、SQLの`EXISTS`句を用いて詳細に定義されました。この応用的な設定は、参加メンバーにとって高度なセキュリティ技術を実践的に学ぶ機会となりました。

### 開発効率化のためのツール導入検討

*   **ORMの将来的な検討:** 現在は生のSQLでデータベース操作を行っていますが、より管理を容易にし、コードとデータベース定義の整合性を高めるために、将来的に**ORM（Object-Relational Mapping）**ツール（例：Prisma）を導入し、開発の自動化を進めることが検討されています。
*   **改善点の管理:** 開発中に見つかった軽微な修正点やリファクタリングの必要箇所は、忘れずに対応するため、**GitHub Issues**や専用のProjectでタスクとして管理する運用が徹底されています。

## 総括

この開発サイクルを通じて、Phase 2の主要機能である動画閲覧機能の実装が本格化し、Next.jsの動的ルーティングやSupabaseのRLS応用など、モダンな技術を実践的に習得することができました。

特に、セキュリティの基盤となるSupabaseのRLS設定を詳細に設計し、次期開発テーマとして「ユーザー承認機能」（Phase 3）の具体的な計画を策定できたことで、プロジェクト全体の計画性とセキュリティ体制が大きく強化されました。

シンラボのチーム開発は、最先端技術の実践と、それに伴う技術的な課題解決を通じて、参加者一人ひとりのスキルアップを強力に支援し続けています。手を動かし、仲間と連携して学ぶ楽しさを共有しつつ、引き続きポータルサイトの進化を加速させてまいります。

シンラボのチーム開発は、AIの活用や最先端技術の実践を通して、参加者一人ひとりのスキル向上を支援する場であり続けます。手を動かしながら連携して学ぶ楽しさを共有しつつ、引き続き開発を進めてまいります。

チーム開発に興味のある方、スキルアップを図りたい方はぜひシンラボにお越しください。

シンギュラリティ・ラボのHPは[こちら](https://sinlab.future-tech-association.org/join)

---

## プログラミングイベントのご案内

毎月数回、GASを中心としたプログラミングを学べるオンライン講座を開催しております。直接学びたい方はぜひご参加ください。
申し込みフォームは[こちら](https://forms.gle/gc5F2PZC1mkwZAc27)
過去のプログラミングイベントの紹介は[こちら](https://sinlab.future-tech-association.org/school/)

## GASアプリ開発サービスのお知らせ

シンギュラリティ・ラボでは、GASを中心としたWebアプリ開発のご相談を受け付けております。
普段の作業のちょっとした自動化から自分やチーム専用のカスタムアプリまで、ぜひお気軽にお問い合わせください。
詳細は[こちら](https://appdev.future-tech-association.org/)

## シンギュラリティ・ラボのご案内

オンラインサロン「シンギュラリティ・ラボ」（通称シンラボ）では、さまざまなITスキルを学び、チーム開発に取り組む仲間を募集しております。 初心者から経験者まで、どなたでも参加可能です。
少しでも興味がございましたらお気軽にお越しください。

シンギュラリティ・ラボのHPは[こちら](https://sinlab.future-tech-association.org/join)

お問い合わせ先 sinlab-recruit@future-tech-association.org
