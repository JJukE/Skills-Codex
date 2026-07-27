# Worklog Schema

Use this reference when creating, checkpointing, validating, or finalizing a
worklog. Keep frontmatter flat and JSON-compatible so the bundled helper can
parse it without a YAML dependency.

## Filename

Create new worklogs at:

```text
docs/YYMMDD_HHMM_method-name_title.md
```

- Interpret the initial timestamp in `Asia/Seoul`.
- Normalize method and title to lowercase kebab-case.
- Bound the method slug to 48 UTF-8 bytes and the title slug to 96 UTF-8 bytes.
  For a longer slug, keep the largest character-safe prefix that fits and append
  `-` plus the first eight hex characters of its SHA-256 digest.
- Use `unassigned` in the filename when the method is unknown.
- Keep `method: null` in frontmatter when the method is unknown.
- If the path exists, append `_02`, `_03`, and so on.
- Never change the initial timestamp or `worklog_id`.
- Never overwrite an existing file.
- Normalize allocation title and objective whitespace to one safe line before
  rendering Markdown so embedded headings cannot alter the schema.

## Required Frontmatter

Write fields in this order:

```yaml
---
schema: "research-session-worklog-v1"
worklog_id: "YYMMDD_HHMM_method-name_title"
created_at: "YYYY-MM-DDTHH:MM:SS+09:00"
last_checkpoint_at: null
finalized_at: null
timezone: "Asia/Seoul"
project: "repository-name"
method: null
title: "Human-readable title"
primary_activity: "implementation"
activity_types: ["implementation"]
worklog_scope: "implementation_task"
work_status: "planned"
documentation_status: "in_progress"
verification_status: "not_verified"
repository: "repository-name"
remote_url: null
branch: null
commit_start: null
commit_current: null
commit_final: null
task_key: "task-0123456789ab"
session_count: 1
checkpoint_count: 0
compact_count: 0
run_ids: []
related_worklogs: []
tags: []
---
```

Rules:

- Use `null` for an unknown scalar. Do not use empty strings, `"unknown"`, or
  guessed values.
- Use empty arrays for known-empty collections.
- Use the repository basename for `project` unless repository evidence or an
  explicit argument supplies a stable project name.
- Store a sanitized remote URL with no credentials or query string. Use `null`
  when it cannot be recorded safely.
- Keep worktree dirtiness and changed-file detail in `Reproducibility Snapshot`,
  not in frontmatter.
- Do not store an unstable Codex session identifier.
- Keep the schema flat. Do not add nested objects.

## Identity Fields

`worklog_id` is the filename stem. A collision suffix is part of the ID.

`task_key` is a deterministic hint, not proof that two tasks are identical. The
helper hashes normalized repository identity, objective, method, and scope. Use
the selection criteria in `lifecycle-and-selection.md` before reusing a file.

`commit_start` captures HEAD at allocation when Git evidence is available.
Update `commit_current` only from repository evidence. Set `commit_final` from
HEAD during finalization when available. A dirty tree can make a commit
insufficient to reproduce the work, so record the relevant changed paths and
diff summary in the body.

## Enumerations

`primary_activity`:

```text
analysis
implementation
refactoring
data_preparation
training
inference
evaluation
ablation
debugging
mixed
```

`activity_types` contains one or more concrete activities. When
`primary_activity` is `mixed`, include at least two concrete activities and do
not include `mixed` in the array.

`worklog_scope`:

```text
code_analysis
implementation_task
data_pipeline
experiment_batch
evaluation_study
debugging_incident
mixed_pipeline
```

`work_status`:

```text
planned
running
partial
completed
failed
blocked
aborted
documentation_only
```

`documentation_status`:

```text
in_progress
checkpointed
final
```

`verification_status`:

```text
verified
partially_verified
not_verified
verification_failed
```

## Required Common Sections

Keep every common section, in this order:

```text
# Title
## Executive Summary
## Original Request
## Scope and Assumptions
## Current State
## Reproducibility Snapshot
## Commands Executed
## Observed Facts
## Decisions
## Artifacts
## Failures and Anomalies
## Uncertainty and Open Questions
## Next Actions
## Session Checkpoints
## Knowledge Handoff
```

Do not create empty activity-specific sections. Add the profile section only
when the activity occurred or its evidence was inspected.

## Evidence Rules

- Put only commands that actually ran under `Commands Executed`.
- Put proposed commands under a clearly labeled `Suggested, Not Executed`
  subsection.
- Mark observations as observed and interpretations as interpretations.
- Cite repository-relative source, config, log, metric, checkpoint, and artifact
  paths where available.
- Quote only decisive lines. Do not copy full logs or full diffs.
- Record missing evidence explicitly.
- Redact credentials instead of preserving them for reproducibility.
- Treat a running job as running, not completed.
- Treat selected qualitative samples as qualitative and selected.
- Treat one run or one seed as one unit, not an aggregate conclusion.
- Treat a reported pass without its command, exit status, or output as
  `verification_status: not_verified`.
- Use `work_status: completed` only when inspected evidence supports a terminal
  outcome; changed files alone support at most `partial`.
- Never infer branch, commit, or remote metadata. Populate them from repository
  inspection or leave them null.

Record local artifacts in this canonical form when a concrete path is known:

```markdown
- path: `outputs/run-001/metrics.json`
  role: aggregated metric output
  evidence: produced by the recorded evaluation command
```

The `path` value must be repository-relative, must not contain `..`, and must
not resolve outside the repository through a symlink. Label an unavailable or
external artifact without presenting it as a local `path` entry.

## Validation Invariants

- `created_at` never changes.
- `last_checkpoint_at` is null until the first checkpoint.
- All lifecycle timestamps and checkpoint headings use `+09:00`.
- `last_checkpoint_at` equals the latest append-only checkpoint timestamp.
- `finalized_at` is null before finalization and equals the terminal checkpoint
  timestamp afterward.
- `commit_final` is null before finalization. It may remain null afterward only
  when the current repository has no available Git HEAD, which produces a
  validation warning. When HEAD is available, it is required and must identify
  a commit available in the repository. A later current HEAD may differ.
- `checkpoint_count` equals the number of timestamped checkpoint headings.
- `compact_count` equals checkpoints explicitly labeled with the `compact`
  event.
- `session_count` increases only when a resume checkpoint establishes a new
  Codex session.
- A final worklog is immutable.
- A final worklog ends with `completion`, `failure`, or `aborted` and uses a
  terminal work status.
- Every recorded local artifact path either exists or is labeled missing.
