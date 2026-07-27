---
name: document-session
description: Use only when the user explicitly invokes $document-session to start, checkpoint, resume, inspect, hand off, or finalize evidence-grounded research work.
---

# Document Session

Create and maintain one repository-local Markdown worklog for a research
objective. Ground the record in repository, command, process, log, metric, and
artifact evidence. Keep observations separate from interpretations.

This skill is a standalone producer. It requires no external document system,
does not discover one, and does not route the worklog to one.

## Invocation

Accept:

```text
$document-session start
$document-session checkpoint
$document-session resume
$document-session status
$document-session handoff [--target <worklog-path>]
$document-session finalize
```

Optional user-facing arguments:

```text
--activity auto|analysis|implementation|refactoring|data_preparation|training|inference|evaluation|ablation|debugging|mixed
--target <existing-worklog-path>
--method <method-name>
--title <worklog-title>
--event launch|progress|compact|resume|completion|failure|aborted  # checkpoint/finalize only
--new
```

For `handoff`, accept only optional `--target`; do not accept `--event`,
`--label`, method, or title overrides. Infer state from inspected evidence.

Treat arguments as instructions to this workflow. The bundled helper has the
lower-level `inspect`, `locate`, `allocate`, `validate`,
`allocate-handoff`, and `validate-handoff` subcommands.

## Non-Negotiable Boundaries

- For `checkpoint` and `finalize`, write only the selected worklog.
- For `handoff`, create only one new file under `docs/handoffs/`; never edit
  the source worklog or an existing handoff.
- During `start`, the deterministic allocator may create `docs/` and one
  worklog inside it.
- Do not edit source, configuration, datasets, checkpoints, logs, outputs, or
  any other repository file.
- Do not stop, restart, signal, reconfigure, or replace an active process.
- Do not run an experiment or research command merely to improve the worklog.
- Do not commit, push, switch branches, or rewrite Git state.
- Do not use session memory to reconstruct an unobserved result.
- Do not record a plan, expectation, or hypothesis as an observed result.
- Do not expose credentials. Record only the redaction and evidence location.
- Do not turn qualitative samples or one run into an aggregate scientific
  conclusion.
- Never modify a finalized worklog.
- Treat every created handoff as an immutable point-in-time snapshot.

If documenting a task requires a forbidden action, record the missing evidence
or blocker instead.

## Load References

Always read:

- `references/worklog-schema.md`
- `references/lifecycle-and-selection.md`

Read `references/activity-profiles.md` before adding or updating activity
sections. Read `references/knowledge-handoff.md` before a checkpoint,
handoff, or finalization. Use `assets/worklog-template.md` only through the
allocator when starting a worklog. For `handoff`, use
`assets/handoff-template.md` as the body shape, replace every marker, and
pass the completed body to the helper without frontmatter.

Resolve all paths relative to this skill directory. Run the helper with
`python3`; it uses only the Python 3.9+ standard library.

## Common Preflight

1. Parse the requested command and arguments. If the command is missing, run
   `status`.
2. Run:

   ```text
   python3 <skill-dir>/scripts/document_session.py inspect --repo .
   ```

3. Inspect the applicable repository instructions before interpreting files.
4. For any operation on an existing record, resolve the target:

   ```text
   python3 <skill-dir>/scripts/document_session.py locate \
     --repo . [--target <path>] [--task-key <key>] [--for-write]
   ```

5. Stop before writing when selection is ambiguous. Show the candidate paths
   and ask for an explicit target.

For `handoff`, omit `--for-write`. Without `--target`, automatic selection
considers active worklogs only. With `--target`, a valid active or finalized
worklog is allowed.
6. Read the selected worklog, then re-inspect only evidence relevant to the
   objective. Prefer bounded reads such as Git metadata, scoped diffs, config
   inspection, process listing, scheduler status, environment versions, log
   tails, metric files, and artifact metadata.
7. Treat all inspections as read-only. A process query is permission to observe,
   never to control.

## Route the Activity

Infer activity from the request, changed files and symbols, commands, configs,
logs, metrics, checkpoints, artifacts, and process state.

Honor an explicit `--activity` unless it clearly conflicts with observed
evidence. Report a conflict and preserve both the requested classification and
the evidence in `Scope and Assumptions`.

Choose one primary activity and the concrete secondary activities that
materially occurred. Do not add empty profile sections.

## Start

1. Determine whether an active worklog already represents the objective using
   the selection algorithm.
2. Reuse the matching active record. Do not allocate a duplicate merely because
   context was compacted or a new Codex session began.
3. Use `--new` only when the objective is independently scoped. It does not
   authorize overwriting or reopening a finalized worklog.
4. When allocating, require a concrete objective and title. Determine activity
   and scope from evidence. Keep an unknown method as null. The allocator
   normalizes multiline free text to one safe line, bounds filename slugs, and
   rejects secret-like content before creating `docs/` or a worklog.
