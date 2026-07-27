# Knowledge Handoff

Use `Knowledge Handoff` to make verified context portable to another researcher,
another Codex session, or an unspecified document processor. Do not assume or
name a destination.

## Durable Technical Findings

Record confirmed technical facts that can be reused. Cite repository-relative
source, config, log, metric, or artifact paths when possible. Label inferences.

## Reproducibility Constraints

Record required environment, data, checkpoint, version, platform, and hardware
conditions. Record unknowns that prevent exact reproduction.

## Research Decisions

Record explicit design or experiment decisions and their evidence-grounded
rationale. Do not rewrite plans as completed decisions.

## Experiment Evidence

Reference concrete run IDs, protocols, metrics, raw counts, and artifact paths.
State the unit of evidence and the conclusion boundary.

## Failure Patterns

Record repeatable or reusable failure patterns. Label a one-off anomaly as a
single occurrence. Separate symptom, workaround, hypothesis, and confirmed root
cause.

## Candidate Follow-up Topics

List possible future method, dataset, experiment, debugging, or analysis work.
Candidates are not commitments and are not observed results.

## Evidence Boundaries

State what this worklog cannot establish, including incomplete runs, missing
artifacts, protocol differences, selection bias, unverified code, and
unaggregated seeds.

## Suggested Stable Identifiers

Suggest generic identifiers only when supported:

- project name;
- method name;
- dataset name;
- run ID;
- result label;
- failure label.

Do not invent an external path, entity ID, page, collection, or routing target.

## Machine-Readable Metadata

Do not include a nested machine-readable block in the MVP. Frontmatter already
provides stable scalar and list fields. Keeping detailed findings in Markdown
avoids duplicated sources of truth and remains independent of any consumer.
