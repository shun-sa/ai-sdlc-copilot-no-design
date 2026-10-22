from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml

import experiment_recorder as recorder


ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / ".github"))
import workflow_profile as profile


def module(name, relative):
    specification = importlib.util.spec_from_file_location(name, ROOT / relative)
    result = importlib.util.module_from_spec(specification)
    sys.modules[name] = result
    specification.loader.exec_module(result)
    return result


trace = module("comparison_trace", ".github/skills/traceability-audit/scripts/trace_check.py")
loop = module("comparison_loop", ".github/skills/failure-triage/scripts/loop_control.py")
quality = module("comparison_quality", ".github/skills/quality-review/scripts/validate_quality_review.py")
security = module("comparison_security", ".github/skills/security-review/scripts/validate_security_review.py")
triage = module("comparison_triage", ".github/skills/failure-triage/scripts/validate_failure_triage.py")
quality_fixtures = module("comparison_quality_fixtures", ".github/skills/quality-review/scripts/test_validate_quality_review.py")
security_fixtures = module("comparison_security_fixtures", ".github/skills/security-review/scripts/test_validate_security_review.py")


class ComparisonTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.write(profile.PROFILE_PATH, profile.EXPECTED)
        self.tick = 0

    def write(self, relative, value):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value if isinstance(value, str) else json.dumps(value), encoding="utf-8")
        return path

    def policy(self, kind):
        name = "loop-policy.json" if kind == "loop" else kind + "-policy.yaml"
        directory = {"loop": "failure-triage", "traceability": "traceability-audit"}.get(kind, kind)
        path = ROOT / f".github/skills/{directory}/policy/{name}"
        return json.loads(path.read_text(encoding="utf-8")) if kind == "loop" else yaml.safe_load(path.read_text(encoding="utf-8"))

    def event(self, kind, payload=None):
        self.tick += 10
        clock = lambda: ((datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=self.tick)).isoformat(), self.tick * 1_000_000_000)
        return recorder.append(self.root, "RUN-C0", f"event-{self.tick}", kind, payload or {}, clock)

    def test_fixed_profile_and_empty_workspace_pass(self):
        self.assertTrue(profile.direct(self.root))
        profile.check_workspace(self.root)
        self.assertEqual(profile.context(self.root)["excluded_phases"], ["ARCHITECTURE", "ADDR"])

    def test_profile_cannot_disable_arbitrary_checks(self):
        self.write(profile.PROFILE_PATH, {**profile.EXPECTED, "excluded_phases": ["UNIT_TEST"]})
        with self.assertRaises(ValueError):
            profile.context(self.root)

    def test_absent_profile_preserves_full_policy_identity(self):
        (self.root / profile.PROFILE_PATH).unlink()
        policy = self.policy("traceability")
        self.assertFalse(profile.direct(self.root))
        self.assertIs(profile.effective_policy(self.root, policy, "traceability"), policy)

    def test_stale_or_generated_design_artifacts_are_rejected(self):
        for directory in ("docs/architecture", "docs/addr", "docs/adr", "reports/architecture", "reports/addr"):
            with self.subTest(directory=directory):
                path = self.write(directory + "/old.md", "stale")
                with self.assertRaises(ValueError):
                    profile.check_workspace(self.root)
                path.unlink()

    def test_trace_effective_policy_only_excludes_design_checks(self):
        original = self.policy("traceability")
        before = copy.deepcopy(original)
        effective = profile.effective_policy(self.root, original, "traceability")
        self.assertEqual(original, before)
        for name in ("require_test_for", "addr_without_code"):
            self.assertEqual(effective["checks"][name], original["checks"][name])
        for scope, checks in original["checks"]["scopes"].items():
            for severity in ("fail", "warn"):
                self.assertEqual(effective["checks"]["scopes"][scope][severity], [check for check in checks.get(severity, []) if check not in {"C02", "C03", "C04", "C09"}])
        self.assertEqual(effective["code"]["allowed"], ["requirement", "acceptance"])
        self.assertFalse(effective["integration"]["preserve_architecture_gate"])

    def test_quality_severity_and_non_design_thresholds_preserved(self):
        policy = self.policy("quality-review")
        effective = profile.effective_policy(self.root, policy, "quality-review")
        for key in ("severity", "criteria", "scope", "complexity", "cross_phase"):
            self.assertEqual(effective[key], policy[key])
        self.assertFalse(quality.validate_policy(effective))

    def test_security_baseline_is_unchanged(self):
        policy = self.policy("security-review")
        effective = profile.effective_policy(self.root, policy, "security-review")
        for key in ("security", "criteria", "severity"):
            self.assertEqual(effective[key], policy[key])
        self.assertFalse(security.validate_policy(effective))

    def test_triage_excludes_removed_routes_and_preserves_remaining_invalidation(self):
        policy = self.policy("failure-triage")
        effective = profile.effective_policy(self.root, policy, "failure-triage")
        self.assertNotIn("ADR_REQUIRED", effective["classification"]["allowed"])
        self.assertEqual(effective["invalidation"]["REQUIREMENTS"], ["IMPLEMENTATION", "UNIT_TEST", "INTEGRATION_TEST"])
        self.assertFalse(set(profile.EXCLUDED) & set(effective["routes"]["allowed"]))
        self.assertFalse(triage.validate_policy(effective))

    def test_report_marker_and_excluded_routes_are_validated(self):
        self.assertTrue(profile.report_errors(self.root, {}, "security-review"))
        report = {"workflow_profile": profile.DIRECT, "issues": []}
        self.assertFalse(profile.report_errors(self.root, report, "security-review"))
        for phase in profile.EXCLUDED:
            self.assertTrue(profile.report_errors(self.root, {**report, "recommended_route": phase}, "failure-triage"))
            self.assertTrue(profile.report_errors(self.root, {**report, "issues": [{"recommended_route": phase}]}, "security-review"))

    def test_architecture_quality_must_be_na_not_fake_pass(self):
        report = {"workflow_profile": profile.DIRECT, "criteria_results": [{"criterion": "architecture-quality", "applicable": False, "result": "NOT_APPLICABLE", "reason": "C0 excludes design"}]}
        self.assertFalse(profile.report_errors(self.root, report, "quality-review"))
        report["criteria_results"][0].update(applicable=True, result="PASS")
        self.assertTrue(profile.report_errors(self.root, report, "quality-review"))

    def test_implementation_quality_fail_remains_fail(self):
        policy = profile.effective_policy(self.root, self.policy("quality-review"), "quality-review")
        report = {"criteria_results": [{"criterion": "implementation-quality", "applicable": True, "result": "FAIL"}]}
        errors, counts = quality.validate_criteria_results(report, {"implementation-quality"}, policy, "IMPLEMENTATION")
        self.assertTrue(errors)
        self.assertEqual(counts["fail"], 1)

    def review(self, kind, report):
        policy = ROOT / f".github/skills/{kind}/policy/{kind}-policy.yaml"
        report_path = self.write(f"reports/{kind}/{kind}-report.json", report)
        self.write(f"reports/{kind}/{kind}-report.md", "# Actual review\n")
        unit = self.write("reports/unit-test/validation-result.json", {"status": "PASS"})
        integration = self.write("reports/integration-test/validation-result.json", {"status": "PASS"})
        validator = quality if kind == "quality-review" else security
        return validator.validate(self.root, policy, ROOT / f".github/skills/{kind}/criteria", report_path, report_path.parent, unit, integration)

    def test_full_quality_validation_works_without_gate_and_rejects_profile_omission(self):
        report = quality_fixtures.base_report("FULL")
        report["workflow_profile"] = profile.DIRECT
        architecture = next(item for item in report["criteria_results"] if item["criterion"] == "architecture-quality")
        architecture.update(applicable=False, result="NOT_APPLICABLE", reason="C0 design stage excluded")
        report["summary"].update(criteria_pass=5, criteria_not_applicable=1)
        errors, result = self.review("quality-review", report)
        self.assertEqual(errors, [])
        self.assertEqual(result["status"], "PASS")
        del report["workflow_profile"]
        errors, result = self.review("quality-review", report)
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(any("workflow_profile" in error for error in errors))

    def test_full_security_validation_works_without_gate_and_does_not_suppress_failure(self):
        report = security_fixtures.base_report("FULL")
        report["workflow_profile"] = profile.DIRECT
        for item in report["criteria_results"]:
            if item["criterion"] == "secrets-credentials":
                item["criterion"] = "secret-credentials"
        errors, result = self.review("security-review", report)
        self.assertEqual(errors, [])
        self.assertEqual(result["status"], "PASS")
        report["criteria_results"][0]["result"] = "FAIL"
        errors, result = self.review("security-review", report)
        self.assertTrue(errors)
        self.assertEqual(result["status"], "FAIL")

    def test_active_entry_points_have_valid_frontmatter_and_no_missing_skills(self):
        for path in (ROOT / ".github/agents").glob("*.agent.md"):
            text = path.read_text(encoding="utf-8")
            self.assertTrue(text.startswith("---\n"), path)
            frontmatter = yaml.safe_load(text.split("---", 2)[1])
            self.assertIsInstance(frontmatter["name"], str)
        for name in ("implementation", "unit-test", "integration-test", "quality-review", "security-review", "failure-triage", "traceability-audit"):
            path = ROOT / f".github/skills/{name}/SKILL.md"
            text = path.read_text(encoding="utf-8")
            self.assertTrue(text.startswith("---\n"), path)
            self.assertIsInstance(yaml.safe_load(text.split("---", 2)[1]), dict)

    def prepare_trace(self):
        self.write("docs/requirements/functional_requirements.md", "# 要件\n\n- FR-001: 正常な値を返す\n")
        self.write("app/service.py", "# trace: FR-001\ndef value():\n    return 1\n")
        self.write("tests/unit/test_service.py", "# trace: FR-001\ndef test_value():\n    assert True\n")
        path = ".github/skills/traceability-audit/policy/traceability-policy.yaml"
        self.write(path, (ROOT / path).read_text(encoding="utf-8"))

    def auditor(self, scope="IMPLEMENTATION"):
        auditor = trace.Auditor(self.root, self.policy("traceability"), scope)
        auditor.load()
        auditor.check_all(None)
        return auditor

    def test_direct_requirement_code_passes_without_design_gate(self):
        self.prepare_trace()
        auditor = self.auditor()
        self.assertFalse([issue for issue in auditor.issues if issue.level == "FAIL"], auditor.issues)
        self.assertFalse((self.root / "reports/architecture").exists())

    def test_missing_annotation_still_fails(self):
        self.prepare_trace()
        self.write("app/service.py", "def value():\n    return 1\n")
        self.assertTrue(any(issue.check == "C05" and issue.level == "FAIL" for issue in self.auditor().issues))

    def test_unknown_requirement_still_fails(self):
        self.prepare_trace()
        self.write("app/service.py", "# trace: FR-999\ndef value():\n    return 1\n")
        self.assertTrue(any(issue.check == "C01" and issue.level == "FAIL" for issue in self.auditor().issues))

    def test_fake_design_id_is_not_accepted_as_evidence(self):
        self.prepare_trace()
        self.write("app/service.py", "# trace: ADDR-001\ndef value():\n    return 1\n")
        issues = self.auditor().issues
        self.assertTrue(any(issue.check == "C01" for issue in issues))
        self.assertTrue(any(issue.check == "C05" for issue in issues))

    def test_full_trace_still_fails_missing_requirement_test(self):
        self.prepare_trace()
        (self.root / "tests/unit/test_service.py").unlink()
        self.assertTrue(any(issue.check == "C10" and issue.level == "FAIL" for issue in self.auditor("FULL").issues))

    def test_trace_table_does_not_turn_unexecuted_test_into_pass(self):
        self.prepare_trace()
        auditor = self.auditor("FULL")
        outputs = trace.generated_outputs(auditor, "reports/traceability")
        self.assertIn("未実行", outputs["requirements-traceability-check.md"])

    def test_trace_generate_and_independent_validation_bind_current_policy(self):
        self.prepare_trace()
        args = trace.parse_args(["--repo-root", str(self.root), "--scope", "IMPLEMENTATION"])
        self.assertEqual(trace.run(args), 0)
        args.no_write = True
        self.assertEqual(trace.run(args), 0)
        report = json.loads((self.root / "reports/traceability/validation-result.json").read_text(encoding="utf-8"))
        self.assertEqual(report["workflow_profile"], profile.DIRECT)
        self.assertEqual(set(report["excluded_checks"]), {"C02", "C03", "C04", "C09"})
        (self.root / "reports/traceability/trace-map.json").write_text("{}", encoding="utf-8")
        self.assertEqual(trace.run(args), 1)

    def test_excluded_phase_rejected_by_trace_and_loop(self):
        self.prepare_trace()
        for phase in profile.EXCLUDED:
            with self.assertRaises(ValueError):
                self.auditor(phase)
            with self.assertRaises(ValueError):
                loop.source_snapshot(self.root, phase)

    def test_loop_preserves_all_non_design_required_checks(self):
        original = self.policy("loop")
        effective = profile.effective_policy(self.root, original, "loop")
        self.assertEqual(effective["required_checks"], {phase: checks for phase, checks in original["required_checks"].items() if phase not in profile.EXCLUDED})
        for key in original.keys() - {"required_checks"}:
            self.assertEqual(effective[key], original[key])

    def prepare_loop(self):
        path = loop.POLICY
        self.write(path, (ROOT / path).read_text(encoding="utf-8"))
        checks = {}
        for key in loop.policy(self.root)["required_checks"]["IMPLEMENTATION"]:
            relative = f"reports/checks/{key}.json"
            self.write(relative, {"status": "PASS", "audit_scope": "IMPLEMENTATION", "errors": []})
            checks[key] = relative
        self.write(checks["build"], {"status": "FAIL", "audit_scope": "IMPLEMENTATION", "errors": ["compile error"]})
        event = {"signature": {"origin_phase": "IMPLEMENTATION", "classification": "IMPLEMENTATION_ERROR", "artifact": "app/service.py", "requirement_reference": "FR-001", "test_case": "", "stable_error_type": "compile"}, "validation_result": checks["build"], "impact": "cannot compile FR-001", "recommended_route": "IMPLEMENTATION"}
        return checks, event

    def test_three_repairs_continue_without_converting_failure_to_pass(self):
        checks, event = self.prepare_loop()
        for cycle in range(4):
            loop.record(self.root, {**event, "cycle": cycle, "run_id": f"repair-{cycle}", "repair": "actual repair" if cycle else ""})
            if cycle < 3:
                with self.assertRaises(ValueError):
                    loop.phase_decision(self.root, "IMPLEMENTATION", checks)
        decision = loop.phase_decision(self.root, "IMPLEMENTATION", checks)
        self.assertEqual(decision["status"], "CONTINUE_WITH_UNRESOLVED")
        self.assertFalse(decision["quality_pass"])
        self.assertEqual(loop.verify_transition(self.root, "IMPLEMENTATION"), decision)
        self.assertEqual(json.loads((self.root / checks["build"]).read_text())["status"], "FAIL")
        with self.assertRaises(ValueError):
            loop.record(self.root, {**event, "cycle": 4, "run_id": "repair-4", "repair": "fourth"})

    def test_loop_cannot_route_to_removed_phase(self):
        _, event = self.prepare_loop()
        with self.assertRaises(ValueError):
            loop.record(self.root, {**event, "cycle": 0, "run_id": "failure", "recommended_route": "ADDR"})

    def test_measurement_defaults_to_implementation_and_records_profile(self):
        self.event("RUN_STARTED")
        payload = recorder.load_events(self.root, "RUN-C0")[0]["payload"]
        self.assertEqual(payload["phase"], "IMPLEMENTATION")
        self.assertEqual(payload["condition_id"], "C0")
        self.assertEqual(payload["workflow_profile"], profile.EXPECTED)

    def test_measurement_rejects_both_removed_phases(self):
        self.event("RUN_STARTED")
        for phase in profile.EXCLUDED:
            with self.assertRaises(ValueError):
                self.event("PHASE_ENTERED", {"phase": phase, "previous_result": "PASS"})

    def test_measurement_profile_cannot_change_during_run(self):
        self.event("RUN_STARTED")
        (self.root / profile.PROFILE_PATH).unlink()
        with self.assertRaises(ValueError):
            self.event("CHECKPOINT", {"reason": "profile changed"})
        with self.assertRaises(ValueError):
            recorder.summary(self.root, "RUN-C0")

    def test_measurement_elapsed_and_excluded_phases_are_not_zero(self):
        self.event("RUN_STARTED")
        self.event("PHASE_ENTERED", {"phase": "UNIT_TEST", "previous_result": "PASS"})
        self.event("PHASE_ENTERED", {"phase": "INTEGRATION_TEST", "previous_result": "PASS"})
        self.event("PHASE_ENDED", {"phase": "INTEGRATION_TEST", "result": "PASS"})
        self.event("RUN_ENDED", {"status": "COMPLETE", "source_fingerprint": recorder.source_fingerprint(self.root)})
        result = recorder.export(self.root, "RUN-C0")
        self.assertEqual(result["time_window"]["elapsed_seconds"], 30)
        self.assertEqual(result["time_window"]["start_phase"], "IMPLEMENTATION")
        for phase in profile.EXCLUDED:
            self.assertEqual(result["phase_times"][phase], {"visits": 0, "seconds": None, "status": "EXCLUDED_BY_PROFILE"})
        self.assertIn("実装開始→", (self.root / "reports/experiments/RUN-C0/measurement-report.md").read_text(encoding="utf-8"))
        self.assertIsNone(result["tokens"]["value"])

    def test_measurement_counts_actual_rework_to_requirements_and_implementation(self):
        self.event("RUN_STARTED")
        self.event("PHASE_ENTERED", {"phase": "UNIT_TEST", "previous_result": "PASS"})
        self.event("PHASE_ENTERED", {"phase": "IMPLEMENTATION", "previous_result": "FAIL", "classification": "IMPLEMENTATION_ERROR", "reason": "code fix"})
        self.event("PHASE_ENTERED", {"phase": "REQUIREMENTS", "previous_result": "BLOCKED", "classification": "REQUIREMENT_ERROR", "reason": "spec conflict"})
        result = recorder.summary(self.root, "RUN-C0")
        self.assertEqual(result["rework"]["by_to_phase"], {"IMPLEMENTATION": 1, "REQUIREMENTS": 1})

    def test_cli_defaults_to_c0_start_phase(self):
        result = subprocess.run([sys.executable, str(ROOT / ".github/skills/evaluation/scripts/experiment_recorder.py"), "start", "--root", str(self.root), "--run-id", "RUN-CLI"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(recorder.load_events(self.root, "RUN-CLI")[0]["payload"]["phase"], "IMPLEMENTATION")

    def test_removed_phase_cli_entry_points_refuse_execution(self):
        for kind, script in (("architecture", "validate_design.py"), ("addr", "validate_addr.py")):
            result = subprocess.run([sys.executable, str(ROOT / f".github/skills/{kind}/scripts/{script}"), "--root", str(self.root)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("EXCLUDED", result.stdout)
        self.assertFalse((self.root / "reports").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
