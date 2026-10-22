---
name: implementation
description: >
  C0比較条件で要件から直接実装する。要求全体の網羅、DB Testability、Build、
  既存Regressionと3回修正ループを維持し、独立した設計/判断成果物を作らない。
user-invocable: false
disable-model-invocation: false
---

# Implementation Skill

## Purpose

このSkillは、
要件定義成果物に定義された内容を漏れなくProduction Codeへ実装するための
標準的な実装手順を定義します。

Implementation工程では以下を重視します。

1. 要件定義成果物の内容をすべて確認する
2. 実装対象となる要件を漏れなく実装する
3. 要件の範囲内で必要な実装方式を選び、要求変更が必要な場合は親へ返す
4. 後続の単体テスト・結合テストでテスト可能な構造にする
5. DBを使用する場合、Dockerコンテナ等のテストDBへ切り替え可能にする

このSkillは、
要件・ACを独自に変更するためのものではありません。


# Fundamental Rules

実装時は以下を必ず守ってください。

1. 要件定義成果物全体を確認する
2. FRだけでなく、実装に影響する他の要件も確認する
3. 要件を理由なく未実装のまま残さない
4. 要件の明示的な制約を実装前に確認する
5. 要件の明示的な制約と異なる方式を独自に採用しない
6. Out of Scopeを実装しない
7. 根拠のない機能を追加しない
8. 要件内の実装選択は実装し、必要な根拠は実装報告へ簡潔に記録する
9. Production Codeを本番環境固有のDBへ密結合させない
10. 後続Test Agentが自動テスト可能な構造を維持する


# Inputs

要件本文・UC/AC・NFR・Steering・準備済み仕様・既存コード・親の対象範囲とrun_idを読みます。
# C0比較条件

`.github/workflow-profile.json` の `NO_DESIGN_ADDR` を変更しません。
Requirements → Implementation → Unit Test → Integration Test → FULLの順に親が制御します。
設計・ADDR工程、設計書、実装タスク表、判断文書、設計/実装引渡しGateを作成・要求・再利用しません。
詳細は `docs/ai-sdlc/no-design-comparison.md` を正とします。
共通Criterion内の設計/判断文書だけに関する項目は対象外です。コードの構造・品質・安全性検査は残します。

要件内の方式選択は実装し、AC・明示制約・スコープに影響する未決だけ親へ返します。

# Procedure

## Step 1. 要件定義成果物をすべて確認する

要件定義成果物について、
最低限以下を実装観点で確認してください。

1. 用語集
2. 背景
3. 目的
4. 誰のために
5. 開発のスコープ外（Out of Scope）
6. 成功条件（Acceptance Criteria）
7. 業務フロー/ユーザーストーリー
8. 共通機能要件
9. 認証・認可
10. エラー仕様（共通）
11. 非機能要件（NFR）
12. データモデル
13. 機能要件（FR）
14. 制約条件

FRだけを読んで実装を開始してはいけません。

各項目について、
Production Codeへの影響があるか確認してください。


## Step 2. 実装対象を整理する

要件から実装対象を抽出してください。

特に以下を確認します。

- 各FR
- 各FRの入力項目
- バリデーション
- エラー条件
- 出力/挙動・完了条件
- 共通機能要件
- 認証・認可
- 共通エラー仕様
- NFR
- データモデル
- 技術制約
- 業務制約
- Acceptance Criteria

要件に記載された内容を、
「重要ではない」などの理由で独自に除外してはいけません。


## Step 3. Requirement Coverageを作成する

実装開始前に、
実装対象となるRequirementと実装状態を整理してください。

各Requirementを以下のいずれかに分類します。

### NOT_IMPLEMENTED

まだ実装されていない。

### IMPLEMENTED

今回のImplementation工程で実装した。

### VERIFIED_EXISTING

既存実装を確認し、
要件を既に満たしていることを確認した。

### BLOCKED

情報不足または矛盾により実装できない。

### DELEGATION_REQUIRED

Implementation工程以外での対応が必要。

Implementation工程完了時には、
実装対象のRequirementが原則として

- IMPLEMENTED
- VERIFIED_EXISTING

のいずれかになっている必要があります。


## Step 5. 既存実装を確認する

新しいコードを書く前に、
既存実装を検索してください。

最低限以下を確認します。

- 同じ機能が既に存在しないか
- 共通処理が存在しないか
- 既存コードの責務・規約と整合するか
- 同じデータアクセス処理がないか
- 共通エラー処理がないか
- 既存の設定方式がないか
- 既存のDB接続方式がないか

既存実装を確認せずに
重複機能を新規作成してはいけません。


## Step 8. 要件内で実装判断を行う

