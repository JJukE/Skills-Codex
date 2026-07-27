# Research Skills

Use these skills from the research repository where you want Codex to act.
See [Installing Skills](../README.md#installing-skills) before using them.

| Skill | Use it for | Invoke it |
| --- | --- | --- |
| [`add-baseline`](add-baseline/SKILL.md) | Verify official paper links, then optionally update a baseline README and clone the official repository. | `Use $add-baseline to find official links for paper.pdf. Search only.` |
| [`document-session`](document-session/SKILL.md) | Maintain an evidence-grounded Markdown worklog for a research task. | `$document-session start --title "Evaluate {method}" --activity evaluation` |
| [`git-sync`](git-sync/SKILL.md) | Pull, commit, and push requested changes using the repository's commit convention. | `Use $git-sync to pull, commit, and push the requested changes.` |
| [`graphify`](graphify/SKILL.md) | Build and query a persistent knowledge graph for code, papers, documents, and other research artifacts. | `/graphify .` or `/graphify --help` |

## Important Notes

- `add-baseline` defaults to search-only until you confirm the links and request the README update or clone.
- `document-session` must be invoked explicitly. Its lifecycle commands are `start`, `checkpoint`, `resume`, `status`, and `finalize`; it writes only the selected worklog.
- `git-sync` requires a configured remote, a current branch, and a repository-root `COMMIT_CONVENTION.md`.
- `graphify` requires the Graphify runtime; PDF support and multi-agent setup are documented in the [Graphify installation notes](../README.md#graphify).
