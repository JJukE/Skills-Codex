# Worklog Schema

## Contents

- [Filename](#filename)
- [Required Frontmatter](#required-frontmatter)
- [Identity Fields](#identity-fields)
- [Enumerations](#enumerations)
- [Required Common Sections](#required-common-sections)
- [Evidence Rules](#evidence-rules)
- [Validation Invariants](#validation-invariants)
- [Standalone Handoff Schema](#standalone-handoff-schema)

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

## Standalone Handoff Schema

Use this schema only for the immutable file produced by `handoff`. The source
worklog keeps `research-session-worklog-v1` and is not edited.

### Filename and Location

Create handoffs at:

```text
docs/handoffs/YYMMDD_HHMM_method-name_title.md
```

- Interpret the timestamp in `Asia/Seoul`.
- Derive method and title only from source worklog frontmatter.
- Use `unspecified-method` in the filename when source `method` is null or
  empty; keep `method: null` in handoff frontmatter.
- Reuse the worklog slug normalization and the 48-byte method and 96-byte title
  bounds.
- Append `_02`, `_03`, and so on when the path exists.
- Set `handoff_id` to the complete filename stem, including a collision
  suffix.
- Never overwrite, edit, or reuse an existing path.

### Required Frontmatter

Write fields in this order:

```yaml
---
schema: "research-session-handoff-v1"
handoff_id: "YYMMDD_HHMM_method-name_title"
captured_at: "YYYY-MM-DDTHH:MM:SS+09:00"
timezone: "Asia/Seoul"
source_worklog_id: "YYMMDD_HHMM_method-name_title"
source_worklog_path: "docs/YYMMDD_HHMM_method-name_title.md"
source_worklog_sha256: "64-lowercase-hex-characters"
project: "repository-project"
method: null
title: "Human-readable title"
primary_activity: "mixed"
activity_types: ["implementation", "evaluation", "debugging"]
documentation_status_at_capture: "checkpointed"
work_status_at_capture: "running"
verification_status_at_capture: "partially_verified"
active_process_state: "running"
verification_evidence: ["logs/run.log", "tests/result.txt"]
repository: "repository-name"
branch: "main"
commit_at_capture: "git-commit"
coverage: "partial"
snapshot_sha256: "64-lowercase-hex-characters"
---
```

Rules:

- Copy `source_worklog_id`, project, method, title, primary activity, and
  activity types from the source.
- Store `source_worklog_path` as a forward-slash, repository-relative path to
  a canonical worklog directly under `docs/`.
- Hash the exact source worklog bytes into `source_worklog_sha256`.
- Inspect the current repository basename, branch, and HEAD at capture. Use
  `null` for unavailable branch or commit evidence.
- Copy the source documentation status exactly. An active source remains
  `in_progress` or `checkpointed`; a finalized source remains `final`.
- Derive work, verification, process, and coverage status from current
  inspection. These may differ from the source worklog's earlier status.
- Use `coverage: complete` only when all evidence relevant to the snapshot was
  inspected. Otherwise use `partial`.
- List inspected verification paths or identifiers. `verified` requires at
  least one entry.
- Never pair `active_process_state: running` with
  `work_status_at_capture: completed` or `aborted`.
- Keep unknown nullable scalars null. Keep frontmatter flat and
  JSON-compatible.

`active_process_state` values:

```text
none
running
completed
failed
unknown
```

`coverage` values:

```text
complete
partial
```

Reuse the worklog `primary_activity`, `activity_types`,
`documentation_status`, `work_status`, and `verification_status`
enumerations for their corresponding capture fields.

### Required Body

The body starts with:

```text
# <source title> - Research Handoff
```

Keep these sections exactly once and in order:

```text
## Current Scope and State
## Implementation Changes
## Experiment and Run Evidence
## Observed Results
## Decisions
## Failures and Anomalies
## Artifacts
## Reproducibility Constraints
## Uncertainty and Evidence Boundaries
## Next Actions
## Coverage Limitations
```

Each section must contain at least one `[observed]`, `[interpretation]`,
`[decision]`, or `[unknown]` classification. Use an explicit unknown when no
evidence is available. Frontmatter is supplied by the helper; do not put
frontmatter or unresolved template markers in the body.

### Immutable Snapshot Seal

`snapshot_sha256` is exactly 64 lowercase hexadecimal characters. It covers
all required frontmatter except `snapshot_sha256` plus the complete body.

Canonicalization:

1. Parse flat frontmatter and serialize the sealed fields in the required order
   with the helper's JSON-compatible scalar rendering.
2. Exclude `snapshot_sha256` itself.
3. Normalize CRLF and CR to LF in the body, remove leading blank lines, and keep
   exactly one terminal LF. Preserve internal headings, whitespace, and code
   blocks.
4. Hash UTF-8 bytes of the canonical sealed frontmatter, two LF characters,
   and canonical body with SHA-256.

Frontmatter order, spacing, or LF versus CRLF does not change the seal because
validation parses and canonicalizes those forms. Any metadata value or body
change causes `handoff.immutable-modified`. Missing, uppercase, short, legacy,
or mismatched seals are invalid. Validation never creates, repairs, or replaces
a seal.

### Source Portability

Creation requires a valid source worklog. Later validation behaves as follows:

- matching source bytes: no source warning;
- same source identity with changed bytes: `source.changed` warning;
- unavailable source path: `source.missing` warning;
- existing source with a mismatched schema, ID, or filename identity: hard
  validation error.

The warnings preserve portability without changing the point-in-time seal.

### Allocation Transaction

`allocate-handoff` reads the completed body from standard input.

- Preview chooses the exact collision-safe path and returns canonical metadata,
  body, Markdown, capture timestamp, seal, and allocation token without writing.
- The allocation token is a deterministic integrity and drift guard, not a
  secret or authorization mechanism.
- Create requires the preview `captured_at`, token, identical body, identical
  capture flags, unchanged source bytes, unchanged Git capture state, and the
  same available path.
- Any drift fails before publication. Create never recalculates a suffix.
- Publication writes a complete temporary file in `docs/handoffs/`, flushes
  it, and claims the target exclusively. Concurrent creates yield one complete
  winner and one conflict.
- After publication, the helper re-reads and validates the handoff. It removes
  only its newly created target if self-validation fails.