要件・制約を満たす方式・責務分割・DB接続方法を選んで実装します。
独立した設計書・判断文書・Task表は作りません。必要な根拠は実装報告内へ簡潔に記録します。
仕様の曖昧さが観測可能な期待結果を変える場合はREQUIREMENT_ERRORとして親へ返します。

## Step 9. Production Codeを実装する

要件、制約、要件の明示的な制約に従って
Production Codeを実装してください。

実装時は以下を確認してください。

- FRを満たす
- Acceptance Criteriaを満たせる
- 共通機能要件を満たす
- 認証・認可要件を満たす
- エラー仕様を満たす
- 必要なNFRを反映する
- データモデルと整合する
- 業務制約を守る
- 技術制約を守る
- Out of Scopeを実装しない
- 要件の明示的な制約を守る
- 要件の明示的な制約を守る


## Step 10. DBアクセスをテスト可能な構造にする

DBを利用するProduction Codeは、
単体テストおよび結合テストにおいて
Dockerコンテナ等で起動する一時的なテストDBへ
接続できる構造としてください。

Production環境のDBへ固定依存してはいけません。


## Step 11. DB接続情報を外部化する

DB接続に必要な情報を
Production Codeへハードコードしてはいけません。

最低限以下を外部から設定可能にしてください。

- Host
- Port
- Database Name
- User
- Password
- その他接続に必要な値

既存プロジェクトで採用されている
設定方式を優先してください。

例:

- 環境変数
- 設定ファイル
- Dependency Injection

既存方式がなければ、要件・制約内で必要十分な設定方式を選んで実装します。
要件そのものを変更する必要がある場合はREQUIREMENT_ERRORとして親へ返します。


## Step 12. テスト用DBへの差し替え可能性を確認する

以下を確認してください。

- Production DBとテストDBの接続先を切り替えられる
- Dockerコンテナ等で割り当てられたHost/Portを利用できる
- Production Credentialがなくてもテストできる
- Production DBがなくてもテストを実行できる
- テスト環境ごとに独立したDBを利用できる
- テスト終了後に破棄可能なDBを利用できる

以下は禁止します。

- Production DBエンドポイントのハードコード
- Production Credentialへの必須依存
- 固定された共有テストDBへの必須依存
- Productionデータが存在することを前提とした実装


## Step 13. DB Schemaを再現可能にする

DB Schemaが必要な場合、
Dockerコンテナ等のテストDBへ
同じSchemaを再現できるようにしてください。

既存プロジェクトにMigration方式がある場合は、
その方式を使用してください。

例:

- Flyway
- Liquibase
- Prisma Migration
- ORM Migration
- SQL Migration

既存方式がなければ、要件・制約内で必要十分なMigration方式を選んで実装します。
その選択が要件・ACの変更を必要とする場合はREQUIREMENT_ERRORとして親へ返します。


## Step 14. DB初期状態への依存を避ける

Production Codeは、
特定のテストデータやProductionデータが
事前に存在することを前提にしてはいけません。

以下を避けてください。

- 固定IDへの依存
- Productionデータへの依存
- 特定の共有DB状態への依存
- テストから初期化できない永続状態への依存

テストデータそのものの作成は、
後続Test Agentの責務です。


## Step 15. Testabilityを確認する

後続のUnit Test AgentおよびIntegration Test Agentが
Production Codeを自動テストできることを確認してください。

以下のようなテスト困難な実装を避けてください。

- 環境依存値のハードコード
- 外部サービスへの固定接続
- DB接続先の固定
- 隠れたグローバル状態
- テストから差し替えられない外部依存
- 起動時にProduction環境への接続を必須とする構造

テストしやすくするために
要件そのものを変更してはいけません。


## Step 16. エラー処理を実装する

以下を確認してください。

- 共通エラー仕様
- FR固有のエラー条件
- バリデーションエラー
- 認証エラー
- 認可エラー
- データアクセスエラー
- 外部サービスエラー

要件で定義されたエラー条件を
正常系のみの実装で回避してはいけません。


## Step 17. 認証・認可を実装する

認証・認可要件が存在する場合は、
要件および要件の明示的な制約に従って実装してください。

特に認可について、
Frontend側の表示制御だけで
満たしたことにしてはいけません。

要件の明示的なセキュリティ制約を必ず遵守してください。


## Step 18. NFRを実装へ反映する

NFRを
後続テストで確認するだけの項目として扱ってはいけません。

Production Codeの実装に影響するNFRについては、
必要な実装を行ってください。

Implementation工程だけでは対応できないNFRについては、
DELEGATION_REQUIREDとして記録してください。


## Step 19. Requirement Coverageを再確認する

実装後、
Step 3で作成したRequirement Coverageを更新してください。

各Requirementについて以下を確認します。

- IMPLEMENTED
- VERIFIED_EXISTING
- BLOCKED
- DELEGATION_REQUIRED

