# Skills-Codex

Personal Codex skills repository.

This repository stores custom Codex skills that can be reused across different Codex environments. Skills are organized by their primary usage so they can be installed selectively into a Docker-based research environment or a local LLM Wiki environment.

## Installing Skills

### Repo-level

Clone this repository anywhere on any device, then copy a specific skill into a workspace-local `.agents/skills/` directory:

```bash
mkdir -p .agents/skills
cp -R /path/to/Skills-Codex/research/<skill-name> .agents/skills/
cp -R /path/to/Skills-Codex/llm_wiki/<skill-name> .agents/skills/
```

Use the command for the usage bucket that contains the skill. The `.agents/` directory is local workspace state and is ignored by this repository.

To install all research skills into the current workspace:

```bash
mkdir -p .agents/skills
cp -R /path/to/Skills-Codex/research/* .agents/skills/
```

To install the vendored Graphify skill only:

```bash
mkdir -p .agents/skills
cp -R /path/to/Skills-Codex/research/graphify .agents/skills/
```

### Device-level

Install or sync individual skill directories into the target Codex skills directory for the environment you are using.

For Docker research:

```bash
cp -R research/<skill-name> /root/.codex/skills/
```

To install all research skills into Docker research:

```bash
cp -R research/* /root/.codex/skills/
```

For local LLM Wiki use:

```bash
cp -R llm_wiki/<skill-name> /Users/{user_name}/.codex/skills/
```

To install all research skills into local Codex:

```bash
cp -R research/* /Users/{user_name}/.codex/skills/
```

You can also keep this repository as the shared source of truth and install individual skills from either usage bucket wherever Codex is available.

### Graphify

`research/graphify` is vendored from the official Graphify Codex project installer output. The skill records the vendored Graphify version in `.graphify_version`, but the Graphify runtime package is still required or installed by the skill when it runs.

Copying `research/graphify` installs the Codex skill only. To enable Graphify runtime support for PDF extraction, install Graphify with its PDF extra in the Python environment that runs `graphify`:

```bash
python3 -m pip install "graphifyy[pdf]"
```

If `graphify` is installed in a specific Python environment, use that environment's Python instead:

```bash
$(dirname "$(which graphify)")/python -m pip install "graphifyy[pdf]"
```

For parallel extraction in Codex, enable multi-agent support in `~/.codex/config.toml`:

```toml
[features]
multi_agent = true
```

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

Skills are grouped by usage:

```text
research/
  skill-name/
    SKILL.md
    references/
    scripts/
    assets/

llm_wiki/
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

Current skills:

- `research/add-baseline`: find and verify baseline paper metadata and official links, then optionally update a baseline README and clone the official repository
- `research/graphify`: build and query persistent knowledge graphs for codebases, papers, documents, images, and research corpora
- `research/git-sync`: pull, commit, and push repository changes using the local commit convention
- `llm_wiki/paper-ingest`: ingest Zotero papers into an LLM Wiki and compile durable wiki pages

## Skill Naming

Use short, descriptive, lowercase directory names with hyphens:

```text
paper-baseline-finder/
wiki-note-capture/
experiment-runner/
```

Prefer names that describe the task the skill performs rather than the tool it uses.

## Authoring Guidelines

- Keep each skill focused on one repeatable workflow.
- Place new skills under `research/` or `llm_wiki/` according to their primary usage.
- Put all required operating instructions in `SKILL.md`.
- Use references, scripts, and assets only when they make the skill easier to maintain or reuse.
- Avoid hard-coding environment-specific paths unless the path is part of the skill contract.
- When a skill supports both Docker and local use, document any environment differences clearly.
- Prefer portable commands and explicit assumptions.

## Commit Convention

Use the commit message format described in [COMMIT_CONVENTION.md](COMMIT_CONVENTION.md).
