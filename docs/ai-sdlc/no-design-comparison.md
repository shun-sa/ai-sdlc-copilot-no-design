# C0：設計・ADDRを除いた比較実験環境

## 比較条件

基準は04-experiment-reports-git-update適用後の共通Agent資産です。
Requirements → Implementation → Unit Test → Integration Test → FULLで開発します。
変更因子は設計・ADDR工程の有無です。要件を簡略化したり、品質・安全性・テスト閾値を下げる実験ではありません。

| 項目 | 設計あり（既存環境） | C0（この環境） |
| --- | --- | --- |
| 要件・テンプレート・Steering | 現行 | 同一、02の入力を使用可能 |
| Architecture / ADDR | 独立した2工程 | 非実施、Agent/Skill入口を削除 |
| 設計書・Task・判断・Gate | 生成・検証 | 生成・要求・再利用しない |
| 実装方式選択 | 設計・判断に従う | 要件・制約内で実装担当が行う |
| 要求の曖昧さ・矛盾 | 要件へ差し戻し | 同じ。実装選択だけなら要件へ押し戻さない |
| Unit / IntegrationのPolicy・Criterion・Validator | 現行 | 同一 |
| 品質・安全性・横断整合性 | 独立検査 | 同じ。存在しない設計文書のみ対象外 |
| 共通ループ | 初回失敗＋最大3回修正 | 同一。未解決とFAILを残して継続 |
| 受入表準備・人の承認・固定・実行 | 現行 | 同一 |
| 記録・reportsのGit管理 | 現行 | 同一 |

設計工程を別名の計画・判断Agentへ移しません。Implementationは実装に必要な選択をコードへ反映し、
必要な根拠を実装報告内に簡潔に残すだけです。要件・AC・Out of Scope・明示制約は勝手に変えません。

## 実効PolicyとValidator

`.github/workflow-profile.json` を固定条件とし、`.github/workflow_profile.py` が実効Policyを適用します。
共通Policyファイルは元のまま保持し、比較条件と無関係な閾値変更を防ぎます。

- 許可Scope：REQUIREMENTS / IMPLEMENTATION / UNIT_TEST / INTEGRATION_TEST / FULL。
- 設計・ADDRの必須Check、戻り先、ADR_REQUIRED分類は対象外。
- Quality/Security/FailureTriageのJSONには `workflow_profile: NO_DESIGN_ADDR` を必須とする。
- Qualityのarchitecture-qualityは `applicable: false`, `result: NOT_APPLICABLE` と除外理由を必須とする。PASSにしない。
- 共通Criterionの「Accepted ADR」など設計文書にしか適用されない条項は対象外。要件の制約、実コードの品質・構造、安全性、テストの期待値整合性は検査する。
- TraceのC02/C03/C04/C09だけを対象外とし、Reportに除外理由を出す。C01/C05/C06/C07/C08/C10/C11は元のScope別強度で維持する。
- コード・テストは実在要件IDを直接参照する。ACは併記可能。複数要件・複数定義の注釈、JUnit実行版、派生物独立検証は維持する。
- コミット依頼時だけ実在要件/CRを接頭辞にする。Task IDを捏造しない。
- 結合計画の互換欄related_adrは空配列または既存Schemaのnull。判断IDを作らない。
- `docs/architecture`, `docs/addr`, `docs/adr`, `reports/architecture`, `reports/addr` にファイルがある作業先は拒否する。

設計・ADDRのPython内部ライブラリ/テンプレートと旧互換の回帰試験は残っていますが、Agent/Skill入口はありません。
これらは共通パーサーの互換検証用で、C0の入力・実施工程ではありません。両ValidatorのCLIもC0では明示的に拒否します。
旧設計ありガイドは履歴参照専用であり、この環境で工程を追加する指示ではありません。

## 計測

要件確認後、最初のImplementation委譲直前に開始します。計測器がC0と除外工程を自動記録し、Run途中の条件変更を拒否します。

```text
python .github/workflow_profile.py --repo-root .
python .github/skills/evaluation/scripts/experiment_recorder.py start --run-id RUN-C0-001 --condition-id C0 --phase IMPLEMENTATION
```

主区間は実装開始→最後の有効な結合試験終了です。設計ありの「設計開始→結合終了」とは開始工程が違うため、
共通の比較名は「要件確定後→結合終了」とし、条件・開始工程を必ず併記します。
除外工程はnull / EXCLUDED_BY_PROFILEであり、0秒として実施済み扱いしません。
工程別時間、実際の差し戻し元/先/回数、分岐網羅、INITIAL/計画/結果、受入合格率は既存記録方式です。
トークンはVSCodeで別途取得し、要件確認を除く開始点を両条件で揃えてください。

既存環境で見つかったSTALE/INVALID、計画と実行結果の件数不一致、固定INITIALの差分等の検証ロジックは、
C0だけで修正していません。今回の変更はその問題を解消したという意味ではありません。
計測が未確認なら数値を比較の確定値として使わず、両条件を同じ計測修正版で再実行する等の統一対応が必要です。

## 開始手順と分離

1. この環境一式ZIPを**新しい空の作業先**へ展開する。既存の設計あり環境やreportsの上へ上書きしない。
2. Agent資産だけを確認・確定し、その後に実験用ブランチをユーザーが作成する。
3. 同じ02-minicommerce-requirements.zipを展開する。共通の入力版・要件IDを変えない。
4. 言語/DB/テスト実行環境、モデル、予算、外部結合項目の提示タイミング等を設計あり条件と揃える。
5. 要件確認後、SDLCOrchestratorへImplementationからの開始を明示する。Architecture Agentは起動しない。
6. 実行後、reportsを実験ブランチへ保存する。mainへマージしない。受入表は開発中にリポジトリへ入れない。
7. 開発終了後にAcceptanceTestExecutorへ同じ外部受入表を渡し、準備・人の承認・凍結・実行を既存手順で行う。

Gitブランチだけでは過去の評価やDBを隔離できません。厳密な比較では履歴・既存実装・過去reports・DBを共有しない実行先を用意します。
既存02には変換確認用reportsが含まれますが、過去の開発/評価結果を混入させないでください。
本配布物には実要件、実装、実験結果、外部受入表を同梱しません。既存の設計あり環境は変更していません。

## 起動依頼の例

「C0比較条件で開発してください。要件確認は完了済みです。分割要件本文・UC/AC・Steeringを読み、
設計・ADDR工程を実行せずImplementationから開始してください。run_idはRUN-C0-001とし、
以後の全工程・差し戻し・検査・計測・3回修正後の未解決継続は既存契約に従ってください。
受入試験は開発終了後に別途指示します。」
