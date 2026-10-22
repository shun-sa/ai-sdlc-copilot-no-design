# AI SDLC Copilot — C0比較実験環境

## この環境の工程

**Requirements → Implementation → Unit Test → Integration Test → Final Assurance**

固定Profileは `NO_DESIGN_ADDR`（条件ID C0）です。
設計（Architecture）とADDRの2工程だけを除いた比較条件です。
設計あり環境の上書き版ではなく、別の空ディレクトリへ展開してください。

- 要件テンプレート・Project AI Steering・要件IDは現行と同じです。
- Implementationは要件・制約から直接実装します。設計書・実装タスク一覧・判断文書・引渡しGateは作りません。
- Unit/IntegrationのPolicy・Criterion・Validator、独立Quality/Securityレビューを維持します。
- 初回失敗＋最大3回の修正・再検査後、未解決を記録して次へ進む規則を維持します。
- 工程時間・手戻り・分岐網羅・結合項目・受入合格率の記録、reportsのGit管理を維持します。
- 受入試験の外部シート準備・人の承認・凍結・実行は開発終了後だけです。

## 開始方法

1. Agent環境一式を新しい空の作業先へ展開し、Agent資産を確認・確定します。
2. 実験用ブランチを作った後、既存の `02-minicommerce-requirements.zip` を展開します。
3. 要件確認を終えた新しい開発チャットで `SDLCOrchestrator` にImplementationからの開始を依頼します。
4. Architecture Agent / ADDR Agentは起動しません。入口はこの配布物から除いています。
5. 外部結合ケースの有無は人が選択し、Hidden Acceptance入力は開発中に置きません。
6. reportsは実験ブランチに保存し、実験データをmainへマージしません。

```text
python .github/workflow_profile.py --repo-root .
```

実要件・アプリ・実験結果・外部評価シートはこのAgent配布物に含みません。
以前の実装、設計、判断、reports、DBを持ち込んで比較条件を混在させないでください。

## Agent Roles

| Agent | C0での責務 |
| --- | --- |
| SDLCOrchestrator | 工程制御、検査、3回ループ、工程記録 |
| Requirements | 準備済み入力を既存の分割テンプレートへ再構成 |
| Implementation | 要件・制約内の方式選択とProduction Code実装 |
| UnitTest | 要件から単体試験、実JUnit・分岐計測 |
| IntegrationTest | 独立INITIAL、外部ケース照合、GAP_FILL、実結合試験 |
| QualityReview | 対象工程の品質・要求/コード/テスト整合性 |
| SecurityReview | 共通の安全性・認証認可・秘密管理等の検査 |
| TraceabilityAuditor | 実在要件→コード→テストの注釈検査、派生物生成・独立再計算 |
| FailureTriage | 3回修正後の原因分析と助言。修正回数を追加しない |
| AcceptanceTestExecutor / AcceptanceTestPrepare | 開発後の外部受入表準備、人の承認・凍結、実行 |
| Evaluation | 開発終了後の独立評価 |

専門AgentのSUCCESSは工程全体の品質PASSではありません。
設計・ADDRに対応する検査だけを対象外とし、残るGateや人の判断を省略しません。
内部の旧互換ライブラリ/テンプレートは共通回帰試験用に残りますが、実施工程ではありません。

## 記録と比較

C0は「実装開始→最後の有効な結合試験終了」を測ります。
設計あり条件は「設計開始→結合終了」であり、共通名は「要件確定後→結合終了」として開始工程を併記します。
除外工程は `null / EXCLUDED_BY_PROFILE`。0秒の実施済み工程と混同しません。
トークンはVSCode側で取得し、両条件とも要件確認後から揃えて測定してください。
計測のSTALE/INVALIDをC0だけで修正していないため、未確認値は確定値として比較しません。

## ガイド

- [C0比較条件・変更範囲・起動例](docs/ai-sdlc/no-design-comparison.md)
- [実験記録の共通契約](docs/ai-sdlc/experiment-measurement.md)
- [共通3回修正ループ](docs/ai-sdlc/bounded-repair-loop.md)
- [実験結果のGit管理](docs/ai-sdlc/experiment-git-workflow.md)

このREADMEとC0ガイドが本環境の工程契約です。
設計あり環境のガイドは互換検証・履歴参照用であり、C0へ工程を追加する指示ではありません。
