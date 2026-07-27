from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "research/document-session/scripts/document_session.py"
TEMPLATE_PATH = REPO_ROOT / "research/document-session/assets/worklog-template.md"


def run_git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        text=True,
        capture_output=True,
    )
    return result.stdout.strip()


def init_repo(repo: Path) -> None:
    run_git(repo, "init", "-q")


def run_cli(*args: object) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT_PATH), *(str(arg) for arg in args)],
        check=False,
        text=True,
        capture_output=True,
    )


def run_cli_input(
    input_text: str,
    *args: object,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT_PATH), *(str(arg) for arg in args)],
        input=input_text,
        check=False,
        text=True,
        capture_output=True,
    )


def worklog_text(
    worklog_id: str,
    *,
    documentation_status: str = "in_progress",
    checkpoint_count: int = 0,
    compact_count: int = 0,
    session_count: int = 1,
    task_key: str = "task-0123456789ab",
    extra_body: str = "",
) -> str:
    finalized_at = (
        '"2026-07-28T16:00:00+09:00"'
        if documentation_status == "final"
        else "null"
    )
    commit_final = '"abc123"' if documentation_status == "final" else "null"
    return f"""---
schema: "research-session-worklog-v1"
worklog_id: "{worklog_id}"
created_at: "2026-07-28T15:30:00+09:00"
last_checkpoint_at: null
finalized_at: {finalized_at}
timezone: "Asia/Seoul"
project: "example-research"
method: null
title: "Model Update"
primary_activity: "implementation"
activity_types: ["implementation"]
worklog_scope: "implementation_task"
work_status: "planned"
documentation_status: "{documentation_status}"
verification_status: "not_verified"
repository: "example-research"
remote_url: null
branch: "main"
commit_start: null
commit_current: null
commit_final: {commit_final}
task_key: "{task_key}"
session_count: {session_count}
checkpoint_count: {checkpoint_count}
compact_count: {compact_count}
run_ids: []
related_worklogs: []
tags: []
---

# Model Update

## Executive Summary

Implementation worklog initialized; no result is claimed.

## Original Request

Implement the model update.

## Scope and Assumptions

- Scope is limited to the current implementation task.

## Current State

- Current objective: Implement the model update.
- Current activity: implementation
- Implementation status: planned
- Active experiment: None observed.
- Active process: None observed.
- Blocking issue: None observed.
- Unresolved uncertainty: Exact test command is unknown.
- Next action: Inspect the changed files.

## Reproducibility Snapshot

- Repository: `example-research`

## Commands Executed

No research command has been recorded yet.

## Observed Facts

- [observed] The repository is available.

## Decisions

- [decision] Use one worklog for this task.

## Artifacts

No artifact has been recorded yet.

## Failures and Anomalies

None observed.

## Uncertainty and Open Questions

- Exact validation evidence is unknown.

## Next Actions

- Inspect repository evidence.

{extra_body}
## Session Checkpoints

No checkpoint has been recorded yet.

## Knowledge Handoff

### Durable Technical Findings

None confirmed yet.

### Reproducibility Constraints

Repository access is required.

### Research Decisions

Use one active worklog for this task.

### Experiment Evidence

None observed.

### Failure Patterns

None observed.

### Candidate Follow-up Topics

None identified.

### Evidence Boundaries

No result is established by this initial worklog.

### Suggested Stable Identifiers

- project name: `example-research`
"""


def finalized_worklog_text(worklog_id: str) -> str:
    checkpoint = """### 2026-07-28T16:00:00+09:00 — completion: Completed

#### Completed

The documented objective reached its terminal state.
"""
    profile = """## Implementation Record

The implementation evidence was reviewed.

"""
    return (
        worklog_text(
            worklog_id,
            documentation_status="final",
            checkpoint_count=1,
            extra_body=profile,
        )
        .replace(
            "last_checkpoint_at: null",
            'last_checkpoint_at: "2026-07-28T16:00:00+09:00"',
        )
        .replace('work_status: "planned"', 'work_status: "completed"')
        .replace("No checkpoint has been recorded yet.", checkpoint)
    )


def handoff_body(title: str = "Model Update") -> str:
    return f"""# {title} - Research Handoff

## Current Scope and State

- [observed] Training is running at capture time.
- [unknown] Completion remains unknown.

## Implementation Changes

- [observed] The source worklog records the implementation scope.

## Experiment and Run Evidence

- [observed] The active process state is running.

## Observed Results

- [unknown] No completed quantitative result is available.

## Decisions

- [decision] Preserve the running state without a completion claim.

## Failures and Anomalies

- [unknown] No failure evidence was available at capture time.

## Artifacts

- [observed] The source worklog is the only confirmed artifact.

## Reproducibility Constraints

- [observed] Repository access is required.

## Uncertainty and Evidence Boundaries

- [unknown] One running process does not establish an aggregate result.

## Next Actions

- [interpretation] Re-check the process and metrics after it stops.

## Coverage Limitations

- [unknown] Runtime logs and checkpoints were not independently inspected.
"""