未確認のRequirementを残してはいけません。


## Step 20. 作成時に参照を記入する

作成と同時に `# trace: FR-001` 等の実在要件IDを先頭に記入します。Djangoは同形式のテンプレートコメントです。
ACは要件IDと併記できます。複数ID・複数トップレベル定義なら各定義直前にも部分集合を記入します。
詳細はTraceability Skillに従い、表・Mapは手編集しません。架空のTask/判断IDは作りません。
ユーザーが依頼したコミットだけを行い、実在要件/CRの接頭辞を使います。

## Step 21. Build Validationを実行する

プロジェクトに存在する
Build・Compile・静的検証を実行してください。

利用可能な場合は以下を確認します。

- Formatter
- Linter
- Type Check
- Compile
- Build

既存テストが存在する場合は、
Regression確認のために実行してください。

新しいテストケースを作成することは
後続Test Agentの責務です。


## Step 22. Validation Errorを処理する

Buildまたは既存テストが失敗した場合、
原因を確認してください。

### IMPLEMENTATION_ERROR

Production Codeの実装ミス。

Implementation工程内で修正してください。

### REQUIREMENT_ERROR

要件の矛盾・不足が原因。

要件を勝手に変更せず、
BLOCKEDとして返してください。

### ENVIRONMENT_ERROR

実行環境または外部依存が原因。

原因と影響を記録してください。


## Step 23. Retryを制御する

同一原因に対する修正を
無制限に繰り返してはいけません。

同一原因について3回修正しても
BuildまたはValidationが成功しない場合は、
FAILEDと実施履歴をSDLC Orchestratorへ返してください。親が共通台帳へ未解決を記録して次工程へ渡します。

以下を記録してください。

- 原因
- 実施した修正
- 各修正結果


# Requirement Coverage Check

Implementation工程完了前に、
要件定義成果物をもう一度確認してください。

以下を確認します。

- Acceptance Criteria
- 共通機能要件
- 認証・認可
- エラー仕様
- NFR
- データモデル
- FR
- 制約条件

「FRをすべて実装した」だけで
実装完了と判断してはいけません。


# Database Testability Check

DBを使用する場合、
最低限以下を確認してください。

- DB接続設定が外部化されている
- Docker等のテストDBへ接続できる
- Production DBへの固定依存がない
- Production Credentialへの固定依存がない
- SchemaをテストDBへ再現できる
- テストデータを独立して投入可能である
- テスト終了後にDBを破棄してもProduction Codeに影響しない

DBを使用しない場合はNOT_APPLICABLEとして扱ってください。


# Prohibited Actions

以下を禁止します。

- 要件を理由なく未実装にする
- FRだけを実装して全要件実装済みと判断する
- 要件定義成果物を勝手に変更する
- 要件の明示的な制約を勝手に変更する
- 要件の明示的な制約を無視する
- 要件・ACを無断で変更する
- Out of Scopeの機能を実装する
- 根拠のない機能を追加する
- DB接続情報をハードコードする
- Production DBをテストに必要とする
- 共有DBの状態へテストが依存する構造にする
- テストを通すために要件を変更する
- テストを通すために要件の明示的な制約を無視する
- 次工程のAgentを直接起動する


# Completion Check

Implementation Skillを完了する前に、
以下をすべて確認してください。

- 要件定義成果物全体を確認した
- 実装対象Requirementをすべて確認した
- 各Requirementの実装状態を確認した
- 必要なRequirementを実装した
- 既存実装については実際にコードを確認した
- 要件の明示的な制約を確認した
- 要件の明示的な制約を遵守した
- Out of Scopeを実装していない
- Requirementと実装箇所を紐づけた
- DB利用時のTestabilityを確認した
- BuildまたはCompileが成功した
- BLOCKED事項を明示した
- DELEGATION_REQUIRED事項を明示した


# Output

処理完了後、
Implementation Agentが判断できるように
以下を返してください。

- 作成・更新・削除したファイル
- Requirementごとの実装状態
- Requirementごとの実装箇所
- Requirementごとの実装箇所・未実装理由
- BLOCKED事項
- DELEGATION_REQUIRED事項
- DB Testability確認結果
- Build結果
- 既存テスト実行結果
- 要件の明示的な制約遵守確認結果
- Out of Scope確認結果
- ASSUMPTION

## 共通3回ループ

修正・再検査は `docs/ai-sdlc/bounded-repair-loop.md` に集約します。
初回失敗0＋実修正1〜3の後も残る場合、FAIL/BLOCKEDを維持して親へ未解決として返し、
親が履歴・影響を記録して次工程への継続を許可します。4回目を自己開始しません。
未解決継続を品質SUCCESS/PASSへ変換せず、原因を隠す修正・捏造・削除・skipをしません。
