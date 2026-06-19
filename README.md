# Skills-Codex

Personal Codex skills repository.

This repository stores custom Codex skills that can be reused across different Codex environments. The same skills should be installable from this shared repository into either a Docker-based research environment or a local LLM Wiki environment.

## Usage Contexts

### Research Environment

Use this path inside the Docker container:

```text
/root/.codex/skills/
```

This environment is for research work such as implementations, experiments, reproductions, baselines, evaluation scripts, and engineering notes around model or paper exploration.

### LLM Wiki Environment

Use one of these locations on the local machine:

```text
/Users/{user_name}/.codex/skills/
```

or install/use skills directly from this shared repository.

This environment is for LLM Wiki work, including second-brain workflows, personal knowledge management, documentation, synthesis, and reusable knowledge-capture routines.

## Repository Layout

Each skill should live in its own directory:

```text
skill-name/
  SKILL.md
  references/
  scripts/
  assets/
```

Only `SKILL.md` is required. Add supporting folders only when the skill needs them:

- `references/`: supporting instructions, templates, examples, or domain notes
- `scripts/`: helper scripts used by the skill
- `assets/`: reusable files, images, examples, or other static resources

## Skill Naming

Use short, descriptive, lowercase directory names with hyphens:

```text
paper-baseline-finder/
wiki-note-capture/
experiment-runner/
```

Prefer names that describe the task the skill performs rather than the tool it uses.

## Installing Skills

Install or sync the skill directories into the target Codex skills directory for the environment you are using.

For Docker research:

```bash
cp -R skill-name /root/.codex/skills/
```

For local LLM Wiki use:

```bash
cp -R skill-name /Users/{user_name}/.codex/skills/
```

You can also keep this repository as the shared source of truth and install individual skills from it wherever Codex is available.

## Authoring Guidelines

- Keep each skill focused on one repeatable workflow.
- Put all required operating instructions in `SKILL.md`.
- Use references, scripts, and assets only when they make the skill easier to maintain or reuse.
- Avoid hard-coding environment-specific paths unless the path is part of the skill contract.
- When a skill supports both Docker and local use, document any environment differences clearly.
- Prefer portable commands and explicit assumptions.

## Commit Convention

Use the commit message format described in [COMMIT_CONVENTION.md](COMMIT_CONVENTION.md).
