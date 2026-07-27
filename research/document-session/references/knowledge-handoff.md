# Knowledge Handoff

## Contents

- [Point-in-Time Snapshot](#point-in-time-snapshot)
- [Evidence Classes](#evidence-classes)
- [Activity-Aware Interpretation](#activity-aware-interpretation)
- [Portable Content](#portable-content)
- [Embedded Worklog Section](#embedded-worklog-section)
- [Immutable Publication](#immutable-publication)

Use the embedded `Knowledge Handoff` worklog section for durable context that
changes with checkpoints. Use the `handoff` command when a separate immutable
point-in-time snapshot is required. Both forms remain portable and
consumer-neutral.

## Point-in-Time Snapshot

A standalone handoff records what the available evidence established at one
capture timestamp. It may be created from an active, checkpointed, or finalized
worklog. It never changes the source and it never turns an active run into a
terminal result.

Include these sections in order:

1. `Current Scope and State`
2. `Implementation Changes`
3. `Experiment and Run Evidence`
4. `Observed Results`
5. `Decisions`
6. `Failures and Anomalies`
7. `Artifacts`
8. `Reproducibility Constraints`
9. `Uncertainty and Evidence Boundaries`
10. `Next Actions`
11. `Coverage Limitations`

Keep every section non-empty. When evidence is unavailable, write a precise
`[unknown]` statement instead of filling the gap from memory.

## Evidence Classes

Use these labels:

- `[observed]`: directly supported by inspected repository, Git, command,
  process, config, log, metric, checkpoint, or artifact evidence;
- `[interpretation]`: a bounded explanation derived from named observations;
- `[decision]`: an explicit design or experiment choice and rationale;
- `[unknown]`: absent, incomplete, conflicting, or unsafe-to-record evidence.

Keep plans and proposed next actions out of observed results.

## Activity-Aware Interpretation

For implementation, refactoring, or debugging, distinguish changed code,
inspected diff, executed verification, workaround, hypothesis, and confirmed
root cause.

For training, inference, evaluation, or ablation, record process state, run
identifier, config, checkpoint, metric source, protocol, seed, and aggregation
unit when observed. Apply these boundaries:

- a running process has progress evidence, not a completed result;
- selected inference samples are qualitative and selected;
- one run or one seed is one evidence unit, not an aggregate conclusion;
- a metric without its protocol, split, or source retains that limitation;
- a reported command result without inspected command, status, or output is not
  verified.

For mixed activity, preserve each material activity in the body instead of
collapsing debugging, implementation, and evaluation into one result claim.

## Portable Content

Record repository-relative paths and stable identifiers when available. Include
the source worklog ID and path, current repository, branch, commit, capture
timestamp, activity, statuses, process state, verification evidence, and
coverage in frontmatter.

In the body, record:

- current scope and state;
- implementation changes;
- experiment and run evidence;
- observed results;
- decisions;
- failures and anomalies;
- artifacts;
- reproducibility constraints;
- uncertainties and evidence boundaries;
- proposed next actions;
- evidence surfaces that were not inspected.

Do not invent a destination, routing target, or identifier. Do not copy secret
or credential values. Record only that a value was redacted and where safe
evidence can be re-inspected.

## Embedded Worklog Section

Keep the mutable worklog section concise:

- durable technical findings;
- reproducibility constraints;
- research decisions;
- experiment evidence;
- failure patterns;
- candidate follow-up topics;
- evidence boundaries;
- stable identifiers supported by evidence.

Checkpoint may update this embedded section. Finalize reconciles it before
locking the worklog. Handoff reads it as one evidence source but creates a
separate file.

## Immutable Publication

Preview the complete snapshot before creation. The helper binds the source
bytes, capture metadata, path, body, and seal to the allocation token. After
creation, validate the seal and never edit or reseal the file. Create another
handoff for a later state or correction. A missing or later-changed source is a
coverage warning; it does not change the captured bytes or conclusions.
