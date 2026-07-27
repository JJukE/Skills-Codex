# Research Skills

Use these skills from the research repository where you want Codex to act.
See [Installing Skills](../README.md#installing-skills) before using them.

| Skill | Use it for |
| --- | --- |
| [`add-baseline`](add-baseline/SKILL.md) | Verify official paper links, then optionally update a baseline README and clone the official repository. |
| [`document-session`](document-session/SKILL.md) | Maintain a compact-safe research worklog and export immutable point-in-time handoffs. |
| [`git-sync`](git-sync/SKILL.md) | Pull, commit, and push requested changes using the repository's commit convention. |
| [`graphify`](graphify/SKILL.md) | Build and query a persistent knowledge graph for code, papers, documents, and other research artifacts. |

## Add Baseline

Invoke this prompt-driven skill with `$add-baseline` and state which mode you
want.

| Mode | What it does | Example |
| --- | --- | --- |
| Search only | Finds paper metadata and verifies official links without editing files or cloning a repository. | `Use $add-baseline to find and verify official links for paper.pdf. Search only.` |
| Add and clone | After you confirm the links, updates the baseline README and clones the official repository. | `Use $add-baseline to add paper.pdf to README.md and clone the official repository after I confirm the links.` |

## Document Session

Invoke this skill explicitly with `$document-session`. It grounds records in
repository, command, process, log, metric, and artifact evidence. It does not
assume or contact any external knowledge system.

| Command | What it does | Example |
| --- | --- | --- |
| `start` | Creates a new worklog or reuses the active worklog for the same research objective. | `$document-session start --title "Evaluate {method}" --activity evaluation` |
| `checkpoint` | Updates the mutable worklog state and appends an evidence-grounded checkpoint. Use it before compact or at meaningful progress boundaries. | `$document-session checkpoint --event compact` |
| `resume` | Reads an existing worklog and reports what changed, the blocker, and the next action without editing it. | `$document-session resume` |
| `status` | Reports the current worklog status, validation result, and missing evidence without editing it. | `$document-session status` |
| `handoff` | Creates a new immutable point-in-time snapshot without finalizing the active worklog. Use it for progress, day-close, failure, or other downstream transfer. | `$document-session handoff --event day-close` |
| `finalize` | Adds a supported terminal checkpoint, reconciles the worklog, and makes it immutable. | `$document-session finalize --event completion` |

A common multi-session workflow is:

```text
$document-session start --title "Train {method}" --activity training
$document-session checkpoint --event compact
$document-session resume
$document-session checkpoint --event progress
$document-session handoff --event day-close
```

The three persistence operations have different roles:

- `checkpoint` updates the active mutable worklog for compact-safe continuation;
- `handoff` creates a separate immutable snapshot while the task may still be running;
- `finalize` closes and locks the active worklog when a terminal state is supported by evidence.

A handoff must remain portable and consumer-neutral. It may expose generic
research entities, runs, findings, decisions, failures, artifacts, evidence
boundaries, and next actions, but it must not name or require a particular Wiki,
database, document processor, or ingest skill.

## Git Sync

Invoke this prompt-driven skill with `$git-sync` and name the changes that
belong in the commit.

| Command | What it does | Example |
| --- | --- | --- |
| `$git-sync` | Pulls safely, stages only the requested changes, commits with `COMMIT_CONVENTION.md`, and pushes without force. | `Use $git-sync to pull, commit, and push only research/README.md.` |

## Graphify

Invoke Graphify with `/graphify`. Build a graph before using `query`, `path`, or
`explain` when the target does not already contain `graphify-out/`.

| Command | What it does | Example |
| --- | --- | --- |
| Help | Prints the complete Graphify usage reference without running the pipeline. | `/graphify --help` |
| Build | Builds a knowledge graph for the selected folder; `.` means the current directory. | `/graphify .` |
| Update | Re-extracts new or changed files and refreshes an existing graph. | `/graphify . --update` |
| Add | Fetches a URL into `./raw` and updates the graph. | `/graphify add https://arxiv.org/abs/1706.03762` |
| Query | Traverses the graph to answer a broad question. | `/graphify query "How does evaluation depend on preprocessing?"` |
| Path | Finds the shortest graph path between two concepts. | `/graphify path "DatasetLoader" "EvaluationMetric"` |
| Explain | Gives a plain-language explanation of one graph node. | `/graphify explain "EvaluationMetric"` |

See the full [`graphify` skill](graphify/SKILL.md) for deep extraction, export,
watch, MCP, Neo4j, and other advanced options.

## Important Notes

- `add-baseline` defaults to search-only until you confirm the links and request the README update or clone.
- `document-session` must be invoked explicitly. Its lifecycle commands are `start`, `checkpoint`, `resume`, `status`, `handoff`, and `finalize`.
- `document-session handoff` is allowed before finalization and creates a separate immutable snapshot; it must not modify or control active research processes.
- `git-sync` requires a configured remote, a current branch, and a repository-root `COMMIT_CONVENTION.md`.
- `graphify` requires the Graphify runtime; PDF support and multi-agent setup are documented in the [Graphify installation notes](../README.md#graphify).
