# Lifecycle and Selection

## Contents

- [State Machine](#state-machine)
- [Selection Algorithm](#selection-algorithm)
- [Command Contract](#command-contract)
- [Checkpoint Format](#checkpoint-format)

## State Machine

```text
absent
  -> in_progress
  -> checkpointed
  -> in_progress/resumed
  -> final
```

Allowed transitions:

- `start`: `absent -> in_progress`
- `checkpoint`: `in_progress|checkpointed -> checkpointed`
- `resume`: read-only inspection of `in_progress|checkpointed`; a later resume
  checkpoint may set `checkpointed -> in_progress`
- `finalize`: `in_progress|checkpointed -> final` after revalidation
- `status`: no transition
- `handoff`: no source transition; create a new immutable snapshot from
  `in_progress|checkpointed|final`

Forbidden transitions:

- `final -> in_progress|checkpointed`
- any write to a finalized file
- `absent -> final`
- changing `created_at`, `worklog_id`, or filename during an update
- treating compact or a new Codex session as a reason to allocate a new file

## Selection Algorithm

Resolve a target in this order:

1. Validate and use explicit `--target`.
2. If a future repository config is supported, validate its active target.
3. Use an active worklog only when exactly one candidate clearly matches the
   current task.
4. Use the sole active worklog when exactly one exists in the repository.
5. Otherwise report candidates and stop before writing.

The MVP has no repository config, so step 2 is intentionally unavailable.
Automatic discovery considers only canonical Markdown files directly inside
`docs/`. An explicit target must satisfy the same location, filename,
frontmatter identity, and initial timestamp contract before selection.

For `handoff`, keep the same selection order with these constraints:

- without `--target`, consider active worklogs only and require exactly one;
- never fall back to a finalized worklog;
- with `--target`, allow a valid active or finalized worklog;
- never pass `--for-write`, because the source is not edited.

Use `task_key` to narrow candidates only when it was derived from the same
objective, method, scope, and repository identity. Then check:

- research objective;
- method or implementation target;
- experiment plan;
- dataset and split;
- evaluation protocol;
- hypothesis or expected evidence;
- whether the candidate already has an independent final conclusion.

Do not choose among multiple candidates based on recency alone.

Reuse one file for:

- before and after compact;
- the same task in a new Codex session;
- follow-up fixes for one implementation objective;
- reruns or added seeds in one experiment batch;
- cause analysis and repair of one debugging incident;
- smoke inference that belongs to one training task.

Allocate a new file for:

- an independent implementation objective;
- a separate experiment batch;
- a new evaluation study;
- a different hypothesis;
- an independent debugging incident;
- follow-up work after finalization.

Link a related finalized record through `related_worklogs`; never reopen it.

## Command Contract

| Command | Source worklog effect | Output |
| --- | --- | --- |
| `checkpoint` | Mutate one selected active worklog. | Updated mutable worklog. |
| `handoff` | Read one active or finalized worklog without changing it. | New immutable Markdown snapshot. |
| `finalize` | Add a terminal checkpoint and lock one active worklog. | Finalized immutable worklog. |

### `start`

Inputs:

- optional `--activity`;
- optional `--target`;
- `--method`, `--title`, and a concrete objective when allocating;
- optional `--new` for a deliberately independent task.

Preconditions:

- the repository root is known;
- no matching active worklog exists, unless `--new` explicitly establishes an
  independent objective;
- title and objective are non-empty.

Effects:

- inspect repository evidence;
- create exactly one worklog with the deterministic allocator;
- never write source, config, artifact, or process state.

Failure:

- stop on ambiguous active worklogs;
- never overwrite a collision;
- do not prefill expected results.

### `checkpoint`

Inputs:

- selected target;
- optional `--activity`;
- `--event launch|progress|compact|resume|completion|failure|aborted`.

Preconditions:

- target is active and belongs to the task;
- evidence to be recorded was re-inspected.

Effects:

- replace `Current State` with the latest state;
- append one timestamped checkpoint;
- update current commit, counts, status, and handoff;
- write only the selected worklog.

Failure:

- stop on ambiguity, finalized target, unsafe content, or unsupported claims;
- do not modify previous checkpoints.

### `resume`

Inputs:

- optional explicit target and task identity evidence.

Preconditions:

- an active target resolves unambiguously.

Effects:

- read the worklog, latest checkpoint, Git state, relevant process state,
  configs, logs, metrics, and artifacts;
- return current objective, state differences, blocker, uncertainty, and next
  action;
- perform no write by default.

Failure:

- report ambiguity or missing evidence;
- never reconstruct missing facts from session memory.

If work continues, create a later `resume` checkpoint. Increment
`session_count` only when that checkpoint documents a newly resumed Codex
session.

### `status`

Inputs:

- optional explicit target or task key.

Effects:

- report candidate paths;
- report objective, activity, work status, blocker, next action;
- report structural completeness and missing evidence;
- perform no write.

Failure:

- list ambiguous candidates and stop;
- do not select a likely candidate.

### `handoff`

Inputs:

- optional `--target <worklog-path>`;
- no `--event`, `--label`, method, or title override.

Preconditions:

- explicit target is a valid active or finalized worklog; or
- automatic selection resolves exactly one active worklog;
- source and relevant current evidence were inspected read-only;
- body matches the required handoff schema and contains no secret-like value.

Effects:

- keep the source worklog byte-for-byte unchanged;
- derive capture metadata from the source and current repository evidence;
- preview one collision-safe `docs/handoffs/` path;
- publish exactly the reviewed Markdown with an immutable snapshot seal;
- validate the new handoff without resealing it;
- permit later handoffs from the same source without changing earlier ones.

Failure:

- stop on ambiguous automatic selection;
- do not fall back to finalized worklogs without an explicit target;
- reject source, body, path, capture, Git, status, or collision drift after
  preview;
- reject a running process captured as completed or aborted;
- reject `verified` without explicit verification evidence;
- never overwrite or repair an existing handoff.

### `finalize`

Inputs:

- selected active target;
- optional `--event completion|failure|aborted`.

Preconditions:

- Git state and relevant commands, configs, logs, metrics, processes, and
  artifacts were revalidated;
- terminal work status is supported by evidence;
- no task-owned process still requires the worklog to remain active.

Effects:

- append a terminal checkpoint;
- update the summary, current state, evidence, uncertainty, and handoff;
- set `documentation_status: final`, `finalized_at`, and `commit_final`;
- validate, then treat the file as immutable.

If Git metadata is unavailable, keep `commit_final: null`, state the evidence
boundary, and retain the validator warning. Git availability is not a
finalization precondition.

Failure:

- checkpoint instead when work remains running or materially unresolved;
- never stop or restart a process to make finalization possible.

## Checkpoint Format

Replace `Current State` on each written checkpoint:

```markdown
## Current State

- Current objective:
- Current activity:
- Implementation status:
- Active experiment:
- Active process:
- Blocking issue:
- Unresolved uncertainty:
- Next action:
```

Append, never rewrite:

```markdown
### YYYY-MM-DDTHH:MM:SS+09:00 — event: concise label

#### Completed
#### Files Changed
#### Commands Executed
#### Experiment Updates
#### Observed Facts
#### Decisions
#### Failures and Anomalies
#### Artifacts
#### Context at Risk
#### Next Action
```

Add an amendment checkpoint when earlier content is wrong. Increment
`compact_count` only for an explicitly requested `compact` event.
Use `+09:00` for every checkpoint. Keep checkpoint timestamps ordered, make
`last_checkpoint_at` equal the latest one, and make `finalized_at` equal the
terminal checkpoint timestamp.
