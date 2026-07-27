#!/usr/bin/env python3
"""Inspect, locate, allocate, and validate portable research worklogs."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlsplit, urlunsplit

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover - Python 3.9+ provides zoneinfo
    ZoneInfo = None  # type: ignore[assignment]


SCHEMA = "research-session-worklog-v1"
METHOD_SLUG_MAX_BYTES = 48
TITLE_SLUG_MAX_BYTES = 96
ACTIVE_DOCUMENTATION_STATUSES = {"in_progress", "checkpointed"}
ACTIVITIES = {
    "analysis",
    "implementation",
    "refactoring",
    "data_preparation",
    "training",
    "inference",
    "evaluation",
    "ablation",
    "debugging",
    "mixed",
}
CONCRETE_ACTIVITIES = ACTIVITIES - {"mixed"}
WORKLOG_SCOPES = {
    "code_analysis",
    "implementation_task",
    "data_pipeline",
    "experiment_batch",
    "evaluation_study",
    "debugging_incident",
    "mixed_pipeline",
}
WORK_STATUSES = {
    "planned",
    "running",
    "partial",
    "completed",
    "failed",
    "blocked",
    "aborted",
    "documentation_only",
}
DOCUMENTATION_STATUSES = {"in_progress", "checkpointed", "final"}
VERIFICATION_STATUSES = {
    "verified",
    "partially_verified",
    "not_verified",
    "verification_failed",
}
REQUIRED_KEYS = [
    "schema",
    "worklog_id",
    "created_at",
    "last_checkpoint_at",
    "finalized_at",
    "timezone",
    "project",
    "method",
    "title",
    "primary_activity",
    "activity_types",
    "worklog_scope",
    "work_status",
    "documentation_status",
    "verification_status",
    "repository",
    "remote_url",
    "branch",
    "commit_start",
    "commit_current",
    "commit_final",
    "task_key",
    "session_count",
    "checkpoint_count",
    "compact_count",
    "run_ids",
    "related_worklogs",
    "tags",
]
COMMON_HEADINGS = [
    "## Executive Summary",
    "## Original Request",
    "## Scope and Assumptions",
    "## Current State",
    "## Reproducibility Snapshot",
    "## Commands Executed",
    "## Observed Facts",
    "## Decisions",
    "## Artifacts",
    "## Failures and Anomalies",
    "## Uncertainty and Open Questions",
    "## Next Actions",
    "## Session Checkpoints",
    "## Knowledge Handoff",
]
PROFILE_HEADINGS = {
    "analysis": "## Analysis Record",
    "implementation": "## Implementation Record",
    "refactoring": "## Refactoring Record",
    "data_preparation": "## Data Preparation Record",
    "training": "## Training Record",
    "inference": "## Inference Record",
    "evaluation": "## Evaluation Record",
    "ablation": "## Ablation Record",
    "debugging": "## Debugging Record",
}
SECRET_PATTERNS = [
    (
        "secret.private-key",
        re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    ),
    ("secret.github-token", re.compile(r"\b(?:gh[opsu]_[A-Za-z0-9]{20,})\b")),
    ("secret.aws-access-key", re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")),
    (
        "secret.bearer-token",
        re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]{20,}", re.IGNORECASE),
    ),
]
CHECKPOINT_EVENTS = {
    "launch",
    "progress",
    "compact",
    "resume",
    "completion",
    "failure",
    "aborted",
}
TERMINAL_EVENTS = {"completion", "failure", "aborted"}
TERMINAL_WORK_STATUSES = {"completed", "failed", "aborted", "documentation_only"}
CHECKPOINT_RE = re.compile(
    r"^### (?P<timestamp>\S+) — (?P<event>[^:]+):",
    re.MULTILINE,
)
TOP_LEVEL_TITLE_RE = re.compile(r"^# (?!#)(?P<title>.+?)\s*$", re.MULTILINE)


class DocumentSessionError(Exception):
    """Expected CLI error with a stable exit code and safe details."""

    def __init__(
        self,
        message: str,
        exit_code: int = 3,
        code: str = "precondition",
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.exit_code = exit_code
        self.code = code
        self.details = details or {}


class JsonArgumentParser(argparse.ArgumentParser):
    """Raise structured usage errors instead of printing argparse text."""

    def error(self, message: str) -> None:
        raise DocumentSessionError(message, exit_code=2, code="cli.usage")


def seoul_timezone():
    if ZoneInfo is not None:
        try:
            return ZoneInfo("Asia/Seoul")
        except Exception:
            pass
    return timezone(timedelta(hours=9), name="Asia/Seoul")


def seoul_now(now: Optional[datetime] = None) -> datetime:
    value = now or datetime.now(timezone.utc)
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(seoul_timezone())


def normalize_slug(text: str) -> str:
    normalized = unicodedata.normalize("NFC", text).lower()
    pieces: list[str] = []
    pending_hyphen = False
    for char in normalized:
        if char.isalnum():
            if pending_hyphen and pieces:
                pieces.append("-")
            pieces.append(char)
            pending_hyphen = False
        else:
            pending_hyphen = True
    slug = "".join(pieces).strip("-")
    if not slug:
        raise ValueError("value does not contain a usable letter or number")
    return slug


def bounded_slug(slug: str, max_bytes: int) -> str:
    encoded = slug.encode("utf-8")
    if len(encoded) <= max_bytes:
        return slug
    digest = hashlib.sha256(encoded).hexdigest()[:8]
    byte_budget = max_bytes - len(digest) - 1
    pieces: list[str] = []
    used = 0
    for char in slug:
        width = len(char.encode("utf-8"))
        if used + width > byte_budget:
            break
        pieces.append(char)
        used += width
    prefix = "".join(pieces).rstrip("-") or "value"
    return f"{prefix}-{digest}"


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _candidate_has_status(candidate: dict[str, Any], statuses: set[str]) -> bool:
    value = candidate.get("documentation_status")
    return isinstance(value, str) and value in statuses


def _git(repo: Path, *args: str) -> Optional[str]:
    try:
        result = subprocess.run(
            ["git", "--no-optional-locks", *args],
            cwd=repo,
            check=False,
            text=True,
            capture_output=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def repository_root(repo: Path) -> Path:
    candidate = repo.expanduser().resolve()
    if not candidate.exists() or not candidate.is_dir():
        raise DocumentSessionError(
            "repository path is not an existing directory",
            code="repository.invalid",
        )
    git_root = _git(candidate, "rev-parse", "--show-toplevel")
    if git_root:
        return Path(git_root).resolve()
    return candidate


def sanitize_remote_url(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    value = value.strip()
    if not value:
        return None
    if "://" in value:
        parsed = urlsplit(value)
        hostname = parsed.hostname
        if not hostname:
            return None
        host = hostname
        try:
            port = parsed.port
        except ValueError:
            return None
        if port is not None:
            host = f"{host}:{port}"
        return urlunsplit((parsed.scheme, host, parsed.path, "", ""))
    scp_match = re.fullmatch(r"(?:[^@]+@)?([^:]+):(.+)", value)
    if scp_match:
        host, path = scp_match.groups()
        return f"ssh://{host}/{path.lstrip('/')}"
    if value.startswith("/") or value.startswith("."):
        return None
    return value


def inspect_repository(
    repo: Path,
    now: Optional[datetime] = None,
) -> dict[str, Any]:
    root = repository_root(repo)
    remote_url = sanitize_remote_url(_git(root, "remote", "get-url", "origin"))
    status_text = _git(root, "status", "--short")
    candidates = discover_worklogs(root, Path("docs"))
    active = [
        item
        for item in candidates
        if _candidate_has_status(item, ACTIVE_DOCUMENTATION_STATUSES)
    ]
    finalized = [
        item for item in candidates if _candidate_has_status(item, {"final"})
    ]
    return {
        "repository_root": str(root),
        "repository": root.name,
        "remote_url": remote_url,
        "branch": _git(root, "branch", "--show-current") or None,
        "head": _git(root, "rev-parse", "HEAD"),
        "dirty": bool(status_text),
        "dirty_summary": status_text.splitlines() if status_text else [],
        "timestamp": seoul_now(now).isoformat(timespec="seconds"),
        "active_worklogs": active,
        "finalized_worklogs": finalized,
    }


def _parse_scalar(raw: str) -> Any:
    raw = raw.strip()
    if raw == "null":
        return None
    if raw in {"true", "false"}:
        return raw == "true"
    if re.fullmatch(r"-?\d+", raw):
        return int(raw)
    if raw.startswith('"') or raw.startswith("["):
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise DocumentSessionError(
                f"invalid JSON-compatible YAML value on line {exc.lineno}",
                code="frontmatter.invalid-value",
            ) from exc
        if isinstance(value, dict):
            raise DocumentSessionError(
                "nested frontmatter objects are not supported",
                code="frontmatter.nested",
            )
        return value
    if raw == "":
        raise DocumentSessionError(
            "empty frontmatter values are not supported; use null",
            code="frontmatter.empty",
        )
    return raw


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        raise DocumentSessionError(
            "missing opening YAML frontmatter delimiter",
            code="frontmatter.missing",
        )
    closing_index: Optional[int] = None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            closing_index = index
            break
    if closing_index is None:
        raise DocumentSessionError(
            "missing closing YAML frontmatter delimiter",
            code="frontmatter.unclosed",
        )
    metadata: dict[str, Any] = {}
    for line_number, line in enumerate(lines[1:closing_index], start=2):
        stripped = line.rstrip("\r\n")
        if not stripped:
            continue
        if stripped[:1].isspace() or ":" not in stripped:
            raise DocumentSessionError(
                f"unsupported frontmatter structure on line {line_number}",
                code="frontmatter.structure",
            )
        key, raw = stripped.split(":", 1)
        if not re.fullmatch(r"[a-z][a-z0-9_]*", key):
            raise DocumentSessionError(
                f"invalid frontmatter key on line {line_number}",
                code="frontmatter.key",
            )
        if key in metadata:
            raise DocumentSessionError(
                f"duplicate frontmatter key on line {line_number}",
                code="frontmatter.duplicate",
            )
        metadata[key] = _parse_scalar(raw)
    return metadata, "".join(lines[closing_index + 1 :])


def _json_yaml(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    return json.dumps(value, ensure_ascii=False, separators=(", ", ": "))


def render_frontmatter(metadata: dict[str, Any]) -> str:
    lines = ["---"]
    for key in REQUIRED_KEYS:
        lines.append(f"{key}: {_json_yaml(metadata[key])}")
    lines.append("---")
    return "\n".join(lines)


def _task_key(
    repository_identity: str,
    objective: str,
    method: Optional[str],
    worklog_scope: str,
) -> str:
    payload = json.dumps(
        {
            "repository": unicodedata.normalize("NFC", repository_identity).strip(),
            "objective": " ".join(
                unicodedata.normalize("NFC", objective).lower().split()
            ),
            "method": (
                unicodedata.normalize("NFC", method).lower().strip()
                if method
                else None
            ),
            "worklog_scope": worklog_scope,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return f"task-{hashlib.sha256(payload).hexdigest()[:12]}"


def _render_template(
    template_path: Path,
    frontmatter: dict[str, Any],
    objective: str,
) -> str:
    try:
        template = template_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise DocumentSessionError(
            "worklog template is unavailable",
            code="template.unavailable",
        ) from exc
    replacements = {
        "{{FRONTMATTER}}": render_frontmatter(frontmatter),
        "{{TITLE}}": str(frontmatter["title"]),
        "{{OBJECTIVE}}": objective.strip(),
        "{{PRIMARY_ACTIVITY}}": str(frontmatter["primary_activity"]),
        "{{PROJECT}}": str(frontmatter["project"]),
        "{{REPOSITORY}}": str(frontmatter["repository"]),
        "{{BRANCH}}": (
            f"`{frontmatter['branch']}`"
            if frontmatter["branch"] is not None
            else "Unknown; Git branch evidence is unavailable."
        ),
        "{{COMMIT_START}}": (
            f"`{frontmatter['commit_start']}`"
            if frontmatter["commit_start"] is not None
            else "Unknown; Git commit evidence is unavailable."
        ),
    }
    for marker, value in replacements.items():
        template = template.replace(marker, value)
    unresolved = re.findall(r"\{\{[A-Z0-9_]+\}\}", template)
    if unresolved:
        raise DocumentSessionError(
            "worklog template contains unresolved markers",
            code="template.unresolved",
            details={"markers": sorted(set(unresolved))},
        )
    return template


def allocate_worklog(
    metadata: dict[str, Any],
    template_path: Path,
    create: bool,
) -> dict[str, Any]:
    root = repository_root(Path(metadata["repo_root"]))
    created = seoul_now(metadata.get("created_at"))
    if not isinstance(metadata.get("title"), str) or not isinstance(
        metadata.get("objective"), str
    ):
        raise DocumentSessionError(
            "title and objective must be strings",
            code="allocation.missing-input",
        )
    title = " ".join(metadata["title"].split())
    objective = " ".join(metadata["objective"].split())
    if not title or not objective:
        raise DocumentSessionError(
            "title and objective are required",
            code="allocation.missing-input",
        )
    method = metadata.get("method")
    if method is not None and not isinstance(method, str):
        raise DocumentSessionError(
            "method must be a string or null",
            code="allocation.missing-input",
        )
    if isinstance(method, str):
        method = method.strip() or None
    primary_activity = metadata.get("primary_activity")
    if not isinstance(primary_activity, str) or primary_activity not in ACTIVITIES:
        raise DocumentSessionError(
            "primary activity is invalid",
            code="allocation.activity",
        )
    worklog_scope = metadata.get("worklog_scope")
    if not isinstance(worklog_scope, str) or worklog_scope not in WORKLOG_SCOPES:
        raise DocumentSessionError(
            "worklog scope is invalid",
            code="allocation.scope",
        )
    work_status = metadata.get("work_status", "planned")
    if not isinstance(work_status, str) or work_status not in WORK_STATUSES:
        raise DocumentSessionError(
            "work status is invalid",
            code="allocation.status",
        )
    verification_status = metadata.get("verification_status", "not_verified")
    if (
        not isinstance(verification_status, str)
        or verification_status not in VERIFICATION_STATUSES
    ):
        raise DocumentSessionError(
            "verification status is invalid",
            code="allocation.status",
        )
    raw_activity_types = metadata.get("activity_types", [])
    if not isinstance(raw_activity_types, list) or any(
        not isinstance(item, str) or item not in CONCRETE_ACTIVITIES
        for item in raw_activity_types
    ):
        raise DocumentSessionError(
            "activity_types must contain concrete activities",
            code="allocation.activity",
        )
    activity_types = list(dict.fromkeys(raw_activity_types))
    if primary_activity == "mixed":
        if len(activity_types) < 2:
            raise DocumentSessionError(
                "mixed activity requires at least two concrete activity types",
                code="allocation.activity",
            )
    elif not activity_types:
        activity_types = [primary_activity]
    elif primary_activity not in activity_types:
        raise DocumentSessionError(
            "primary activity must appear in activity_types",
            code="allocation.activity",
        )
    method_slug = (
        bounded_slug(normalize_slug(str(method)), METHOD_SLUG_MAX_BYTES)
        if method
        else "unassigned"
    )
    title_slug = bounded_slug(normalize_slug(title), TITLE_SLUG_MAX_BYTES)
    prefix = f"{created.strftime('%y%m%d_%H%M')}_{method_slug}_{title_slug}"
    docs_dir = root / "docs"
    inspection = inspect_repository(root, created)
    repository_identity = inspection["remote_url"] or inspection["repository"]
    task_key = _task_key(
        repository_identity,
        objective,
        str(method) if method else None,
        worklog_scope,
    )

    index = 1
    while True:
        suffix = "" if index == 1 else f"_{index:02d}"
        path = docs_dir / f"{prefix}{suffix}.md"
        frontmatter = {
            "schema": SCHEMA,
            "worklog_id": path.stem,
            "created_at": created.isoformat(timespec="seconds"),
            "last_checkpoint_at": None,
            "finalized_at": None,
            "timezone": "Asia/Seoul",
            "project": metadata.get("project") or root.name,
            "method": method,
            "title": title,
            "primary_activity": primary_activity,
            "activity_types": activity_types,
            "worklog_scope": worklog_scope,
            "work_status": work_status,
            "documentation_status": "in_progress",
            "verification_status": verification_status,
            "repository": metadata.get("repository") or root.name,
            "remote_url": inspection["remote_url"],
            "branch": inspection["branch"],
            "commit_start": inspection["head"],
            "commit_current": inspection["head"],
            "commit_final": None,
            "task_key": task_key,
            "session_count": 1,
            "checkpoint_count": 0,
            "compact_count": 0,
            "run_ids": list(metadata.get("run_ids") or []),
            "related_worklogs": list(metadata.get("related_worklogs") or []),
            "tags": list(metadata.get("tags") or []),
        }
        markdown = _render_template(template_path, frontmatter, objective)
        secret_issues = _secret_issues(markdown)
        if secret_issues:
            raise DocumentSessionError(
                "secret-like content detected before allocation",
                exit_code=8,
                code="secret.detected",
                details={"issues": secret_issues},
            )
        if not create:
            try:
                path_exists = path.exists()
            except OSError as exc:
                raise DocumentSessionError(
                    "unable to inspect the allocation path",
                    code="allocation.write",
                ) from exc
            if not path_exists:
                return {
                    "path": str(path),
                    "frontmatter": frontmatter,
                    "markdown": markdown,
                    "created": False,
                }
            index += 1
            continue
        try:
            docs_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise DocumentSessionError(
                "unable to create the docs directory",
                code="allocation.write",
            ) from exc
        try:
            with path.open("x", encoding="utf-8", newline="\n") as handle:
                handle.write(markdown)
        except FileExistsError:
            index += 1
            continue
        except OSError as exc:
            raise DocumentSessionError(
                "unable to create the worklog",
                code="allocation.write",
            ) from exc
        return {
            "path": str(path),
            "frontmatter": frontmatter,
            "markdown": markdown,
            "created": True,
        }


def _candidate(path: Path) -> Optional[dict[str, Any]]:
    try:
        metadata, body = parse_frontmatter(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, DocumentSessionError):
        return None
    if metadata.get("schema") != SCHEMA:
        return None
    current_state = _section_text(body, "## Current State")
    next_actions = _section_text(body, "## Next Actions")
    return {
        "path": str(path.resolve()),
        "worklog_id": metadata.get("worklog_id"),
        "created_at": metadata.get("created_at"),
        "task_key": metadata.get("task_key"),
        "title": metadata.get("title"),
        "method": metadata.get("method"),
        "primary_activity": metadata.get("primary_activity"),
        "activity_types": metadata.get("activity_types"),
        "work_status": metadata.get("work_status"),
        "documentation_status": metadata.get("documentation_status"),
        "verification_status": metadata.get("verification_status"),
        "session_count": metadata.get("session_count"),
        "checkpoint_count": metadata.get("checkpoint_count"),
        "current_state": current_state.strip(),
        "next_actions": next_actions.strip(),
    }


def discover_worklogs(
    repo_root: Path,
    docs_dir: Path = Path("docs"),
) -> list[dict[str, Any]]:
    root = repository_root(repo_root)
    base = docs_dir if docs_dir.is_absolute() else root / docs_dir
    if not base.exists() or not base.is_dir():
        return []
    candidates: list[dict[str, Any]] = []
    for path in sorted(base.glob("*.md")):
        try:
            resolved = path.resolve()
        except OSError:
            continue
        if not path.is_file() or not _is_within(resolved, root):
            continue
        candidate = _candidate(path)
        if candidate is not None and not _worklog_identity_issues(
            resolved, root, candidate
        ):
            candidates.append(candidate)
    return candidates


def _resolve_path(repo_root: Path, value: str) -> Path:
    root = repository_root(repo_root)
    raw = Path(value).expanduser()
    candidate = raw if raw.is_absolute() else root / raw
    try:
        resolved = candidate.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise DocumentSessionError(
            "target worklog does not exist",
            exit_code=4,
            code="target.missing",
        ) from exc
    if not _is_within(resolved, root) or not resolved.is_file():
        raise DocumentSessionError(
            "target must be a regular file inside the repository",
            exit_code=3,
            code="target.unsafe",
        )
    return resolved


def resolve_target(
    repo_root: Path,
    target: Optional[str],
    task_key: Optional[str],
    for_write: bool = False,
) -> dict[str, Any]:
    root = repository_root(repo_root)
    if target:
        path = _resolve_path(root, target)
        candidate = _candidate(path)
        if candidate is None:
            raise DocumentSessionError(
                "target is not a research-session-worklog-v1 document",
                code="target.schema",
            )
        identity_issues = _worklog_identity_issues(path, root, candidate)
        if identity_issues:
            raise DocumentSessionError(
                "target does not match the canonical worklog identity",
                code="target.identity",
                details={
                    "path": candidate["path"],
                    "issues": [item["code"] for item in identity_issues],
                },
            )
        status = candidate["documentation_status"]
        if not isinstance(status, str) or status not in DOCUMENTATION_STATUSES:
            raise DocumentSessionError(
                "target has an invalid documentation status",
                code="target.status",
                details={"path": candidate["path"]},
            )
        if for_write and status == "final":
            raise DocumentSessionError(
                "finalized worklogs are immutable",
                exit_code=6,
                code="target.finalized",
                details={"path": candidate["path"]},
            )
        return candidate

    candidates = discover_worklogs(root, Path("docs"))
    active = [
        item
        for item in candidates
        if _candidate_has_status(item, ACTIVE_DOCUMENTATION_STATUSES)
    ]
    if task_key:
        active = [item for item in active if item.get("task_key") == task_key]
    if not active:
        raise DocumentSessionError(
            "no active worklog matches the selection",
            exit_code=4,
            code="target.not-found",
        )
    if len(active) > 1:
        raise DocumentSessionError(
            "multiple active worklogs match the selection",
            exit_code=5,
            code="target.ambiguous",
            details={"candidates": active},
        )
    return active[0]


def _issue(
    code: str,
    message: str,
    line: Optional[int] = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {"code": code, "message": message}
    if line is not None:
        result["line"] = line
    return result


def _secret_issues(text: str) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for rule, pattern in SECRET_PATTERNS:
        for match in pattern.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            issues.append(
                _issue(rule, "suspicious secret-like value detected", line=line)
            )
    return issues


def _worklog_identity_issues(
    path: Path,
    root: Path,
    metadata: dict[str, Any],
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    if metadata.get("worklog_id") != path.stem:
        issues.append(
            _issue("identity.filename", "worklog_id must equal the filename stem")
        )
    if path.parent != (root / "docs").resolve():
        issues.append(
            _issue("path.location", "worklog must be directly inside docs")
        )

    match = re.fullmatch(
        r"(?P<stamp>\d{6}_\d{4})_"
        r"(?P<method>[^_]+)_(?P<title>[^_]+?)"
        r"(?:_(?P<suffix>\d{2,}))?",
        path.stem,
    )
    filename_valid = match is not None
    if match is not None:
        method_part = match.group("method")
        title_part = match.group("title")
        suffix = match.group("suffix")
        try:
            expected_method = (
                bounded_slug(
                    normalize_slug(metadata["method"]), METHOD_SLUG_MAX_BYTES
                )
                if isinstance(metadata.get("method"), str)
                and metadata["method"].strip()
                else "unassigned"
            )
            expected_title = (
                bounded_slug(
                    normalize_slug(metadata["title"]), TITLE_SLUG_MAX_BYTES
                )
                if isinstance(metadata.get("title"), str)
                and metadata["title"].strip()
                else None
            )
        except ValueError:
            expected_method = None
            expected_title = None
        filename_valid = method_part == expected_method and title_part == expected_title
        if suffix is not None and int(suffix) < 2:
            filename_valid = False
        created_at = metadata.get("created_at")
        if isinstance(created_at, str):
            try:
                created = datetime.fromisoformat(created_at)
            except ValueError:
                created = None
            if created is not None and match.group("stamp") != created.strftime(
                "%y%m%d_%H%M"
            ):
                issues.append(
                    _issue(
                        "filename.timestamp",
                        "filename timestamp must match created_at",
                    )
                )
    if not filename_valid:
        issues.append(
            _issue("filename.invalid", "filename does not match the worklog contract")
        )
    return issues


def _parse_timestamp(
    value: Any,
    key: str,
    errors: list[dict[str, Any]],
) -> Optional[datetime]:
    if value is None:
        return None
    if not isinstance(value, str):
        errors.append(_issue("timestamp.type", f"{key} must be a string or null"))
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        errors.append(_issue("timestamp.invalid", f"{key} is not ISO-8601"))
        return None
    if parsed.tzinfo is None:
        errors.append(_issue("timestamp.offset", f"{key} must include an offset"))
        return None
    return parsed


def _section_text(body: str, heading: str) -> str:
    pattern = re.compile(
        rf"^{re.escape(heading)}\s*$\n(?P<content>.*?)(?=^##\s|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(body)
    return match.group("content") if match else ""


def validate_worklog(path: Path, repo_root: Path) -> dict[str, Any]:
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    root = repository_root(repo_root)
    raw_path = path.expanduser()
    candidate_path = raw_path if raw_path.is_absolute() else root / raw_path
    try:
        resolved = candidate_path.resolve(strict=True)
    except (OSError, RuntimeError):
        return {
            "valid": False,
            "errors": [_issue("path.missing", "worklog path does not exist")],
            "warnings": [],
        }
    if not _is_within(resolved, root):
        return {
            "valid": False,
            "errors": [_issue("path.unsafe", "worklog is outside the repository")],
            "warnings": [],
        }
    try:
        text = resolved.read_text(encoding="utf-8")
        metadata, body = parse_frontmatter(text)
    except (OSError, UnicodeError, DocumentSessionError) as exc:
        return {
            "valid": False,
            "errors": [_issue("frontmatter.invalid", str(exc))],
            "warnings": [],
        }

    for key in REQUIRED_KEYS:
        if key not in metadata:
            errors.append(_issue("frontmatter.required", f"missing field: {key}"))
    if errors:
        return {"valid": False, "errors": errors, "warnings": warnings}

    required_strings = (
        "schema",
        "worklog_id",
        "timezone",
        "project",
        "title",
        "primary_activity",
        "worklog_scope",
        "work_status",
        "documentation_status",
        "verification_status",
        "repository",
        "task_key",
    )
    for key in required_strings:
        if not isinstance(metadata[key], str):
            errors.append(
                _issue("frontmatter.type", f"{key} must be a string")
            )
    for key in (
        "method",
        "remote_url",
        "branch",
        "commit_start",
        "commit_current",
        "commit_final",
    ):
        if metadata[key] is not None and not isinstance(metadata[key], str):
            errors.append(
                _issue("frontmatter.type", f"{key} must be a string or null")
            )

    if metadata["schema"] != SCHEMA:
        errors.append(_issue("schema.unsupported", "unsupported worklog schema"))
    errors.extend(_worklog_identity_issues(resolved, root, metadata))
    if metadata["timezone"] != "Asia/Seoul":
        errors.append(_issue("timezone.invalid", "timezone must be Asia/Seoul"))
    task_key_value = metadata["task_key"]
    if not isinstance(task_key_value, str) or not re.fullmatch(
        r"task-[0-9a-f]{12}",
        task_key_value if isinstance(task_key_value, str) else "",
    ):
        errors.append(_issue("identity.task-key", "task_key has an invalid format"))

    created = _parse_timestamp(metadata["created_at"], "created_at", errors)
    last_checkpoint = _parse_timestamp(
        metadata["last_checkpoint_at"], "last_checkpoint_at", errors
    )
    finalized = _parse_timestamp(metadata["finalized_at"], "finalized_at", errors)
    for key, parsed in (
        ("created_at", created),
        ("last_checkpoint_at", last_checkpoint),
        ("finalized_at", finalized),
    ):
        if parsed is not None and parsed.utcoffset() != timedelta(hours=9):
            errors.append(_issue("timestamp.seoul", f"{key} must use +09:00"))
    if created and last_checkpoint and last_checkpoint < created:
        errors.append(
            _issue("timestamp.order", "last_checkpoint_at precedes created_at")
        )
    if created and finalized and finalized < created:
        errors.append(_issue("timestamp.order", "finalized_at precedes created_at"))

    enum_checks = [
        ("primary_activity", ACTIVITIES),
        ("worklog_scope", WORKLOG_SCOPES),
        ("work_status", WORK_STATUSES),
        ("documentation_status", DOCUMENTATION_STATUSES),
        ("verification_status", VERIFICATION_STATUSES),
    ]
    for key, allowed in enum_checks:
        if not isinstance(metadata[key], str) or metadata[key] not in allowed:
            errors.append(_issue("enum.invalid", f"invalid {key}"))

    activity_types = metadata["activity_types"]
    activity_types_valid = isinstance(activity_types, list) and bool(activity_types)
    if activity_types_valid:
        activity_types_valid = all(
            isinstance(item, str) and item in CONCRETE_ACTIVITIES
            for item in activity_types
        )
    if not activity_types_valid:
        errors.append(
            _issue(
                "activity.types",
                "activity_types must contain concrete activity values",
            )
        )
    elif metadata["primary_activity"] == "mixed":
        if len(set(activity_types)) < 2:
            errors.append(
                _issue("activity.mixed", "mixed activity requires at least two types")
            )
    elif (
        isinstance(metadata["primary_activity"], str)
        and metadata["primary_activity"] in ACTIVITIES
        and metadata["primary_activity"] not in activity_types
    ):
        errors.append(
            _issue(
                "activity.primary",
                "primary_activity must appear in activity_types",
            )
        )

    for key in ("run_ids", "related_worklogs", "tags"):
        if not isinstance(metadata[key], list) or any(
            not isinstance(item, str) for item in metadata[key]
        ):
            errors.append(
                _issue("frontmatter.list", f"{key} must be a list of strings")
            )
    counter_values: dict[str, Optional[int]] = {}
    for key in ("session_count", "checkpoint_count", "compact_count"):
        value = metadata[key]
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            errors.append(
                _issue("counter.invalid", f"{key} must be a non-negative integer")
            )
            counter_values[key] = None
        else:
            counter_values[key] = value

    title_matches = list(TOP_LEVEL_TITLE_RE.finditer(body))
    title_valid = (
        len(title_matches) == 1
        and isinstance(metadata["title"], str)
        and title_matches[0].group("title") == metadata["title"]
    )
    if title_matches and COMMON_HEADINGS:
        first_common = re.search(
            rf"^{re.escape(COMMON_HEADINGS[0])}\s*$",
            body,
            re.MULTILINE,
        )
        title_valid = bool(
            title_valid
            and first_common is not None
            and title_matches[0].start() < first_common.start()
        )
    if not title_valid:
        errors.append(
            _issue(
                "heading.title",
                "exactly one top-level title matching frontmatter title is required before the common sections",
            )
        )

    for heading in COMMON_HEADINGS:
        count = len(re.findall(rf"^{re.escape(heading)}\s*$", body, re.MULTILINE))
        if count != 1:
            errors.append(
                _issue(
                    "heading.count",
                    f"{heading} must appear exactly once",
                )
            )
    heading_matches = [
        re.search(rf"^{re.escape(heading)}\s*$", body, re.MULTILINE)
        for heading in COMMON_HEADINGS
    ]
    positions = [match.start() for match in heading_matches if match is not None]
    if len(positions) == len(COMMON_HEADINGS) and positions != sorted(positions):
        errors.append(
            _issue("heading.order", "common headings are out of required order")
        )

    checkpoint_section = _section_text(body, "## Session Checkpoints")
    checkpoints = list(CHECKPOINT_RE.finditer(checkpoint_section))
    checkpoint_times: list[datetime] = []
    checkpoint_events: list[str] = []
    for index, checkpoint in enumerate(checkpoints, start=1):
        event = checkpoint.group("event")
        checkpoint_events.append(event)
        if event not in CHECKPOINT_EVENTS:
            errors.append(
                _issue("checkpoint.event", f"checkpoint {index} has an invalid event")
            )
        parsed = _parse_timestamp(
            checkpoint.group("timestamp"),
            f"checkpoint {index} timestamp",
            errors,
        )
        if parsed is None:
            continue
        checkpoint_times.append(parsed)
        if parsed.utcoffset() != timedelta(hours=9):
            errors.append(
                _issue(
                    "timestamp.seoul",
                    f"checkpoint {index} timestamp must use +09:00",
                )
            )
        if created is not None and parsed < created:
            errors.append(
                _issue(
                    "timestamp.order",
                    f"checkpoint {index} precedes created_at",
                )
            )
        if len(checkpoint_times) > 1 and parsed < checkpoint_times[-2]:
            errors.append(
                _issue("timestamp.order", "checkpoint timestamps are out of order")
            )

    if (
        counter_values["checkpoint_count"] is not None
        and counter_values["checkpoint_count"] != len(checkpoints)
    ):
        errors.append(
            _issue(
                "counter.checkpoint",
                "checkpoint_count does not match checkpoint headings",
            )
        )
    compact_count = sum(
        1 for event in checkpoint_events if event == "compact"
    )
    if (
        counter_values["compact_count"] is not None
        and counter_values["compact_count"] != compact_count
    ):
        errors.append(
            _issue("counter.compact", "compact_count does not match compact events")
        )
    resume_count = sum(
        1 for event in checkpoint_events if event == "resume"
    )
    if (
        counter_values["session_count"] is not None
        and counter_values["session_count"] != 1 + resume_count
    ):
        errors.append(
            _issue("counter.session", "session_count does not match resume events")
        )
    if checkpoints and last_checkpoint is None:
        errors.append(
            _issue(
                "timestamp.checkpoint",
                "last_checkpoint_at is required when checkpoints exist",
            )
        )
    if not checkpoints and last_checkpoint is not None:
        errors.append(
            _issue(
                "timestamp.checkpoint",
                "last_checkpoint_at must be null without checkpoints",
            )
        )
    if checkpoint_times and last_checkpoint is not None:
        if last_checkpoint != checkpoint_times[-1]:
            errors.append(
                _issue(
                    "timestamp.checkpoint-latest",
                    "last_checkpoint_at must equal the latest checkpoint timestamp",
                )
            )

    is_final = metadata["documentation_status"] == "final"
    if is_final:
        current_head = _git(root, "rev-parse", "HEAD")
        if finalized is None:
            errors.append(
                _issue("final.required", "finalized_at is required for final worklogs")
            )
        if metadata["commit_final"] is None:
            if current_head is None:
                warnings.append(
                    _issue(
                        "final.commit-missing",
                        "final Git commit is unavailable; preserve that "
                        "evidence boundary",
                    )
                )
            else:
                errors.append(
                    _issue(
                        "final.commit-required",
                        "commit_final is required when Git HEAD is available",
                    )
                )
        elif isinstance(metadata["commit_final"], str) and current_head is not None:
            commit_object = f"{metadata['commit_final']}^{{commit}}"
            if _git(root, "cat-file", "-e", commit_object) is None:
                errors.append(
                    _issue(
                        "final.commit-unknown",
                        "commit_final must identify an available Git commit",
                    )
                )
        if not checkpoint_events or checkpoint_events[-1] not in TERMINAL_EVENTS:
            errors.append(
                _issue(
                    "final.checkpoint",
                    "final worklogs require a terminal checkpoint",
                )
            )
        if (
            not isinstance(metadata["work_status"], str)
            or metadata["work_status"] not in TERMINAL_WORK_STATUSES
        ):
            errors.append(
                _issue("final.status", "final worklogs require a terminal work status")
            )
        if (
            checkpoint_events
            and checkpoint_events[-1] in TERMINAL_EVENTS
            and isinstance(metadata["work_status"], str)
        ):
            expected_statuses = {
                "completion": {"completed", "documentation_only"},
                "failure": {"failed"},
                "aborted": {"aborted"},
            }
            if metadata["work_status"] not in expected_statuses[
                checkpoint_events[-1]
            ]:
                errors.append(
                    _issue(
                        "final.event-status",
                        "terminal checkpoint event and work status disagree",
                    )
                )
        if finalized is not None and checkpoint_times:
            if finalized != checkpoint_times[-1]:
                errors.append(
                    _issue(
                        "final.timestamp",
                        "finalized_at must equal the terminal checkpoint timestamp",
                    )
                )
    elif metadata["finalized_at"] is not None or metadata["commit_final"] is not None:
        errors.append(
            _issue(
                "final.active",
                "active worklogs must not set final fields",
            )
        )

    has_checkpoint = (
        counter_values["checkpoint_count"] is not None
        and counter_values["checkpoint_count"] > 0
    )
    primary_activity = metadata["primary_activity"]
    if has_checkpoint or is_final:
        if primary_activity == "mixed" and activity_types_valid:
            present = [
                PROFILE_HEADINGS[item]
                for item in activity_types
                if PROFILE_HEADINGS[item] in body
            ]
            if len(present) < 2:
                errors.append(
                    _issue(
                        "activity.profile",
                        "mixed worklogs require at least two activity profiles",
                    )
                )
        elif isinstance(primary_activity, str) and primary_activity in PROFILE_HEADINGS:
            required_profile = PROFILE_HEADINGS[primary_activity]
            if required_profile not in body:
                errors.append(
                    _issue(
                        "activity.profile",
                        f"missing activity profile: {required_profile}",
                    )
                )
    for heading in PROFILE_HEADINGS.values():
        if heading in body and not _section_text(body, heading).strip():
            errors.append(
                _issue("activity.empty", f"activity profile is empty: {heading}")
            )

    errors.extend(_secret_issues(text))

    artifacts = _section_text(body, "## Artifacts")
    for match in re.finditer(r"^- path: `([^`]+)`\s*$", artifacts, re.MULTILINE):
        raw_path = match.group(1)
        artifact_path = Path(raw_path)
        line = text.count("\n", 0, text.find(match.group(0))) + 1
        if artifact_path.is_absolute() or ".." in artifact_path.parts:
            errors.append(
                _issue(
                    "artifact.unsafe",
                    "artifact paths must be repository-relative",
                    line=line,
                )
            )
            continue
        try:
            resolved_artifact = (root / artifact_path).resolve(strict=True)
        except (OSError, RuntimeError):
            warnings.append(
                _issue(
                    "artifact.missing",
                    f"artifact is missing: {raw_path}",
                    line=line,
                )
            )
            continue
        if not _is_within(resolved_artifact, root):
            errors.append(
                _issue(
                    "artifact.unsafe",
                    "artifact symlink resolves outside the repository",
                    line=line,
                )
            )

    return {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "path": str(resolved),
        "worklog_id": metadata.get("worklog_id"),
    }


def _success(command: str, data: dict[str, Any], warnings=None) -> None:
    print(
        json.dumps(
            {
                "ok": True,
                "command": command,
                "data": data,
                "warnings": warnings or [],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def _failure(command: str, error: DocumentSessionError) -> None:
    print(
        json.dumps(
            {
                "ok": False,
                "command": command,
                "error": {
                    "code": error.code,
                    "message": str(error),
                    "details": error.details,
                },
            },
            ensure_ascii=False,
            indent=2,
        ),
        file=sys.stderr,
    )


def _argument_timestamp(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "created-at must be an ISO-8601 timestamp"
        ) from exc
    if parsed.tzinfo is None:
        raise argparse.ArgumentTypeError("created-at must include an offset")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = JsonArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser("inspect")
    inspect_parser.add_argument("--repo", default=".")

    locate_parser = subparsers.add_parser("locate")
    locate_parser.add_argument("--repo", default=".")
    locate_parser.add_argument("--target")
    locate_parser.add_argument("--task-key")
    locate_parser.add_argument("--for-write", action="store_true")

    allocate_parser = subparsers.add_parser("allocate")
    allocate_parser.add_argument("--repo", default=".")
    allocate_parser.add_argument("--title", required=True)
    allocate_parser.add_argument("--method")
    allocate_parser.add_argument("--objective", required=True)
    allocate_parser.add_argument(
        "--activity", choices=sorted(ACTIVITIES), required=True
    )
    allocate_parser.add_argument(
        "--activity-type",
        action="append",
        choices=sorted(CONCRETE_ACTIVITIES),
        default=[],
    )
    allocate_parser.add_argument(
        "--scope", choices=sorted(WORKLOG_SCOPES), required=True
    )
    allocate_parser.add_argument("--created-at", type=_argument_timestamp)
    allocate_parser.add_argument("--create", action="store_true")

    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("--repo", default=".")
    validate_parser.add_argument("--target", required=True)

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    command = "unknown"
    try:
        parser = build_parser()
        args = parser.parse_args(argv)
        command = args.command
        if command == "inspect":
            data = inspect_repository(Path(args.repo))
            _success(command, data)
            return 0
        if command == "locate":
            data = resolve_target(
                Path(args.repo),
                args.target,
                args.task_key,
                for_write=args.for_write,
            )
            _success(command, data)
            return 0
        if command == "allocate":
            root = repository_root(Path(args.repo))
            metadata = {
                "repo_root": root,
                "title": args.title,
                "method": args.method,
                "objective": args.objective,
                "primary_activity": args.activity,
                "activity_types": args.activity_type,
                "worklog_scope": args.scope,
                "created_at": args.created_at,
            }
            template = (
                Path(__file__).resolve().parents[1] / "assets/worklog-template.md"
            )
            data = allocate_worklog(metadata, template, args.create)
            _success(command, data)
            return 0
        if command == "validate":
            result = validate_worklog(Path(args.target), Path(args.repo))
            _success(command, result, result["warnings"])
            if result["valid"]:
                return 0
            if any(item["code"].startswith("secret.") for item in result["errors"]):
                return 8
            if any(item["code"] == "path.missing" for item in result["errors"]):
                return 4
            if any(item["code"] == "path.unsafe" for item in result["errors"]):
                return 3
            return 7
        raise DocumentSessionError(
            "unsupported command", exit_code=2, code="cli.command"
        )
    except DocumentSessionError as error:
        _failure(command, error)
        return error.exit_code
    except ValueError as error:
        expected = DocumentSessionError(str(error), exit_code=3, code="input.invalid")
        _failure(command, expected)
        return expected.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