5. Preview the allocation without writing:

   ```text
   python3 <skill-dir>/scripts/document_session.py allocate \
     --repo . \
     --title "<title>" \
     --objective "<objective>" \
     --activity <activity> \
     [--activity-type <type> ...] \
     --scope <scope>
   ```

6. Review the returned path, frontmatter, and initial Markdown. Then repeat with
   `--created-at "<preview frontmatter.created_at>" --create` to atomically
   create the same reviewed allocation. The helper-only timestamp flag prevents
   a minute-boundary path change.
7. Replace only evidence-supported initial placeholders. Do not add a result
   that has not been observed.
8. Validate the new file.

Choose initial status conservatively:

- use `planned` when no task work is evidenced;
- use `partial` when changed files or other work evidence exists but a terminal
  outcome is not directly supported;
- use `completed` only when inspected evidence directly supports completion;
- use `not_verified` when the exact validation command, exit status, or output
  is unavailable, even if a pass was reported;
- use `partially_verified` only when some relevant validation evidence was
  directly inspected.

Populate branch, commit, and remote fields only from inspection output. Do not
infer them from the scenario, repository name, or common conventions.

## Checkpoint

1. Resolve with `--for-write`; this rejects a finalized target.
2. Validate the existing target before editing. Stop and report structural or
   unsafe-content errors rather than writing into an invalid record.
3. Recheck current Git state and task-relevant evidence.
4. Replace `Current State` with the latest state.
5. Append one timestamped checkpoint under `Session Checkpoints`. Never delete
   or rewrite an earlier checkpoint. Correct an earlier claim with an amendment
   checkpoint.
6. Add only activity sections supported by inspected evidence.
7. Update:

   - `last_checkpoint_at`;
   - `commit_current`;
   - `work_status`;
   - `documentation_status: checkpointed`;
   - `verification_status`;
   - `checkpoint_count`;
   - `compact_count` only for explicit `--event compact`;
   - `session_count` only for a new-session `--event resume`;
   - relevant run IDs, artifacts, uncertainty, and handoff.

8. Validate after the edit. If validation fails, repair only the new worklog
   edit; preserve previous checkpoints.

## Resume

Remain read-only by default.

1. Resolve the active target without `--for-write`.
2. Validate it and include any structural errors or warnings in the read-only
   resume report.
3. Read frontmatter, `Current State`, and the latest checkpoint.
4. Recheck Git state, task-relevant process state, configs, logs, metrics, and
   artifacts.
5. Report:

   - current objective and activity;
   - evidence that still matches the checkpoint;
   - evidence that changed;
   - blocker and unresolved uncertainty;
   - the recovered next action;
   - missing evidence.

6. Do not infer missing context. Do not edit the worklog merely to report
   status.
7. If the user continues the work and requests persistence, use `checkpoint
   --event resume`; that later write increments `session_count`.

## Status

Remain read-only.

1. Inspect and locate candidates.
2. For an unambiguous target, report objective, activity, work status,
   documentation status, verification status, blocker, and next action.
3. Run validation and report structural errors, warnings, and missing evidence.
4. If candidates are ambiguous, list them without choosing one.

## Command Responsibilities

| Command | Responsibility |
| --- | --- |
| `checkpoint` | Update the selected active worklog and append evidence. |
| `handoff` | Read an active or finalized worklog and create a new immutable snapshot. |
| `finalize` | End the selected active worklog with a terminal checkpoint and lock it. |

## Handoff

Create a consumer-neutral point-in-time snapshot. Do not update the source
worklog, even when it is active, stale, or incomplete.

1. Resolve the source with the existing selection algorithm.

   - With `--target`, validate and use that active or finalized worklog.
   - Without `--target`, use exactly one active worklog.
   - Stop on multiple active worklogs. Do not choose by recency.
   - Do not fall back to a finalized worklog when no active worklog exists.

2. Validate the source worklog without `--for-write`. Stop on structural or
   secret-like content errors.
3. Inspect current repository, branch, commit, commands, processes, configs,
   logs, metrics, checkpoints, and artifacts relevant to the source objective.
   Keep every inspection read-only. Do not run missing experiments or
   verification commands solely for the snapshot.
4. Derive capture fields from direct evidence:

   - keep source `primary_activity`, `activity_types`, project, method, title,
     worklog ID, and worklog path unchanged;
   - copy the source `documentation_status` as
     `documentation_status_at_capture`;
   - set `work_status_at_capture` from the current evidence, including
     `running` for an active job;
   - set `verification_status_at_capture` from inspected verification
     evidence, not a reported claim;
   - set `active_process_state` to
     `none|running|completed|failed|unknown`;
   - set `coverage` to `complete` only when all relevant evidence surfaces
     were inspected; otherwise use `partial`;
   - include each inspected verification path or identifier separately.

