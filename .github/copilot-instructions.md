# Project-wide Copilot Instructions

## Purpose

このRepositoryでは、
AIによるRequirements、Implementation、
Unit Test、Integration Testまでの
一気通貫Software Development Lifecycleを実行する。

各工程の具体的な作業手順は
Custom AgentおよびSkillに定義する。

このFileには、
すべてのAgentが常に遵守すべき
Project-wide invariantのみを定義する。


# SDLC Control

SDLC全体の工程制御は
SDLC Orchestratorのみが担当する。

専門Agentは自身の工程完了後、
次工程を直接起動してはいけない。

専門Agentは結果をSDLC Orchestratorへ返却する。

各工程のSUCCESSは
専門Agent自身の処理完了を意味し、
工程全体のPASSを意味しない。


# Phase Order

# C0比較条件

`.github/workflow-profile.json` の `NO_DESIGN_ADDR` を変更しません。
Requirements → Implementation → Unit Test → Integration Test → FULLの順に親が制御します。
設計・ADDR工程、設計書、実装タスク表、判断文書、設計/実装引渡しGateを作成・要求・再利用しません。
詳細は `docs/ai-sdlc/no-design-comparison.md` を正とします。
共通Criterion内の設計/判断文書だけに関する項目は対象外です。コードの構造・品質・安全性検査は残します。
要件の未決事項も、実施する工程の担当またはOwnerへ割り当てます。存在しない判断文書を解決先にしません。

# Experiment Measurement

実験時の工程境界・実行証跡は `docs/ai-sdlc/experiment-measurement.md` に従って記録する。
主工程の開始・終了・実際の差し戻しはOrchestratorが記録し、子Agentへ同じrun_idを渡す。
UnitTestは分岐計測付き実コマンドを記録器経由で実行し、IntegrationTestはINITIAL/計画/結果を保存する。
観測用Scriptの開発中実行だけを認め、Evaluation/AcceptanceTestExecutorの開発中起動や
Hidden Acceptance入力の早期公開は認めない。取得できなかった時間・網羅率・合格率・トークン数を推測しない。
AcceptanceTestPrepareも開発中には起動しない。開発完了後のAcceptanceTestExecutor専用準備担当とし、
外部表の条件を変えず外部テストへ翻訳する。人の明示承認・凍結前の評価実行は認めない。
計測結果は品質Gateや共通3回ループを変更せず、未解決継続と品質PASSを区別する。
実験結果はreportsを含め実験ブランチでGit管理し、実験後のデータをmainへマージしない。
開発Agentは他Runや過去の評価ブランチのreports・Hidden Acceptance入力を参照しない。
Gitのブランチはアクセス権の隔離ではない。厳密な非公開評価では実験ごとに過去評価履歴のない実行環境を使う。

# Source of Truth

RequirementのSource of Truthは
Requirements成果物とする。

要件定義の構造は `.github/skills/requirements/templates/` の分割テンプレートと
`.github/project-context/templates/project-ai-steering.md` を正本とする。
`docs/requirements/requirements.md` は分割成果物とFR/NFRへの派生索引である。
すべてのAgent/Assuranceはリンク先の本文とUC詳細を読み、AC / Pass-Fail RuleはUC詳細を正本とする。
PJ固有情報は `.github/project-context/project-ai-steering.md` を参照する。
Steeringへ要求本文やFramework共通手順を複製しない。

Production Codeの現在の挙動を
Requirementの代わりに使用してはいけない。

Testの期待結果を
Production Codeから逆算してはいけない。


# Requirements Structure

Requirements Templateの構成を
変更してはいけない。

Sectionの追加、削除、名称変更、
順序変更を行ってはいけない。

Requirement IDを
後続工程の都合で変更してはいけない。


# Implementation Decisions

実装に必要な方式選択は要件・制約の範囲内でImplementationが行います。
要件・AC・明示制約の意味を変える場合だけ親経由でRequirementsへ戻します。
別名の設計Agentや判断Agentを追加せず、独立した設計/判断成果物を要求しません。

# Implementation

Implementationは
Requirements全体および明示制約に従う。

FRだけでなく、
Acceptance Criteria、
共通機能要件、
認証・認可、
Error仕様、
NFR、
Data Model、
Constraint、
Out of Scopeを確認する。

Out of Scopeを
利便性やBest Practiceだけを理由に実装してはいけない。


# Database Testability

Databaseを利用するProduction Codeは、
Production Databaseへ固定依存してはいけない。

TestではProduction Database、
Production Credential、
Production Dataを使用してはいけない。

必要に応じてDocker Container等の
Disposable Test Databaseを使用可能な構造とする。


# Test Expectations

Unit TestおよびIntegration Testの期待結果は
Requirementsおよび要件の明示的な制約から導出する。

TestをPASSさせる目的で
Expected ResultをProduction Codeへ合わせてはいけない。

Failureを隠す目的で
Testを削除、skip、無効化、
Assertion弱体化してはいけない。


# 共通ループ基本方針（工程遷移では本節を優先）

