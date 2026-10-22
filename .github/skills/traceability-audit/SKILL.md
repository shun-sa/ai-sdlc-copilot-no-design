---
name: traceability-audit
description: >
  成果物内のID参照とtrace注釈を正本としてC01〜C11を機械検査し、
  Trace Mapと3種の表を再生成する。元成果物は修正せず原因工程へ返す。
user-invocable: false
disable-model-invocation: false
---

# Traceability Audit Skill

## C0の正本と境界

正本は分割要件本文・UC/AC・CRのID参照と、コード・テストのtrace注釈です。
requirements.mdは派生索引、Steeringはプロジェクト文脈でありID定義に数えません。
Requirements → Implementation → Unit Test → Integration Testで進め、設計/ADDRの成果物・Gateは作りません。
詳細はdocs/ai-sdlc/no-design-comparison.md、固定条件は.github/workflow-profile.jsonです。
実効Policyはworkflow_profile.effective_policyが適用します。共通Policyや閾値は変更しません。
元成果物はProducerが修正し、Auditorはoutputs.dir内の派生物だけを再生成します。
AST/FQN・意味推論で根拠を補わず、既存IDを改番しません。

## 作成時の参照

- Production/Testの先頭へ `# trace: FR-001` 等の実在要件IDを記入します。Djangoは同じtraceのテンプレートコメントです。
- ACは要件IDと併記します。ACだけではテストの要件参照を満たしません。
- Python先頭IDが2つ以上かつトップレベルclass/defが2つ以上なら、private/helperを含む全定義直前（decoratorより前）へ先頭の部分集合を記入します。
- 架空の設計・判断・Task IDを作りません。依頼されたコミットだけ、実在要件/CRを件名の接頭辞にします。

## 実行

Python 3.10以上とPyYAMLを使います。ScopeはREQUIREMENTS / IMPLEMENTATION / UNIT_TEST / INTEGRATION_TEST / FULLです。
設計/ADDR Scopeは拒否します。古い設計成果物のある作業先も拒否します。

```text
python .github/skills/traceability-audit/scripts/trace_check.py --scope IMPLEMENTATION
python .github/skills/traceability-audit/scripts/trace_check.py --scope IMPLEMENTATION --no-write
```

生成後、同一Scope・Policy・コミット範囲の--no-writeで独立再計算します。
--no-writeはvalidation-result.json以外を修復しません。
--commits main..HEADは任意C08入力です。未指定は未監査であり合格の証拠ではありません。
終了値0=PASS、1=FAIL、2=入力/設定エラーです。継続には別途共通3回ループの判定が必要です。

| 検査 | C0での扱い |
| --- | --- |
| C01 | ID実在・重複。設計Gateは要求しない |
| C02/C03/C04/C09 | EXCLUDED_BY_PROFILE：設計/判断/Task工程が存在しない |
| C05 | 先頭注釈、許可種別は実在要件/AC |
| C06 | 定義注釈と先頭の整合 |
| C07 | テストの要件参照 |
| C08 | コミットの実在要件/CR接頭辞（警告） |
| C10 | FR/NFR/SECのテスト漏れ。元のScope別強度を維持 |
| C11 | 保存済み派生物と再計算の一致 |

## テスト結果と実行版

JUnit XMLは各テスト担当が実際にテストを実行して生成します。
直後、成果物を変更する前に次でその入力とJUnitのSHA-256を結び付けます。
このコマンド自体はテストを実行しません。過去のJUnitを現在の実行結果として登録してはいけません。

```text
python .github/skills/traceability-audit/scripts/trace_check.py --record-test-run unit_test
python .github/skills/traceability-audit/scripts/trace_check.py --record-test-run integration_test
```

結果は各reports/<test>/trace-execution.jsonです。
確認表は記録された実行版のみを使用し、現在HEADをテスト実行版として代入しません。
実行記録なし・入力/JUnitハッシュ不一致・未実行・skipは充足にしません。
JUnitは役割と正確なモジュール名・テスト名で照合し、同名別ファイルのPASSを流用しません。
Integration Planのrequirement_id/related_adrは既存契約名を維持し、実在要件IDを使い、related_adrは空配列または既存Schemaのnullとします。
外部ケースを改変したり計画だけを実行成功と見なしたりしません。

## 派生成果物

reports/traceability/以下に生成します。

- trace-map.json: version=3、elements/sources/integration_test_casesと入力ハッシュ
- traceability-report.json/.md: 機械検査の結果・Issue・Coverage・注釈量
- requirements-traceability-matrix.md/.csv: 要件→判断/設計/実装/テスト/AC
- requirements-traceability-check.md/.csv: UNIT_TEST以降、実行版・JUnit結果・確認判定
- addr-index.md/.csv: 判断別の参照一覧
- validation-result.json: 既存Assurance契約のstatus/audit_scope/errors/warnings、
  source_baseline_sha256（C0はnull）、issues、workflow_profile、excluded_checks

Semantic Reviewは任意の別文書semantic-review.mdに助言として記録します。
traceability-reportの機械statusやvalidation-resultを意味判断で上書きしません。
Trace PASSは仕様の意味的充足・品質・安全性やテスト成功を保証しません。
独立したQuality/Security/Test ValidatorのGateは従来どおり必須です。

## 差戻し・完了

validation-resultのissues[].routeとclassification/locationを親へ返します。
REQUIREMENTS、IMPLEMENTATION、UNIT_TEST、INTEGRATION_TESTの原因工程が修正します。
要求の不備はRequirements、実装選択/コードの不備はImplementationへ親が振り分けます。
変更後は影響する検査と下流を再検証します。ADDR別一覧は互換出力として空であり、判断を捏造しません。
TRACEABILITY_REGENERATEはAuditorが現在の正本から派生物のみを再生成します。

同じ原因を3回修正しても残れば、共通ループ台帳の未解決結果を親へ返し、継続判定で次工程へ進みます。
検査PASSは生成・独立検証とも成功した場合のみです。工程継続と区別します。
台帳のUNRESOLVEDを機械Reportと確認表へ投影し、該当要件の判定は「未解決あり」にします。
OBSERVEによる履歴更新だけでC11を再び古くしないよう、派生Mapには安定した未解決状態を記録します。
