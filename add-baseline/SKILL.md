---
name: add-baseline
description: Find and verify baseline paper metadata and official links from local PDF files, then optionally update README.md and clone the official GitHub repository. Use when the user asks to add baseline info for a paper PDF, confirm paper links, search only, or run the add-and-clone workflow for research baselines.
---

# Add Baseline

## Overview

Use this skill to turn a local paper PDF into a verified baseline entry. The workflow has two modes:

- **Search-only**: extract paper metadata, verify official links, and report them for confirmation; do not edit files or clone repos.
- **Add-and-clone**: after the user confirms the links, update `README.md` following the existing baseline format and clone the official GitHub repository into the requested local directory.

Default to search-only until the user explicitly confirms the links and asks to add/clone, or replies affirmatively to a pending confirmation.

## Workflow

1. Inspect the existing `README.md` baseline format before proposing changes. Preserve local ordering and wording conventions.
2. Extract metadata and embedded URLs from the PDF. Prefer PDF metadata and embedded annotations first; use `strings <pdf> | rg -i "https?://|github|hugging|hf.co|arxiv|<method>"` when no PDF text extractor is available.
3. Verify all candidate links with current web sources before reporting them. Use primary sources whenever possible: arXiv, the official project page, the official GitHub repo, and official Hugging Face pages.
4. Report the confirmed info to the user before editing or cloning. Include:
   - Method/GitHub heading link
   - Title
   - ArXiv link
   - Project Page link, or state that none was found
   - GitHub link
   - Hugging Face link(s), or state that none was found
   - Planned Status line
   - Brief source basis
5. Stop after reporting if the mode is search-only or the user has not yet confirmed.
6. In add-and-clone mode, after confirmation, insert one baseline block in `README.md` using the local style:

```markdown
### [MethodName](https://github.com/owner/repo) (Venue or Preprint)
- **Title**: Paper title
- **Links**: [ArXiv](...) | [Project Page](...) | [GitHub](...) | [Hugging Face](...)
- **Status**: Current status.
```

Omit links that do not exist, except explicitly note missing links in the confirmation message before editing. If multiple Hugging Face resources exist, label them clearly, e.g. `Hugging Face Model` and `Hugging Face Dataset`.

7. Clone the official GitHub repository into the user-requested path, usually `./<MethodName>` matching the PDF filename. If the destination exists, inspect it and ask before overwriting or reusing it.
8. Verify the README section, README diff, cloned directory contents, cloned repo status, and parent repo status. Report concise results.

## Link Verification Rules

- Treat PDF-embedded links as candidates, not final proof. Confirm them against current primary sources.
- Prefer canonical non-versioned arXiv URLs in README, e.g. `https://arxiv.org/abs/2501.08333`, unless the existing README uses versioned links for that project.
- Use a separate project page only when an official page exists. Do not invent a project page from GitHub or arXiv.
- Use the official GitHub repository linked by the paper/project page/arXiv when available. If multiple official repos exist, explain the distinction and ask which to clone.
- Include Hugging Face only for official project-related model, dataset, or Space pages. If none are found, say so during confirmation and omit it from README.

## Mode Handling

- Search-only triggers: `search only`, `just find`, `confirm links`, `do not edit`, `do not clone`, or any request that asks for information without adding.
- Add-and-clone triggers: `add`, `update README`, `clone`, `after adding`, or an explicit confirmation such as `OK` after the skill has already reported links and the user requested adding/cloning.
- If the user asks both to confirm first and then add/clone, perform search-only first, wait for confirmation, then continue with add-and-clone.

## Status Wording

Keep status factual and based on official sources. Examples:

- `Official repository available; code release pending.`
- `Official repository available; code and dataset release pending.`
- `Official repository available; model and dataset released on Hugging Face.`
- `Repository cloned, environment setup not started.`

Prefer not to claim implementation progress unless the local repo shows that work has happened.
