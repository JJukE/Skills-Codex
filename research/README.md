# Research Skills

Use these skills from the research repository where you want Codex to act.
See [Installing Skills](../README.md#installing-skills) before using them.

| Skill | Use it for |
| --- | --- |
| [`add-baseline`](add-baseline/SKILL.md) | Verify official paper links, then optionally update a baseline README and clone the official repository. |
| [`document-session`](document-session/SKILL.md) | Maintain an evidence-grounded Markdown worklog for a research task. |
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

Invoke this skill explicitly with `$document-session`. It observes repository
evidence and writes only the selected Markdown worklog.

| Command | What it does | Example |
| --- | --- | --- |
| `start` | Creates a new worklog or reuses the active worklog for the same research objective. | `$document-session start --title "Evaluate {method}" --activity evaluation` |
| `checkpoint` | Refreshes the current state and appends an evidence-grounded checkpoint. | `$document-session checkpoint --event progress` |
| `resume` | Reads an existing worklog and reports what changed, the blocker, and the next action without editing it. | `$document-session resume` |
| `status` | Reports the current worklog status, validation result, and missing evidence without editing it. | `$document-session status` |
| `finalize` | Adds a supported terminal checkpoint, reconciles the summary, and makes the worklog immutable. | `$document-session finalize --event completion` |

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
- `document-session` must be invoked explicitly. Its lifecycle commands are `start`, `checkpoint`, `resume`, `status`, and `finalize`; it writes only the selected worklog.
- `git-sync` requires a configured remote, a current branch, and a repository-root `COMMIT_CONVENTION.md`.
- `graphify` requires the Graphify runtime; PDF support and multi-agent setup are documented in the [Graphify installation notes](../README.md#graphify).