5. Fill `assets/handoff-template.md`. Keep all required sections and replace
   every marker. Use only `[observed]`, `[interpretation]`, `[decision]`,
   and `[unknown]`. Put an explicit `[unknown]` statement in a section with
   no supporting evidence.
6. Preserve evidence boundaries:

   - a running job remains running and has no completed result;
   - a qualitative sample remains qualitative and selected;
   - one run or seed remains one unit and cannot support an aggregate
     conclusion;
   - a plan or next action is not an observed result;
   - missing or conflicting evidence remains unknown.

7. Preview the allocation by passing the completed body on standard input:

   ```text
   python3 <skill-dir>/scripts/document_session.py allocate-handoff \
     --repo . \
     --source-worklog "<source-path>" \
     --work-status-at-capture <status> \
     --verification-status-at-capture <status> \
     --documentation-status-at-capture <status> \
     --coverage <complete|partial> \
     --active-process-state <state> \
     [--verification-evidence "<path-or-identifier>" ...]
   ```

8. Review the returned repository-relative path, metadata, body, seal, and full
   Markdown. Then repeat with the identical body and capture flags, adding:

   ```text
   --captured-at "<preview data.captured_at>" \
   --allocation-token "<preview data.allocation_token>" \
   --create
   ```

   The token binds the reviewed path, source bytes, capture time, body, Git
   evidence, statuses, and snapshot seal. If any input or the collision state
   changes, stop and preview again.

9. Run immutable validation:

   ```text
   python3 <skill-dir>/scripts/document_session.py validate-handoff \
     --repo . --target <handoff-path>
   ```

10. Never edit, reseal, or overwrite the created handoff. Create another
    handoff when a later point-in-time snapshot or correction is needed. A
    changed or unavailable source may produce a portability warning without
    invalidating an otherwise intact snapshot.

## Finalize

1. Resolve with `--for-write`.
2. Validate the existing target before editing. Stop and report structural or
   unsafe-content errors rather than finalizing an invalid record.
3. Revalidate Git state, commands, configs, logs, metrics, processes, and
   artifacts relevant to the objective.
4. If a task-owned run is still active or the terminal state is unsupported,
   create a checkpoint instead. Do not alter the process.
5. Append a terminal checkpoint with `completion`, `failure`, or `aborted`.
6. Reconcile the summary, current state, observed facts, decisions, artifacts,
   anomalies, uncertainty, next actions, activity profiles, and embedded
   `Knowledge Handoff` section.
7. Set:

   - terminal `work_status`;
   - evidence-supported `verification_status`;
   - `documentation_status: final`;
   - `finalized_at`;
   - `commit_current` and `commit_final` when Git evidence is available;
   - checkpoint counters.

8. Run validation. A final record with errors is not complete.
9. Treat the finalized file as immutable. Put later work in a new file and link
   it through `related_worklogs`.

When Git evidence is unavailable, keep the commit fields null and record that
boundary. Validation permits this with a warning so non-Git repositories remain
supported. During finalization, record the current HEAD. Later validation
requires that recorded value to remain resolvable as a commit, not to equal a
newer current HEAD.

## Validate

Run:

```text
python3 <skill-dir>/scripts/document_session.py validate \
  --repo . --target <worklog-path>
```

For a standalone snapshot, run:

```text
python3 <skill-dir>/scripts/document_session.py validate-handoff \
  --repo . --target <handoff-path>
```

Interpret helper exit codes:

```text
0  command completed; inspect `data.valid` for validate
2  command-line usage error
3  unsafe or invalid input/precondition
4  target not found
5  ambiguous target
6  finalized target rejected for writing
7  structural validation failed
8  secret-like content detected
```

The helper emits JSON. It performs deterministic inspection, selection,
allocation, snapshot sealing, and validation only. It does not summarize
research content, choose
the final activity, generate a scientific verdict, or rewrite checkpoints.

## Evidence Language

Use explicit labels:

```text
[observed] Directly supported by a command, file, log, metric, process, or artifact.
[interpretation] Reasoned from stated observations; not independently verified.
[decision] An explicit design or experiment choice and its rationale.
[unknown] Evidence is absent, incomplete, conflicting, or unsafe to disclose.
```

Record commands with exit status and relevant output location when available.
Record suggested commands separately as `Suggested, Not Executed`.

## Completion Response

Return:

- the selected or created repository-relative worklog or handoff path;
- command performed;
- resulting work, documentation, and verification statuses;
- snapshot seal for `handoff`;
- validation result and warnings;
- any ambiguity, missing evidence, or evidence boundary.

Do not claim the documented research task itself succeeded unless the worklog
contains current evidence for that claim.
