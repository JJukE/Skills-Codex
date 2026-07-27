from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
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


if __name__ == "__main__":
    unittest.main()
