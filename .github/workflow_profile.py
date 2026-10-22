from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path


PROFILE_PATH = ".github/workflow-profile.json"
DIRECT = "NO_DESIGN_ADDR"
EXCLUDED = ("ARCHITECTURE", "ADDR")
EXPECTED = {"schema_version": 1, "profile": DIRECT, "condition_id": "C0", "excluded_phases": list(EXCLUDED)}


def context(root: Path) -> dict:
    path = root / PROFILE_PATH
    if not path.is_file():
        return {"schema_version": 1, "profile": "FULL", "condition_id": None, "excluded_phases": []}
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if value != EXPECTED:
        raise ValueError("Unexpected workflow profile; only the fixed C0 exclusion is supported.")
    return value


def direct(root: Path) -> bool:
    return context(root)["profile"] == DIRECT


def require_phase(root: Path, phase: str) -> None:
    if direct(root) and phase in EXCLUDED:
        raise ValueError(f"{phase} is excluded by the C0 workflow profile.")


def check_workspace(root: Path) -> None:
    if not direct(root):
        return
    for relative in ("docs/architecture", "docs/addr", "docs/adr", "reports/architecture", "reports/addr"):
        directory = root / relative
        if directory.exists() and any(path.is_file() for path in directory.rglob("*")):
            raise ValueError(f"C0 must not reuse or generate design/ADDR artifacts: {relative}")


def effective_policy(root: Path, policy: dict, kind: str) -> dict:
    if not direct(root):
        return policy
    result = copy.deepcopy(policy)
    result["workflow_profile"] = DIRECT
    if kind == "traceability":
        result["integration"]["preserve_architecture_gate"] = False
        for category in ("addr", "entity", "file_definition", "task"):
            result["sources"][category] = []
        for category in ("code", "unit_test", "integration_test"):
            result[category]["allowed"] = ["requirement", "acceptance"]
        excluded_checks = {"C02", "C03", "C04", "C09"}
        for scope in result["checks"]["scopes"].values():
            for level in ("fail", "warn"):
                scope[level] = [check for check in scope.get(level, []) if check not in excluded_checks]
        result["excluded_checks"] = sorted(excluded_checks)
        result["checks"]["commit_prefixes"] = result["ids"]["requirement"] + ["CR"]
    elif kind == "loop":
        for phase in EXCLUDED:
            result["required_checks"].pop(phase, None)
    elif kind in ("quality-review", "security-review"):
        result["audit"]["allowed_scopes"] = [scope for scope in result["audit"]["allowed_scopes"] if scope not in EXCLUDED]
        if kind == "quality-review":
            for classification in ("ARCHITECTURE_QUALITY_ISSUE", "ADDR_QUALITY_ISSUE"):
                result["issues"]["classifications"] = [value for value in result["issues"]["classifications"] if value != classification]
                result["routing"].pop(classification, None)
            result["quality"]["implementation"]["require_accepted_adr_alignment"] = False
    elif kind == "failure-triage":
        result["analysis"]["root_cause_priority"] = [phase for phase in result["analysis"]["root_cause_priority"] if phase not in EXCLUDED]
        result["classification"]["allowed"] = [value for value in result["classification"]["allowed"] if value != "ADR_REQUIRED"]
        result["routing"].pop("ADR_REQUIRED", None)
        result["routes"]["allowed"] = [phase for phase in result["routes"]["allowed"] if phase not in EXCLUDED]
        result["invalidation"] = {phase: [target for target in targets if target not in EXCLUDED] for phase, targets in result["invalidation"].items() if phase not in EXCLUDED}
    else:
        raise ValueError("Unknown policy kind: " + kind)
    return result


def report_errors(root: Path, report: dict, kind: str) -> list[str]:
    if not direct(root):
        return []
    errors = []
    if report.get("workflow_profile") != DIRECT:
        errors.append("Report must identify workflow_profile=NO_DESIGN_ADDR.")
    for key in ("audit_scope", "source_phase", "recommended_route", "resume_from"):
        if report.get(key) in EXCLUDED:
            errors.append(f"Report {key} targets an excluded phase.")
    for phase in report.get("invalidated_phases", []) if isinstance(report.get("invalidated_phases"), list) else []:
        if phase in EXCLUDED:
            errors.append("Excluded phases must not be invalidated or revisited.")
    for issue in report.get("issues", []) if isinstance(report.get("issues"), list) else []:
        if isinstance(issue, dict) and issue.get("recommended_route") in EXCLUDED:
            errors.append("Issue routes to an excluded phase.")
    if kind == "quality-review":
        criteria = report.get("criteria_results", [])
        architecture = [item for item in criteria if isinstance(item, dict) and item.get("criterion") == "architecture-quality"] if isinstance(criteria, list) else []
        if len(architecture) != 1 or architecture[0].get("applicable") is not False or architecture[0].get("result") != "NOT_APPLICABLE" or not architecture[0].get("reason"):
            errors.append("architecture-quality must be explicitly NOT_APPLICABLE with a C0 exclusion reason.")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Check the fixed no-design/ADDR comparison profile.")
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args()
    root = Path(args.repo_root).resolve()
    try:
        profile = context(root)
        check_workspace(root)
        print(json.dumps({"status": "PASS", **profile, "measurement_start_phase": "IMPLEMENTATION" if direct(root) else "ARCHITECTURE"}, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, TypeError) as error:
        print(f"[FAIL] {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
