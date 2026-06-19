---
name: paper-ingest
description: "Use this skill when ingesting a research paper into an LLM Wiki from Zotero PDFs, optionally linking an official GitHub clipping, creating an English raw seed note, interviewing the user for research context, and compiling durable wiki pages."
---

# Paper Ingest

## Purpose

Use this skill to turn a Zotero-stored research paper and optional official code clipping into reusable English research knowledge in an LLM Wiki.

This skill is for:

- creating a raw Zotero paper seed note from a local PDF
- connecting a paper seed note to an official GitHub clipping
- summarizing source claims, entities, and concepts
- asking the user for personal research context before wiki compilation
- updating `wiki/`, `wiki/index.md`, and `wiki/log.md`

## Core Rules

- Durable notes must be written in English.
- Conversation may be in Korean, but raw seed notes and wiki pages should be English unless the user explicitly requests otherwise.
- Never modify, move, copy, delete, or rewrite external Zotero PDFs.
- Do not modify existing `raw/` clipping files.
- Creating a new `raw/papers/` seed note is allowed only when the user explicitly asks for a raw seed note or paper ingest.
- Keep paper facts, AI interpretation, and the user's later reading notes clearly separated.
- If `My Reading Notes` only says `To be filled after personal reading.`, treat it as empty.
- If matching a GitHub clipping is uncertain, ask the user to confirm before wiki compilation.

## Configured Paths

Vault root is usually the current working directory:

```text
{vault_root}
```

Example Zotero PDF root on macOS:

```text
/Users/{user_name}/Library/Mobile Documents/iCloud~QReader~MarginStudy~easy/Documents/Zotero
```

Shell-escaped form:

```text
/Users/{user_name}/Library/Mobile\ Documents/iCloud\~QReader\~MarginStudy\~easy/Documents/Zotero
```

This path is the machine-specific `zotero_pdf_root_path`. When registering or installing this skill on a new machine, ask the user for `zotero_pdf_root_path` and update this section plus `scripts/find_zotero_pdf.py` before using Zotero PDF discovery.

Raw seed notes:

```text
raw/papers/
```

GitHub clippings:

```text
raw/github/
```

## Workflow

### 1. Discover the paper

Use Zotero MCP or `zotero-cli` if available. If not, use the explicit PDF path from the user or search under `zotero_pdf_root_path`. The helper script defaults to this configured root, so pass `--root` only when overriding it for a specific request.

Helpful scripts:

```bash
python <paper-ingest-skill>/scripts/find_zotero_pdf.py --title "Paper Title"
python <paper-ingest-skill>/scripts/extract_pdf_text.py "/path/to/paper.pdf" --pages 20
```

If no PDF is found, create only metadata-level notes and mark the summary status as `pending_full_text`.

### 2. Create or update the raw seed note

Use the raw seed template in `references/templates.md`.

Required sections:

- Zotero Metadata
- PDF Source
- Source Availability
- AI-Generated Initial Summary
- Required Questions
- My Reading Notes
- Later Wiki Update Targets
- Open Questions

The AI-generated initial summary must be based on the full paper PDF when available, not only metadata or abstract.

For a skeleton preview:

```bash
python <paper-ingest-skill>/scripts/make_seed_note.py --title "Paper Title" --year 2025 --pdf "/path/to/paper.pdf" --dry-run
```

### 3. Connect optional GitHub clipping

Search `raw/github/` for candidate official code clippings:

```bash
python <paper-ingest-skill>/scripts/find_github_clipping.py --title "Paper Title" --authors "Author One, Author Two"
```

Connect automatically only when there is one clear match. If multiple candidates are plausible, ask the user.

### 4. Summarize the source before wiki edits

Before updating `wiki/`, present a concise source summary:

- Key claims
- Entities mentioned: people, tools, organizations, datasets, methods, researches
- Concepts covered

Then ask the user:

1. Why did you capture this?
2. How does this connect to your current work?
3. What do you want to try doing with this?
4. Optional: Which name should be used for the model/method/dataset when querying the wiki later? Suggest a canonical query name first, and if the user does not answer this question, use the suggested name.

Do not compile into `wiki/` until the user answers, unless the user has already provided equivalent answers in the current conversation.

### 5. Compile into the wiki

After receiving the user's answers, create or update durable wiki pages.

Typical targets:

- `wiki/syntheses/<Paper or Repo> Official Code.md`
- `wiki/papers/<Paper Title>.md`
- `wiki/methods/<Method Name>.md`
- `wiki/concepts/<Concept>.md`
- `wiki/tasks/<Task>.md`
- `wiki/datasets/<Dataset>.md`
- `wiki/experiments/<Method> Reproduction Plan.md`
- `wiki/literature-maps/<Topic>.md` when useful

Always update:

- `wiki/index.md`
- `wiki/log.md`

Prefer Obsidian links such as `[[methods/InterMimic]]`.

## Output Standards

Use the templates in `references/templates.md` for stable structure. Keep pages concise enough to stay useful, but include enough technical detail to recover the method, assumptions, limitations, and reproduction status later.

When source facts are uncertain, write placeholders or open questions instead of inventing details.
