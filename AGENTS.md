# AGENTS.md

This repository stores custom Codex skills for reuse across multiple environments.

## Repository Purpose

Maintain portable skills that can be installed into:

- Docker research Codex: `/root/.codex/skills/`
- Local LLM Wiki Codex: `/Users/{user_name}/.codex/skills/`
- This shared repository as a source of truth for installable skills

Research skills support implementations, experiments, reproductions, baselines, and related engineering workflows. LLM Wiki skills support second-brain workflows, knowledge capture, documentation, synthesis, and personal wiki maintenance.

## Public Repository Privacy

This is a public repository. Do not add personal, private, or sensitive information to tracked files.

- Do not commit real names, private usernames, email addresses, phone numbers, addresses, account IDs, API keys, tokens, credentials, private URLs, internal hostnames, or unpublished research data.
- Do not include private LLM Wiki notes, second-brain content, conversation exports, personal journal entries, or copied private documents.
- Use placeholders in examples, such as `{user_name}`, `{project_name}`, `{repo_url}`, `{api_key}`, and `{private_path}`.
- Keep environment-specific paths generic unless the path is a documented Codex convention, such as `/root/.codex/skills/` or `/Users/{user_name}/.codex/skills/`.
- Before committing, review new and changed files for secrets, identifying details, and private knowledge-base content.
- If sensitive information is accidentally committed, stop and ask the user how they want to rotate secrets and rewrite history.

## Working Rules

- Do not assume a skill is only for one environment unless its `SKILL.md` says so.
- Keep skills portable across Docker and local macOS-style paths when practical.
- Do not hard-code user-specific paths except as documented examples.
- Preserve user changes in the worktree. Do not restore, delete, or rewrite unrelated files without explicit instruction.
- Use ASCII unless an existing file or skill content requires otherwise.
- Keep documentation concise and operational.

## Skill Structure

Each skill should be placed in a directory named for the workflow:

```text
skill-name/
  SKILL.md
```

Optional support directories:

```text
skill-name/references/
skill-name/scripts/
skill-name/assets/
```

Use these only when they materially improve maintainability or reuse.

## SKILL.md Expectations

Each `SKILL.md` should include:

- What the skill is for
- When to use it
- Required inputs or assumptions
- Step-by-step workflow instructions
- Environment-specific notes, if behavior differs between Docker research and local LLM Wiki usage
- Any scripts, references, or assets the agent should read or use

Prefer explicit instructions over broad intent. A skill should be usable by Codex without needing repository-specific context beyond the skill directory.

## Development Workflow

- Inspect existing skill patterns before adding a new skill.
- Keep edits scoped to the requested skill or repository documentation.
- Use `rg` or `rg --files` for repository searches.
- Validate Markdown changes by reading the resulting file when possible.
- For executable helper scripts, add the smallest practical verification command.

## Commit Messages

Follow [COMMIT_CONVENTION.md](COMMIT_CONVENTION.md):

```text
[type] short description
```

Use `[docs]` for documentation-only changes, `[feat]` for new skills, `[fix]` for corrections, `[refactor]` for structural improvements, `[test]` for tests, and `[chore]` for maintenance.
