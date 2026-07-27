# Activity Profiles

Use repository and runtime evidence to route the worklog. An explicit
`--activity` wins unless it clearly conflicts with the evidence; record the
conflict rather than silently changing the user's classification.

Choose the activity that best describes the evidence-producing objective as
`primary_activity`. Put all activities that materially occurred in
`activity_types`. Make the primary profile most detailed and add only useful
secondary profile sections.

## Analysis Record

Capture:

- analysis question;
- inspected modules and symbols;
- control flow and data flow;
- tensor shapes, units, or coordinate systems where relevant;
- confirmed findings;
- inferred findings, labeled as interpretation;
- conflicting evidence;
- implications and unknowns.

Do not turn a plausible reading of code into an observed runtime fact.

## Implementation Record

Capture:

- design goal and architecture decisions;
- changed repository-relative files and symbols;
- interfaces, inputs, outputs, shapes, and data flow;
- config changes and backward compatibility;
- tests and validation that actually ran;
- unverified behavior and technical debt.

Keep implementation completion separate from verification status.

## Refactoring Record

Capture:

- behavior-preservation goal;
- before and after structure;
- moved, renamed, and removed symbols;
- interface compatibility;
- removed duplication;
- test coverage and behavior-change risk.

Do not claim preserved behavior without validation evidence.

## Data Preparation Record

Capture:

- source dataset and version;
- input paths;
- filtering, mapping, and preprocessing;
- unit or coordinate conversion;
- split construction;
- observed statistics;
- validation performed;
- output version and paths;
- data-quality caveats.

Distinguish planned transformations from produced datasets.

## Training Record

Capture:

- run ID and exact command;
- config plus overrides;
- dataset and split;
- initialization checkpoint;
- seed;
- optimizer, learning rate, scheduler, losses, steps, and epochs;
- observed hardware and process state;
- progress;
- latest, best, and final checkpoints only when those labels are supported;
- observed metrics, anomalies, termination reason, and output directory.

A running process remains `work_status: running`. Inspection must not signal,
restart, reconfigure, or replace it.

## Inference Record

Capture:

- checkpoint;
- inputs and case-selection method;
- sampling, decoding, or simulator settings;
- seed and sample or episode count;
- output paths and runtime;
- qualitative successes, failures, invalid outputs, and repeated outputs;
- selection-bias boundary.

Hand-picked examples cannot establish a quantitative rate.

## Evaluation Record

Use this default evaluation unit unless the repository defines a stricter one:

```text
checkpoint x dataset/split x protocol x seed
```

Capture:

- checkpoint;
- dataset and split;
- sample or episode count;
- protocol and metric definition;
- metric implementation;
- filtering and aggregation;
- seed count and raw counts;
- baseline source, reference result, and current result;
- protocol differences;
- whether direct comparison is valid.

One completed unit cannot establish an aggregate across unfinished seeds or
protocols.

## Ablation Record

Capture:

- changed factor;
- controlled factors;
- baseline and variant run IDs;
- seed policy;
- comparison metric;
- observed delta;
- confounders;
- aggregation readiness.

Do not attribute causality while material factors are uncontrolled.

## Debugging Record

Capture:

- symptom and decisive error;
- minimal reproduction;
- expected versus actual behavior;
- hypotheses;
- diagnostics;
- attempted fixes and observation after each attempt;
- root cause, or explicitly unknown root cause;
- applied fix;
- regression test;
- workaround versus actual fix;
- resolution status.

A workaround that avoids the symptom is not proof of root cause or resolution.

## Mixed Workflows

Use `primary_activity: mixed` only when no single evidence-producing objective
dominates. Otherwise choose the dominant activity and list secondary activities.

Examples:

```yaml
primary_activity: "training"
activity_types: ["implementation", "training"]
```

```yaml
primary_activity: "evaluation"
activity_types: ["implementation", "debugging", "evaluation"]
```
