---
name: document-session
description: Use only when the user explicitly invokes $document-session to start, checkpoint, resume, inspect, or finalize a portable evidence-grounded research coding or experiment worklog.
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
$document-session finalize
```

Optional user-facing arguments:

```text
--activity auto|analysis|implementation|refactoring|data_preparation|training|inference|evaluation|ablation|debugging|mixed
--target <existing-worklog-path>
--method <method-name>
--title <worklog-title>
--event launch|progress|compact|resume|completion|failure|aborted
--new
```

Treat arguments as instructions to this workflow. The bundled helper has the
lower-level `inspect`, `locate`, `allocate`, and `validate` subcommands.

## Non-Negotiable Boundaries

- Write only the selected worklog Markdown file.
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

If documenting a task requires a forbidden action, record the missing evidence
or blocker instead.

## Load References

Always read:

- `references/worklog-schema.md`
- `references/lifecycle-and-selection.md`

Read `references/activity-profiles.md` before adding or updating activity
sections. Read `references/knowledge-handoff.md` before a checkpoint or
finalization. Use `assets/worklog-template.md` only through the allocator when
starting a new file.

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
   anomalies, uncertainty, next actions, activity profiles, and handoff.
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
allocation, and validation only. It does not summarize research content, choose
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

- the selected or created repository-relative worklog path;
- command performed;
- resulting work, documentation, and verification statuses;
- validation result and warnings;
- any ambiguity, missing evidence, or evidence boundary.

Do not claim the documented research task itself succeeded unless the worklog
contains current evidence for that claim.
