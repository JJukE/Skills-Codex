# Paper Ingest Templates

Use these templates as stable output shapes. Adapt names and sections only when the source genuinely requires it.

## Raw Zotero Paper Seed Note

```markdown
---
source_type: zotero_paper
title: "TITLE"
authors:
  - AUTHOR
year: YEAR
venue: ""
arxiv: ""
url: ""
collections:
  - ""
tags:
  - raw
  - zotero
  - paper
reading_status: not-read
summary_status: completed
created: YYYY-MM-DD
---

# TITLE

## Zotero Metadata

- **Title:** TITLE
- **Authors:** AUTHOR LIST
- **Year:** YEAR
- **Venue:** To be filled
- **arXiv:** To be filled
- **Project page:** To be filled
- **Collection path:** To be filled

## PDF Source

- **External PDF path:** `PDF_PATH`
- **Important rule:** This raw seed note records the source path only. Do not move, copy, delete, or rewrite the original Zotero PDF.

## Source Availability

- The paper PDF is available locally through the Zotero-managed folder above.
- Code/data/checkpoint release status: To be filled.

## AI-Generated Initial Summary

### Feynman Explanation

Explain the paper as if teaching the core idea from first principles.

### Deep Technical Explanation

#### Problem

#### Core Idea

#### Method

#### Data / Sources

#### Experiments / Findings

#### Limitations

### Researcher Interpretation

State interpretations separately from paper facts. Give the basis for each interpretation.

## Required Questions

### 1. What problem does it solve?

### 2. How does it solve the problem?

### 3. What are the key findings?

### 4. Why is this important?

## My Reading Notes

To be filled after personal reading.

## Later Wiki Update Targets

- `wiki/papers/TITLE.md`
- `wiki/methods/METHOD.md`
- `wiki/concepts/CONCEPT.md`
- `wiki/tasks/TASK.md`
- `wiki/experiments/METHOD Reproduction Plan.md`

## Open Questions

- What should be checked during personal reading?
```

## GitHub Source Summary

```markdown
# REPO_OR_METHOD Official Code

## Source

- Raw GitHub clipping: `raw/github/...`
- Related raw paper seed: `raw/papers/...`
- Repository: URL
- Source type: GitHub repository
- Captured: YYYY-MM-DD
- Ingested: YYYY-MM-DD

## Personal Context

I clipped this because ...

This connects to my current work because ...

I want to use it for ...

## Reading Notes Status

State whether `My Reading Notes` contains user-written notes.

## Key Claims

## Release Status

## Entities Mentioned

### People

### Organizations

### Tools And Frameworks

### Research Items

## Concepts Covered

## Relevance To My Research

## Possible Ideation Directions

## Open Questions
```

## Method Page

```markdown
# METHOD

## Summary

## Core Idea

## Current Code Status

## Why It Is A Baseline

## Relation To Other Baselines

## Related Pages

## Open Questions
```

## Reproduction Plan

```markdown
# METHOD Reproduction Plan

## Summary

## Current Status

## Proposed Reproduction Stages

1. Record repository commit, environment, hardware, and dependency versions.
2. Run the simplest released inference path.
3. Run quantitative evaluation if supported.
4. Attempt minimal training only after inference is stable.
5. Record failure cases and reproduction outputs.

## Expected Outputs

- Environment setup note
- Minimal inference reproduction note
- Checkpoint/data inventory
- Baseline result note
- Failure log
- Ideation note

## Initial Risks

## Open Questions
```

## Index Entry

```markdown
- [[path/Page Name]]: One-line summary. Source count: N. Last updated: YYYY-MM-DD.
```

## Log Entry

```markdown
## [YYYY-MM-DD] ingest | TITLE

- Summary:
- Pages changed:
- Sources used:
- Open questions:
```