全工程・全Agentに、`docs/ai-sdlc/bounded-repair-loop.md` と
`.github/skills/failure-triage/policy/loop-policy.json` を適用します。
同一原因の初回失敗はcycle=0。その後の修正・再検査を最大3回行い、
3回後も残ればUNRESOLVEDとして検査結果へ記録し、CONTINUE_WITH_UNRESOLVEDで次工程へ進めます。
担当Agentや工程を変えて回数をリセットせず、4回目の修正ループは開始しません。

検査FAIL、未実行、未承認判断をPASS/成功へ書き換えません。
通常の品質Gateは残し、工程継続はOrchestratorが別の継続判定で許可します。
旧来の「すべてPASSまで停止」「未解決の持越し禁止」は品質PASSの条件として読み、
工程継続については3回後の記録・継続規則を優先します。正本・期待値・外部ケースの改変、
失敗テストの削除/skip、欠落資料・設計判断の捏造で回避しません。
依存して実行不能な作業は未実行と影響を残し、実行可能な後続作業を進めます。
この許可は本番反映・不可逆操作・権限やユーザー承認の代替ではありません。

実行履歴と未解決結果はreports/loop-controlへ保存します。
後続Agentへissue ID・影響・根拠・推奨対応先を渡し、既知の未解決原因を新しい3回ループにしません。
最終結果に未解決が残る場合はCOMPLETE_WITH_UNRESOLVEDとし、COMPLETE/PASSと区別します。

# Error Carry Forward

既知のErrorは黙って持ち越さない。3修正後も残る場合は共通ループ方針で記録して引き継ぐ。

Production CodeのErrorは
Implementation Agentで修正する。

Test CodeのErrorは
対象Test Agentで修正する。

要件の意味・AC・明示制約の不足はRequirementsへ、要件内の実装選択の不備はImplementationへ戻す。

Requirementの問題は
Requirements工程へ戻す。

修正後は、
影響するTestおよびValidatorを
必ず再実行する。


# Upstream Change Invalidation

上流成果物を変更した場合、
変更前に取得した後続工程のPASSを
自動的に有効とみなしてはいけない。

Requirements変更:
Implementation以降を再検証する。

Production Code変更:
影響するUnit TestおよびIntegration Testを再実行する。


# External Integration Test Cases

External Integration Test Caseは
実験用評価データとして扱う。

External Caseの意味、
Input、
Steps、
Expected Resultを
AIの都合で変更してはいけない。

External Caseは
origin=EXTERNALとして管理する。

AI生成Caseは
origin=AI_GENERATEDとして管理する。

AI INITIAL Caseは
External Caseを確認する前に生成・固定する。

External Case確認後に
AI INITIAL Caseを書き換えてはいけない。

Coverage Gap補完Caseは
AI GAP_FILLとして区別する。

External Test Caseが配置されていない場合、
AI自身の判断でExternal Caseなしとして
処理を継続してはいけない。

External Caseなしで処理を継続する場合は、
ユーザーによる明示的な確認が必要である。

External Case未配置と、
ユーザーがExternal Caseなしを明示的に選択した状態を
同一として扱ってはいけない。


# Deterministic Validation

Validatorが存在する工程では、
Validator結果を工程Gateとして使用する。

ValidatorがFAILしている状態で
品質PASSとしてはいけない。工程継続は共通3回ループの別判定を使用する。

AIの自己評価を
Deterministic Validatorの代わりにしてはいけない。


# Traceability


要件→コード→テストの実在IDを直接参照します。ACは要件IDと併記できます。
Production/Testの先頭に `# trace: FR-001` 等を記入し、複数要件・複数定義時の注釈規則を維持します。
設計/判断IDを捏造せず、C02/C03/C04/C09はEXCLUDED_BY_PROFILEとして検査母集団から外します。
C01/C05/C06/C07/C08/C10/C11は維持します。実JUnit直後の実行版記録も必須です。
原因成果物は担当工程が修正し、Auditorは派生物だけを再生成します。

実際のJUnit直後にtrace_check.py --record-test-run <role>で実行版を記録します。
監査は同条件で生成と--no-writeを行い、古い実行証拠を流用しません。
依頼されたコミットだけ、実在要件/CRの接頭辞を使います。

# Security

Credential、
Secret、
Production Token、
Production Dataを
Source CodeまたはTest Dataへハードコードしてはいけない。

Security Requirementおよび
要件の明示的な制約のSecurity Guardrailを遵守する。


# Repository Independence

Git hosting service、
CI/CD service、
Cloud providerを
明示的なRequirementまたは要件の明示的な制約なしに仮定しない。

GitHub Actions等の
特定CI/CD機能への依存を
暗黙的に追加してはいけない。


# Responsibility Separation

Agent:
責務、境界、Input、Outputを定義する。

Skill:
具体的な実行方法を定義する。

Template:
成果物の構造を定義する。

Policy:
合否基準を定義する。

Criterion:
試験観点を定義する。

Validator:
機械的に判定可能なGateを定義する。

同じ詳細手順を複数箇所へ重複定義しない。


# Final Principle

不確実な内容を
暗黙の事実として確定しない。

解消可能な場合は
既存Requirement、Code、Testを確認する。

解消できない重要事項は
ASSUMPTION、BLOCKED等の
明示的な状態として扱う。