class DocumentSessionTest(unittest.TestCase):
    def load_module(self):
        if not SCRIPT_PATH.exists():
            self.fail("document_session.py is missing")
        spec = importlib.util.spec_from_file_location("document_session", SCRIPT_PATH)
        if spec is None or spec.loader is None:
            self.fail("cannot load document_session.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_normalize_slug_catches_invalid_filename_shape(self):
        module = self.load_module()
        self.assertEqual(module.normalize_slug("  Model / Update  "), "model-update")
        self.assertEqual(module.normalize_slug("한글  제목"), "한글-제목")
        with self.assertRaises(ValueError):
            module.normalize_slug("***")

    def test_sanitize_remote_rejects_malformed_port(self):
        module = self.load_module()
        self.assertIsNone(
            module.sanitize_remote_url("https://example.invalid:not-a-port/repo")
        )

    def test_allocate_uses_seoul_time_null_method_and_collision_suffix(self):
        module = self.load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            metadata = {
                "repo_root": repo,
                "project": "example-research",
                "repository": "example-research",
                "method": None,
                "title": "Model Update",
                "objective": "Implement the model update",
                "primary_activity": "implementation",
                "activity_types": ["implementation"],
                "worklog_scope": "implementation_task",
                "created_at": datetime(
                    2026, 7, 28, 15, 30, tzinfo=timezone.utc
                ).astimezone(timezone.utc),
            }
            first = module.allocate_worklog(metadata, TEMPLATE_PATH, create=True)
            second = module.allocate_worklog(metadata, TEMPLATE_PATH, create=True)

            self.assertEqual(
                Path(first["path"]).name,
                "260729_0030_unassigned_model-update.md",
            )
            self.assertEqual(
                Path(second["path"]).name,
                "260729_0030_unassigned_model-update_02.md",
            )
            self.assertEqual(
                first["frontmatter"]["worklog_id"],
                Path(first["path"]).stem,
            )
            self.assertRegex(first["frontmatter"]["task_key"], r"^task-[0-9a-f]{12}$")
            self.assertTrue(Path(first["path"]).exists())
            self.assertNotEqual(
                Path(first["path"]).read_text(),
                Path(second["path"]).read_text(),
            )

    def test_parse_frontmatter_reads_flat_json_compatible_yaml(self):
        module = self.load_module()
        metadata, body = module.parse_frontmatter(
            '---\nname: "example"\nitems: ["a", "b"]\nmissing: null\n---\n\n# Body\n'
        )
        self.assertEqual(metadata["name"], "example")
        self.assertEqual(metadata["items"], ["a", "b"])
        self.assertIsNone(metadata["missing"])
        self.assertEqual(body.strip(), "# Body")

    def test_resolve_target_reports_ambiguity_and_explicit_precedence(self):
        module = self.load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            docs = repo / "docs"
            docs.mkdir()
            first = docs / "260728_1530_unassigned_model-update.md"
            second = docs / "260728_1530_unassigned_model-update_02.md"
            first.write_text(worklog_text(first.stem), encoding="utf-8")
            second.write_text(
                worklog_text(second.stem, task_key="task-111111111111"),
                encoding="utf-8",
            )

            with self.assertRaises(module.DocumentSessionError) as raised:
                module.resolve_target(repo, None, None)
            self.assertEqual(raised.exception.exit_code, 5)

            selected = module.resolve_target(repo, str(second), None)
            self.assertEqual(Path(selected["path"]), second.resolve())

            noncanonical = repo / "notes/model-update.md"
            noncanonical.parent.mkdir()
            noncanonical.write_text(
                worklog_text(noncanonical.stem),
                encoding="utf-8",
            )
            with self.assertRaises(module.DocumentSessionError) as rejected:
                module.resolve_target(repo, str(noncanonical), None)
            self.assertEqual(rejected.exception.code, "target.identity")

    def test_discovery_ignores_nested_noncanonical_worklogs(self):
        module = self.load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            docs = repo / "docs"
            nested = docs / "nested"
            nested.mkdir(parents=True)
            direct = docs / "260728_1530_unassigned_model-update.md"
            nested_target = nested / "260728_1531_unassigned_other.md"
            direct.write_text(worklog_text(direct.stem), encoding="utf-8")
            nested_target.write_text(
                worklog_text(nested_target.stem, task_key="task-111111111111"),
                encoding="utf-8",
            )

            selected = module.resolve_target(repo, None, None)
            self.assertEqual(Path(selected["path"]), direct.resolve())

    def test_resolve_target_rejects_finalized_worklog_for_write(self):
        module = self.load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            docs = repo / "docs"
            docs.mkdir()
            target = docs / "260728_1530_unassigned_model-update.md"
            target.write_text(
                worklog_text(target.stem, documentation_status="final"),
                encoding="utf-8",
            )
            with self.assertRaises(module.DocumentSessionError) as raised:
                module.resolve_target(repo, str(target), None, for_write=True)
            self.assertEqual(raised.exception.exit_code, 6)

    def test_validate_accepts_initial_worklog(self):
        module = self.load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            docs = repo / "docs"
            docs.mkdir()
            target = docs / "260728_1530_unassigned_model-update.md"
            target.write_text(worklog_text(target.stem), encoding="utf-8")

            result = module.validate_worklog(target, repo)
            self.assertTrue(result["valid"], result["errors"])
            self.assertEqual(result["errors"], [])

    def test_validate_requires_one_matching_top_level_title(self):
        module = self.load_module()
        variants = {
            "missing": worklog_text(
                "260728_1530_unassigned_model-update"
            ).replace("# Model Update\n", ""),
            "duplicate": worklog_text(
                "260728_1530_unassigned_model-update"
            ).replace("# Model Update\n", "# Model Update\n\n# Model Update\n"),
            "mismatched": worklog_text(
                "260728_1530_unassigned_model-update"
            ).replace("# Model Update\n", "# Different Title\n"),
        }
        for name, text in variants.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temp_dir:
                repo = Path(temp_dir)
                docs = repo / "docs"
                docs.mkdir()
                target = docs / "260728_1530_unassigned_model-update.md"
                target.write_text(text, encoding="utf-8")

                result = module.validate_worklog(target, repo)

                self.assertFalse(result["valid"])
                self.assertIn(
                    "heading.title",
                    {item["code"] for item in result["errors"]},
                )

    def test_validate_reports_secret_without_echoing_value(self):
        module = self.load_module()
        secret = "ghp_" + ("1" * 36)
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            docs = repo / "docs"
            docs.mkdir()
            target = docs / "260728_1530_unassigned_model-update.md"
            target.write_text(
                worklog_text(target.stem).replace(
                    "No research command has been recorded yet.",
                    f"Command contained {secret}",
                ),
                encoding="utf-8",
            )

            result = module.validate_worklog(target, repo)
            serialized = json.dumps(result)
            self.assertFalse(result["valid"])
            self.assertIn("secret.github-token", serialized)
            self.assertNotIn(secret, serialized)

    def test_validate_warns_for_missing_explicit_artifact(self):
        module = self.load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            docs = repo / "docs"
            docs.mkdir()
            target = docs / "260728_1530_unassigned_model-update.md"
            target.write_text(
                worklog_text(target.stem).replace(
                    "No artifact has been recorded yet.",
                    "- path: `outputs/missing/metrics.json`\n  role: metric output",
                ),
                encoding="utf-8",
            )

            result = module.validate_worklog(target, repo)
            self.assertTrue(result["valid"])
            self.assertIn("artifact.missing", json.dumps(result["warnings"]))

    def test_validate_rejects_artifact_symlink_outside_repository(self):
        module = self.load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture = Path(temp_dir)
            repo = fixture / "repo"
            docs = repo / "docs"
            artifacts = repo / "artifacts"
            docs.mkdir(parents=True)
            artifacts.mkdir()
            outside = fixture / "outside-metrics.json"
            outside.write_text("{}\n", encoding="utf-8")
            (artifacts / "metrics.json").symlink_to(outside)
            target = docs / "260728_1530_unassigned_model-update.md"
            target.write_text(
                worklog_text(target.stem).replace(
                    "No artifact has been recorded yet.",
                    "- path: `artifacts/metrics.json`\n  role: metric output",
                ),
                encoding="utf-8",
            )

            result = module.validate_worklog(target, repo)
            self.assertFalse(result["valid"])
            self.assertIn("artifact.unsafe", json.dumps(result["errors"]))

    def test_inspect_sanitizes_remote_and_does_not_modify_repository(self):
        module = self.load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            init_repo(repo)
            source = repo / "source.txt"
            source.write_text("unchanged\n", encoding="utf-8")
            run_git(repo, "add", "source.txt")
            run_git(
                repo,
                "-c",
                "user.name=Test User",
                "-c",
                "user.email=none",
                "commit",
                "-qm",
                "initial",
            )
            source.write_text("changed\n", encoding="utf-8")
            run_git(
                repo,
                "remote",
                "add",
                "origin",
                "https://"
                + "private-user"
                + ":"
                + "private-token"
                + "@example.invalid/org/repo.git",
            )
            before = source.read_bytes()
            git_index = repo / ".git/index"
            index_before = (git_index.read_bytes(), git_index.stat().st_mtime_ns)

            result = module.inspect_repository(
                repo,
                datetime(2026, 7, 28, 6, 30, tzinfo=timezone.utc),
            )

            self.assertEqual(
                result["remote_url"],
                "https://example.invalid/org/repo.git",
            )
            self.assertEqual(result["timestamp"], "2026-07-28T15:30:00+09:00")
            self.assertEqual(source.read_bytes(), before)
            self.assertEqual(
                (git_index.read_bytes(), git_index.stat().st_mtime_ns),
                index_before,
            )
            self.assertFalse((repo / "docs").exists())

    def test_cli_allocate_create_and_validate_emit_json(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            allocation_args = (
                "allocate",
                "--repo",
                repo,
                "--title",
                "Model Update",
                "--objective",
                "Implement the model update",
                "--activity",
                "implementation",
                "--scope",
                "implementation_task",
                "--created-at",
                "2026-07-28T15:30:00+09:00",
            )
            previewed = run_cli(*allocation_args)
            self.assertEqual(previewed.returncode, 0, previewed.stderr)
            preview_payload = json.loads(previewed.stdout)
            preview_path = Path(preview_payload["data"]["path"])
            self.assertFalse(preview_path.exists())

            allocated = run_cli(
                *allocation_args,
                "--create",
            )
            self.assertEqual(allocated.returncode, 0, allocated.stderr)
            payload = json.loads(allocated.stdout)
            self.assertTrue(payload["ok"])
            target = Path(payload["data"]["path"])
            self.assertEqual(target, preview_path)
            self.assertTrue(target.exists())

            validated = run_cli(
                "validate",
                "--repo",
                repo,
                "--target",
                target.relative_to(repo),
            )
            self.assertEqual(validated.returncode, 0, validated.stderr)
            self.assertTrue(json.loads(validated.stdout)["data"]["valid"])

    def test_cli_uses_stable_selection_exit_codes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            docs = repo / "docs"
            docs.mkdir()
            active_one = docs / "260728_1530_unassigned_model-update.md"
            active_two = docs / "260728_1530_unassigned_model-update_02.md"
            finalized = docs / "260728_1530_unassigned_model-update_03.md"
            active_one.write_text(worklog_text(active_one.stem), encoding="utf-8")
            active_two.write_text(
                worklog_text(active_two.stem, task_key="task-111111111111"),
                encoding="utf-8",
            )
            finalized.write_text(
                worklog_text(finalized.stem, documentation_status="final"),
                encoding="utf-8",
            )

            ambiguous = run_cli("locate", "--repo", repo)
            self.assertEqual(ambiguous.returncode, 5)
            self.assertEqual(
                json.loads(ambiguous.stderr)["error"]["code"],
                "target.ambiguous",
            )

            locked = run_cli(
                "locate",
                "--repo",
                repo,
                "--target",
                finalized,
                "--for-write",
            )
            self.assertEqual(locked.returncode, 6)
            self.assertEqual(
                json.loads(locked.stderr)["error"]["code"],
                "target.finalized",
            )

    def test_cli_returns_secret_exit_code_without_echoing_value(self):
        secret = "ghp_" + ("1" * 36)
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            docs = repo / "docs"
            docs.mkdir()
            target = docs / "260728_1530_unassigned_model-update.md"
            target.write_text(
                worklog_text(target.stem).replace(
                    "No research command has been recorded yet.",
                    f"Command contained {secret}",
                ),
                encoding="utf-8",
            )

            result = run_cli(
                "validate",
                "--repo",
                repo,
                "--target",
                target,
            )
            self.assertEqual(result.returncode, 8)
            self.assertNotIn(secret, result.stdout)
            self.assertNotIn(secret, result.stderr)
            self.assertIn("secret.github-token", result.stdout)

    def test_cli_malformed_frontmatter_returns_structured_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            docs = repo / "docs"
            docs.mkdir()
            target = docs / "260728_1530_unassigned_model-update.md"
            target.write_text(
                worklog_text(target.stem).replace(
                    'primary_activity: "implementation"',
                    'primary_activity: ["implementation"]',
                ),
                encoding="utf-8",
            )

            result = run_cli(
                "validate",
                "--repo",
                repo,
                "--target",
                target.relative_to(repo),
            )
            self.assertEqual(result.returncode, 7)
            payload = json.loads(result.stdout)
            self.assertFalse(payload["data"]["valid"])
            self.assertNotIn("Traceback", result.stderr)

            malformed_status = worklog_text(target.stem).replace(
                'documentation_status: "in_progress"',
                'documentation_status: ["in_progress"]',
            )
            target.write_text(malformed_status, encoding="utf-8")
            inspected = run_cli("inspect", "--repo", repo)
            self.assertEqual(inspected.returncode, 0, inspected.stderr)
            self.assertEqual(
                json.loads(inspected.stdout)["data"]["active_worklogs"],
                [],
            )
            located = run_cli(
                "locate",
                "--repo",
                repo,
                "--target",
                target.relative_to(repo),
            )
            self.assertEqual(located.returncode, 3)
            self.assertEqual(
                json.loads(located.stderr)["error"]["code"],
                "target.status",
            )

    def test_cli_rejects_invalid_allocation_before_writing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            result = run_cli(
                "allocate",
                "--repo",
                repo,
                "--title",
                "Mixed Run",
                "--objective",
                "Document a mixed run",
                "--activity",
                "mixed",
                "--activity-type",
                "training",
                "--scope",
                "mixed_pipeline",
                "--create",
            )
            self.assertEqual(result.returncode, 3)
            self.assertEqual(
                json.loads(result.stderr)["error"]["code"],
                "allocation.activity",
            )
            self.assertFalse((repo / "docs").exists())

    def test_cli_rejects_secret_like_allocation_before_writing(self):
        secret = "ghp_" + ("2" * 36)
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            result = run_cli(
                "allocate",
                "--repo",
                repo,
                "--title",
                "Sensitive Run",
                "--objective",
                f"Document token {secret}",
                "--activity",
                "analysis",
                "--scope",
                "code_analysis",
                "--create",
            )
            self.assertEqual(result.returncode, 8)
            self.assertNotIn(secret, result.stderr)
            self.assertEqual(
                json.loads(result.stderr)["error"]["code"],
                "secret.detected",
            )
            self.assertFalse((repo / "docs").exists())

    def test_cli_allocation_io_failure_is_structured_and_non_destructive(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            docs_file = repo / "docs"
            docs_file.write_text("preserve me\n", encoding="utf-8")
            result = run_cli(
                "allocate",
                "--repo",
                repo,
                "--title",
                "Model Update",
                "--objective",
                "Implement the model update",
                "--activity",
                "implementation",
                "--scope",
                "implementation_task",
                "--create",
            )
            self.assertEqual(result.returncode, 3)
            self.assertNotIn("Traceback", result.stderr)
            self.assertEqual(
                json.loads(result.stderr)["error"]["code"],
                "allocation.write",
            )
            self.assertEqual(docs_file.read_text(), "preserve me\n")

    def test_cli_normalizes_multiline_input_and_bounds_filename(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            long_title = "Model\n## Injected " + ("x" * 400)
            result = run_cli(
                "allocate",
                "--repo",
                repo,
                "--title",
                long_title,
                "--objective",
                "Implement update\n## Observed Facts\nUnverified claim",
                "--activity",
                "implementation",
                "--scope",
                "implementation_task",
                "--created-at",
                "2026-07-28T15:30:00+09:00",
                "--create",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            target = Path(payload["data"]["path"])
            self.assertLessEqual(len(target.name.encode("utf-8")), 200)
            text = target.read_text(encoding="utf-8")
            metadata, body = self.load_module().parse_frontmatter(text)
            self.assertNotIn("\n", metadata["title"])
            self.assertEqual(body.splitlines().count("## Observed Facts"), 1)
            validated = run_cli(
                "validate",
                "--repo",
                repo,
                "--target",
                target.relative_to(repo),
            )
            self.assertEqual(validated.returncode, 0, validated.stdout)

    def test_cli_usage_errors_are_json(self):
        result = run_cli("allocate", "--activity", "not-an-activity")
        self.assertEqual(result.returncode, 2)
        payload = json.loads(result.stderr)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["error"]["code"], "cli.usage")

    def test_cli_maps_missing_and_unsafe_validate_targets(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture = Path(temp_dir)
            repo = fixture / "repo"
            repo.mkdir()
            outside = fixture / "outside.md"
            outside.write_text("not a worklog\n", encoding="utf-8")

            missing = run_cli(
                "validate",
                "--repo",
                repo,
                "--target",
                "docs/missing.md",
            )
            self.assertEqual(missing.returncode, 4)
            self.assertEqual(
                json.loads(missing.stdout)["data"]["errors"][0]["code"],
                "path.missing",
            )

            unsafe = run_cli(
                "validate",
                "--repo",
                repo,
                "--target",
                outside,
            )
            self.assertEqual(unsafe.returncode, 3)
            self.assertEqual(
                json.loads(unsafe.stdout)["data"]["errors"][0]["code"],
                "path.unsafe",
            )

    def test_validate_enforces_filename_location_and_normalization(self):
        module = self.load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            nested = repo / "docs/nested"
            nested.mkdir(parents=True)
            target = nested / "260728_1530_Unassigned_Model Update.md"
            target.write_text(worklog_text(target.stem), encoding="utf-8")

            result = module.validate_worklog(target, repo)
            codes = {item["code"] for item in result["errors"]}
            self.assertFalse(result["valid"])
            self.assertIn("path.location", codes)
            self.assertIn("filename.invalid", codes)

    def test_validate_enforces_checkpoint_timestamp_lifecycle(self):
        module = self.load_module()
        profile = """## Implementation Record

Changed paths were inspected.

"""
        checkpoint = """### 2026-07-28T06:00:00+00:00 — progress: Update

#### Completed

Observed one change.
"""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            docs = repo / "docs"
            docs.mkdir()
            target = docs / "260728_1530_unassigned_model-update.md"
            text = worklog_text(
                target.stem,
                checkpoint_count=1,
                extra_body=profile,
            )
            text = text.replace(
                "last_checkpoint_at: null",
                'last_checkpoint_at: "2026-07-28T15:30:00+09:00"',
            ).replace("No checkpoint has been recorded yet.", checkpoint)
            target.write_text(text, encoding="utf-8")

            result = module.validate_worklog(target, repo)
            codes = {item["code"] for item in result["errors"]}
            self.assertFalse(result["valid"])
            self.assertIn("timestamp.seoul", codes)
            self.assertIn("timestamp.checkpoint-latest", codes)

    def test_validate_allows_non_git_final_with_terminal_checkpoint(self):
        module = self.load_module()
        profile = """## Implementation Record

The implementation evidence was reviewed.

"""
        terminal = """### 2026-07-28T16:00:00+09:00 — completion: Completed

#### Completed

The documented objective reached its terminal state.
"""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            docs = repo / "docs"
            docs.mkdir()
            target = docs / "260728_1530_unassigned_model-update.md"
            text = worklog_text(
                target.stem,
                documentation_status="final",
                checkpoint_count=1,
                extra_body=profile,
            )
            text = text.replace(
                "last_checkpoint_at: null",
                'last_checkpoint_at: "2026-07-28T16:00:00+09:00"',
            ).replace(
                'work_status: "planned"',
                'work_status: "completed"',
            ).replace(
                'commit_final: "abc123"',
                "commit_final: null",
            ).replace("No checkpoint has been recorded yet.", terminal)
            target.write_text(text, encoding="utf-8")

            result = module.validate_worklog(target, repo)
            self.assertTrue(result["valid"], result["errors"])
            self.assertIn("final.commit-missing", json.dumps(result["warnings"]))

            target.write_text(
                text.replace(
                    'work_status: "completed"',
                    'work_status: "failed"',
                ),
                encoding="utf-8",
            )
            mismatch = module.validate_worklog(target, repo)
            self.assertFalse(mismatch["valid"])
            self.assertIn("final.event-status", json.dumps(mismatch["errors"]))

    def test_validate_requires_available_git_head_for_final_commit(self):
        module = self.load_module()
        profile = """## Implementation Record

The implementation evidence was reviewed.

"""
        terminal = """### 2026-07-28T16:00:00+09:00 — completion: Completed

#### Completed

The documented objective reached its terminal state.
"""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            init_repo(repo)
            seed = repo / "seed.txt"
            seed.write_text("seed\n", encoding="utf-8")
            run_git(repo, "add", "seed.txt")
            run_git(
                repo,
                "-c",
                "user.name=Test User",
                "-c",
                "user.email=none",
                "commit",
                "-qm",
                "initial",
            )
            head = run_git(repo, "rev-parse", "HEAD")
            docs = repo / "docs"
            docs.mkdir()
            target = docs / "260728_1530_unassigned_model-update.md"
            text = worklog_text(
                target.stem,
                documentation_status="final",
                checkpoint_count=1,
                extra_body=profile,
            )
            text = text.replace(
                "last_checkpoint_at: null",
                'last_checkpoint_at: "2026-07-28T16:00:00+09:00"',
            ).replace(
                'work_status: "planned"',
                'work_status: "completed"',
            ).replace(
                'commit_final: "abc123"',
                "commit_final: null",
            ).replace("No checkpoint has been recorded yet.", terminal)
            target.write_text(text, encoding="utf-8")

            missing = module.validate_worklog(target, repo)
            self.assertFalse(missing["valid"])
            self.assertIn("final.commit-required", json.dumps(missing["errors"]))

            target.write_text(
                text.replace("commit_final: null", f'commit_final: "{head}"'),
                encoding="utf-8",
            )
            present = module.validate_worklog(target, repo)
            self.assertTrue(present["valid"], present["errors"])

            target.write_text(
                text.replace(
                    "commit_final: null",
                    f'commit_final: "{"0" * 40}"',
                ),
                encoding="utf-8",
            )
            unknown = module.validate_worklog(target, repo)
            self.assertFalse(unknown["valid"])
            self.assertIn("final.commit-unknown", json.dumps(unknown["errors"]))


    def test_handoff_preview_create_collision_and_source_immutability(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            docs = repo / "docs"
            docs.mkdir()
            source = docs / "260728_1530_unassigned_model-update.md"
            source.write_text(worklog_text(source.stem), encoding="utf-8")
            source_before = source.read_bytes()
            args = (
                "allocate-handoff",
                "--repo",
                repo,
                "--source-worklog",
                source.relative_to(repo),
                "--captured-at",
                "2026-07-28T15:30:00+00:00",
                "--work-status-at-capture",
                "running",
                "--verification-status-at-capture",
                "not_verified",
                "--documentation-status-at-capture",
                "in_progress",
                "--coverage",
                "partial",
                "--active-process-state",
                "running",
            )

            preview = run_cli_input(handoff_body(), *args)
            self.assertEqual(preview.returncode, 0, preview.stderr)
            proposal = json.loads(preview.stdout)["data"]
            self.assertEqual(
                proposal["path"],
                "docs/handoffs/260729_0030_unspecified-method_model-update.md",
            )
            self.assertFalse((repo / proposal["path"]).exists())
            self.assertRegex(proposal["allocation_token"], r"^[^.]+\.[0-9a-f]{64}$")
            self.assertRegex(
                proposal["frontmatter"]["snapshot_sha256"],
                r"^[0-9a-f]{64}$",
            )

            created = run_cli_input(
                handoff_body(),
                *args,
                "--allocation-token",
                proposal["allocation_token"],
                "--create",
            )
            self.assertEqual(created.returncode, 0, created.stderr)
            created_data = json.loads(created.stdout)["data"]
            target = repo / created_data["path"]
            self.assertTrue(target.exists())
            self.assertEqual(created_data["markdown"], proposal["markdown"])
            self.assertEqual(source.read_bytes(), source_before)

            second_preview = run_cli_input(handoff_body(), *args)
            self.assertEqual(second_preview.returncode, 0, second_preview.stderr)
            second = json.loads(second_preview.stdout)["data"]
            self.assertEqual(
                second["path"],
                "docs/handoffs/260729_0030_unspecified-method_model-update_02.md",
            )

    def test_handoff_captures_mixed_running_state_and_current_git_identity(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            init_repo(repo)
            seed = repo / "seed.txt"
            seed.write_text("seed\n", encoding="utf-8")
            run_git(repo, "add", "seed.txt")
            run_git(
                repo,
                "-c",
                "user.name=Test User",
                "-c",
                "user.email=none",
                "commit",
                "-qm",
                "initial",
            )
            head = run_git(repo, "rev-parse", "HEAD")
            branch = run_git(repo, "branch", "--show-current")
            docs = repo / "docs"
            docs.mkdir()
            source = docs / "260728_1530_method-model_model-update.md"
            source_text = (
                worklog_text(source.stem)
                .replace("method: null", 'method: "Method Model"')
                .replace(
                    'primary_activity: "implementation"',
                    'primary_activity: "mixed"',
                )
                .replace(
                    'activity_types: ["implementation"]',
                    'activity_types: ["implementation", "evaluation", "debugging"]',
                )
            )
            source.write_text(source_text, encoding="utf-8")

            preview = run_cli_input(
                handoff_body(),
                "allocate-handoff",
                "--repo",
                repo,
                "--source-worklog",
                source,
                "--captured-at",
                "2026-07-28T16:45:00+09:00",
                "--work-status-at-capture",
                "running",
                "--verification-status-at-capture",
                "partially_verified",
                "--documentation-status-at-capture",
                "in_progress",
                "--coverage",
                "partial",
                "--active-process-state",
                "running",
                "--verification-evidence",
                "logs/train.log",
            )
            self.assertEqual(preview.returncode, 0, preview.stderr)
            metadata = json.loads(preview.stdout)["data"]["frontmatter"]
            self.assertEqual(metadata["primary_activity"], "mixed")
            self.assertEqual(
                metadata["activity_types"],
                ["implementation", "evaluation", "debugging"],
            )
            self.assertEqual(metadata["work_status_at_capture"], "running")
            self.assertEqual(metadata["active_process_state"], "running")
            self.assertEqual(metadata["repository"], repo.name)
            self.assertEqual(metadata["branch"], branch)
            self.assertEqual(metadata["commit_at_capture"], head)

    def test_handoff_explicit_finalized_source_and_no_auto_fallback(self):
        module = self.load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            docs = repo / "docs"
            docs.mkdir()
            source = docs / "260728_1530_unassigned_model-update.md"
            source.write_text(finalized_worklog_text(source.stem), encoding="utf-8")

            with self.assertRaises(module.DocumentSessionError) as raised:
                module.resolve_target(repo, None, None)
            self.assertEqual(raised.exception.code, "target.not-found")

            selected = module.resolve_target(repo, str(source), None)
            self.assertEqual(selected["documentation_status"], "final")
            preview = run_cli_input(
                handoff_body(),
                "allocate-handoff",
                "--repo",
                repo,
                "--source-worklog",
                source,
                "--captured-at",
                "2026-07-28T16:45:00+09:00",
                "--work-status-at-capture",
                "completed",
                "--verification-status-at-capture",
                "partially_verified",
                "--documentation-status-at-capture",
                "final",
                "--coverage",
                "partial",
                "--active-process-state",
                "completed",
                "--verification-evidence",
                "tests/results.txt",
            )
            self.assertEqual(preview.returncode, 0, preview.stderr)
            metadata = json.loads(preview.stdout)["data"]["frontmatter"]
            self.assertEqual(metadata["documentation_status_at_capture"], "final")

    def test_handoff_rejects_status_contradictions_incomplete_body_and_secrets(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            docs = repo / "docs"
            docs.mkdir()
            source = docs / "260728_1530_unassigned_model-update.md"
            source.write_text(worklog_text(source.stem), encoding="utf-8")
            base = (
                "allocate-handoff",
                "--repo",
                repo,
                "--source-worklog",
                source,
                "--captured-at",
                "2026-07-28T16:45:00+09:00",
                "--documentation-status-at-capture",
                "in_progress",
                "--coverage",
                "partial",
            )

            running_completed = run_cli_input(
                handoff_body(),
                *base,
                "--work-status-at-capture",
                "completed",
                "--verification-status-at-capture",
                "not_verified",
                "--active-process-state",
                "running",
            )
            self.assertEqual(running_completed.returncode, 3)
            self.assertEqual(
                json.loads(running_completed.stderr)["error"]["code"],
                "handoff.status-contradiction",
            )

            verified_without_evidence = run_cli_input(
                handoff_body(),
                *base,
                "--work-status-at-capture",
                "partial",
                "--verification-status-at-capture",
                "verified",
                "--active-process-state",
                "completed",
            )
            self.assertEqual(verified_without_evidence.returncode, 3)
            self.assertEqual(
                json.loads(verified_without_evidence.stderr)["error"]["code"],
                "handoff.verification-evidence",
            )

            incomplete = run_cli_input(
                "# Model Update - Research Handoff\n",
                *base,
                "--work-status-at-capture",
                "partial",
                "--verification-status-at-capture",
                "not_verified",
                "--active-process-state",
                "unknown",
            )
            self.assertEqual(incomplete.returncode, 3)
            self.assertEqual(
                json.loads(incomplete.stderr)["error"]["code"],
                "handoff.body",
            )

            secret = "ghp_" + ("1" * 36)
            secret_result = run_cli_input(
                handoff_body().replace(
                    "Repository access is required.",
                    f"Credential: {secret}",
                ),
                *base,
                "--work-status-at-capture",
                "partial",
                "--verification-status-at-capture",
                "not_verified",
                "--active-process-state",
                "unknown",
            )
            self.assertEqual(secret_result.returncode, 8)
            self.assertNotIn(secret, secret_result.stdout)
            self.assertNotIn(secret, secret_result.stderr)

    def test_handoff_token_binds_source_body_path_and_is_single_use(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            docs = repo / "docs"
            docs.mkdir()
            source = docs / "260728_1530_unassigned_model-update.md"
            source.write_text(worklog_text(source.stem), encoding="utf-8")
            args = (
                "allocate-handoff",
                "--repo",
                repo,
                "--source-worklog",
                source,
                "--captured-at",
                "2026-07-28T16:45:00+09:00",
                "--work-status-at-capture",
                "running",
                "--verification-status-at-capture",
                "not_verified",
                "--documentation-status-at-capture",
                "in_progress",
                "--coverage",
                "partial",
                "--active-process-state",
                "running",
            )
            preview = run_cli_input(handoff_body(), *args)
            self.assertEqual(preview.returncode, 0, preview.stderr)
            proposal = json.loads(preview.stdout)["data"]
            encoded, digest = proposal["allocation_token"].split(".", 1)
            malformed_token = f"{encoded}!!!!.{digest}"
            malformed = run_cli_input(
                handoff_body(),
                *args,
                "--allocation-token",
                malformed_token,
                "--create",
            )
            self.assertEqual(malformed.returncode, 3)
            self.assertEqual(
                json.loads(malformed.stderr)["error"]["code"],
                "handoff.allocation-token",
            )
            self.assertFalse((repo / proposal["path"]).exists())


            body_drift = run_cli_input(
                handoff_body().replace(
                    "Training is running",
                    "Training may be running",
                ),
                *args,
                "--allocation-token",
                proposal["allocation_token"],
                "--create",
            )
            self.assertEqual(body_drift.returncode, 3)
            self.assertEqual(
                json.loads(body_drift.stderr)["error"]["code"],
                "handoff.allocation-drift",
            )
            self.assertFalse((repo / "docs/handoffs").exists())

            source.write_text(
                source.read_text(encoding="utf-8").replace(
                    "Exact test command is unknown.",
                    "Test command remains unknown.",
                ),
                encoding="utf-8",
            )
            source_drift = run_cli_input(
                handoff_body(),
                *args,
                "--allocation-token",
                proposal["allocation_token"],
                "--create",
            )
            self.assertEqual(source_drift.returncode, 3)
            self.assertEqual(
                json.loads(source_drift.stderr)["error"]["code"],
                "handoff.allocation-drift",
            )

            fresh = run_cli_input(handoff_body(), *args)
            self.assertEqual(fresh.returncode, 0, fresh.stderr)
            fresh_data = json.loads(fresh.stdout)["data"]
            created = run_cli_input(
                handoff_body(),
                *args,
                "--allocation-token",
                fresh_data["allocation_token"],
                "--create",
            )
            self.assertEqual(created.returncode, 0, created.stderr)
            reused = run_cli_input(
                handoff_body(),
                *args,
                "--allocation-token",
                fresh_data["allocation_token"],
                "--create",
            )
            self.assertEqual(reused.returncode, 3)
            self.assertEqual(
                json.loads(reused.stderr)["error"]["code"],
                "handoff.allocation-conflict",
            )

    def test_handoff_concurrent_create_publishes_exactly_one_complete_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            docs = repo / "docs"
            docs.mkdir()
            source = docs / "260728_1530_unassigned_model-update.md"
            source.write_text(worklog_text(source.stem), encoding="utf-8")
            args = (
                "allocate-handoff",
                "--repo",
                repo,
                "--source-worklog",
                source,
                "--captured-at",
                "2026-07-28T16:45:00+09:00",
                "--work-status-at-capture",
                "running",
                "--verification-status-at-capture",
                "not_verified",
                "--documentation-status-at-capture",
                "in_progress",
                "--coverage",
                "partial",
                "--active-process-state",
                "running",
            )
            preview = run_cli_input(handoff_body(), *args)
            self.assertEqual(preview.returncode, 0, preview.stderr)
            proposal = json.loads(preview.stdout)["data"]
            create_args = (
                *args,
                "--allocation-token",
                proposal["allocation_token"],
                "--create",
            )
            with ThreadPoolExecutor(max_workers=2) as executor:
                results = list(
                    executor.map(
                        lambda _: run_cli_input(handoff_body(), *create_args),
                        range(2),
                    )
                )
            self.assertEqual(sorted(result.returncode for result in results), [0, 3])
            target = repo / proposal["path"]
            self.assertEqual(target.read_text(encoding="utf-8"), proposal["markdown"])
            self.assertFalse(list(target.parent.glob(".*.tmp")))

    def test_validate_handoff_enforces_seal_and_tolerates_canonical_formatting(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            docs = repo / "docs"
            docs.mkdir()
            source = docs / "260728_1530_unassigned_model-update.md"
            source.write_text(worklog_text(source.stem), encoding="utf-8")
            args = (
                "allocate-handoff",
                "--repo",
                repo,
                "--source-worklog",
                source,
                "--captured-at",
                "2026-07-28T16:45:00+09:00",
                "--work-status-at-capture",
                "running",
                "--verification-status-at-capture",
                "not_verified",
                "--documentation-status-at-capture",
                "in_progress",
                "--coverage",
                "partial",
                "--active-process-state",
                "running",
            )
            preview = run_cli_input(handoff_body(), *args)
            proposal = json.loads(preview.stdout)["data"]
            created = run_cli_input(
                handoff_body(),
                *args,
                "--allocation-token",
                proposal["allocation_token"],
                "--create",
            )
            self.assertEqual(created.returncode, 0, created.stderr)
            target = repo / proposal["path"]

            valid = run_cli(
                "validate-handoff",
                "--repo",
                repo,
                "--target",
                target.relative_to(repo),
            )
            self.assertEqual(valid.returncode, 0, valid.stderr)
            self.assertTrue(json.loads(valid.stdout)["data"]["valid"])

            text = target.read_text(encoding="utf-8")
            lines = text.splitlines()
            closing = lines.index("---", 1)
            frontmatter_lines = lines[1:closing]
            target.write_bytes(
                (
                    "---\r\n"
                    + "\r\n".join(reversed(frontmatter_lines))
                    + "\r\n---\r\n"
                    + "\r\n".join(lines[closing + 1 :])
                    + "\r\n"
                ).encode("utf-8")
            )
            canonical_equivalent = run_cli(
                "validate-handoff", "--repo", repo, "--target", target
            )
            self.assertEqual(
                canonical_equivalent.returncode,
                0,
                canonical_equivalent.stdout + canonical_equivalent.stderr,
            )

            target.write_text(
                target.read_text(encoding="utf-8").replace(
                    "Training is running at capture time.",
                    "Training was completed at capture time.",
                ),
                encoding="utf-8",
            )
            modified = run_cli(
                "validate-handoff", "--repo", repo, "--target", target
            )
            self.assertEqual(modified.returncode, 7)
            self.assertIn(
                "handoff.immutable-modified",
                json.dumps(json.loads(modified.stdout)["data"]["errors"]),
            )
            noncanonical = target.with_name(f"{target.stem}_002.md")
            noncanonical.write_text(
                target.read_text(encoding="utf-8").replace(
                    f'handoff_id: "{target.stem}"',
                    f'handoff_id: "{noncanonical.stem}"',
                ),
                encoding="utf-8",
            )
            noncanonical_result = run_cli(
                "validate-handoff",
                "--repo",
                repo,
                "--target",
                noncanonical,
            )
            self.assertEqual(noncanonical_result.returncode, 7)
            self.assertIn(
                "filename.invalid",
                json.dumps(
                    json.loads(noncanonical_result.stdout)["data"]["errors"]
                ),
            )


    def test_validate_handoff_rejects_missing_malformed_and_legacy_seals(self):
        module = self.load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            handoffs = repo / "docs/handoffs"
            handoffs.mkdir(parents=True)
            source_dir = repo / "docs"
            source = source_dir / "260728_1530_unassigned_model-update.md"
            source.write_text(worklog_text(source.stem), encoding="utf-8")
            metadata = {
                "schema": "research-session-handoff-v1",
                "handoff_id": "260728_1645_unspecified-method_model-update",
                "captured_at": "2026-07-28T16:45:00+09:00",
                "timezone": "Asia/Seoul",
                "source_worklog_id": source.stem,
                "source_worklog_path": str(source.relative_to(repo)),
                "source_worklog_sha256": "0" * 64,
                "project": "example-research",
                "method": None,
                "title": "Model Update",
                "primary_activity": "implementation",
                "activity_types": ["implementation"],
                "documentation_status_at_capture": "in_progress",
                "work_status_at_capture": "running",
                "verification_status_at_capture": "not_verified",
                "active_process_state": "running",
                "verification_evidence": [],
                "repository": "example-research",
                "branch": None,
                "commit_at_capture": None,
                "coverage": "partial",
                "snapshot_sha256": "0" * 64,
            }
            target = handoffs / f"{metadata['handoff_id']}.md"

            variants = {
                "missing": {
                    k: v
                    for k, v in metadata.items()
                    if k != "snapshot_sha256"
                },
                "uppercase": {
                    **metadata,
                    "snapshot_sha256": ("A" * 64),
                },
                "short": {
                    **metadata,
                    "snapshot_sha256": ("0" * 63),
                },
                "legacy_schema": {
                    **metadata,
                    "schema": "chat-handoff-markdown-v1",
                },
                "legacy_field": {
                    **{k: v for k, v in metadata.items() if k != "snapshot_sha256"},
                    "snapshot_seal": "0" * 64,
                },
            }
            for name, variant in variants.items():
                with self.subTest(name=name):
                    arbitrary_order = "\n".join(
                        f"{key}: {module._json_yaml(value)}"
                        for key, value in variant.items()
                    )
                    target.write_text(
                        f"---\n{arbitrary_order}\n---\n\n{handoff_body()}",
                        encoding="utf-8",
                    )
                    result = run_cli(
                        "validate-handoff", "--repo", repo, "--target", target
                    )
                    self.assertEqual(result.returncode, 7)

    def test_validate_handoff_warns_when_source_changes_or_is_missing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            docs = repo / "docs"
            docs.mkdir()
            source = docs / "260728_1530_unassigned_model-update.md"
            source.write_text(worklog_text(source.stem), encoding="utf-8")
            args = (
                "allocate-handoff",
                "--repo",
                repo,
                "--source-worklog",
                source,
                "--captured-at",
                "2026-07-28T16:45:00+09:00",
                "--work-status-at-capture",
                "partial",
                "--verification-status-at-capture",
                "not_verified",
                "--documentation-status-at-capture",
                "in_progress",
                "--coverage",
                "partial",
                "--active-process-state",
                "unknown",
            )
            preview = run_cli_input(handoff_body(), *args)
            proposal = json.loads(preview.stdout)["data"]
            created = run_cli_input(
                handoff_body(),
                *args,
                "--allocation-token",
                proposal["allocation_token"],
                "--create",
            )
            self.assertEqual(created.returncode, 0, created.stderr)
            target = repo / proposal["path"]

            source.write_text(
                source.read_text(encoding="utf-8").replace(
                    "Exact test command is unknown.",
                    "Test command remains unknown.",
                ),
                encoding="utf-8",
            )
            changed = run_cli(
                "validate-handoff", "--repo", repo, "--target", target
            )
            self.assertEqual(changed.returncode, 0, changed.stderr)
            changed_payload = json.loads(changed.stdout)
            self.assertIn(
                "source.changed",
                [item["code"] for item in changed_payload["data"]["warnings"]],
            )

            source.unlink()
            missing = run_cli(
                "validate-handoff", "--repo", repo, "--target", target
            )
            self.assertEqual(missing.returncode, 0, missing.stderr)
            missing_payload = json.loads(missing.stdout)
            self.assertIn(
                "source.missing",
                [item["code"] for item in missing_payload["data"]["warnings"]],
            )

    def test_handoff_body_allows_markdown_links_with_evidence_tags(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            docs = repo / "docs"
            docs.mkdir()
            source = docs / "260728_1530_unassigned_model-update.md"
            source.write_text(worklog_text(source.stem), encoding="utf-8")
            body = handoff_body().replace(
                "The source worklog records the implementation scope.",
                "The [source](docs/source.md) records the implementation scope.",
            )
            preview = run_cli_input(
                body,
                "allocate-handoff",
                "--repo",
                repo,
                "--source-worklog",
                source,
                "--captured-at",
                "2026-07-28T16:45:00+09:00",
                "--work-status-at-capture",
                "partial",
                "--verification-status-at-capture",
                "not_verified",
                "--documentation-status-at-capture",
                "in_progress",
                "--coverage",
                "partial",
                "--active-process-state",
                "unknown",
            )
            self.assertEqual(preview.returncode, 0, preview.stderr)

if __name__ == "__main__":
    unittest.main()
