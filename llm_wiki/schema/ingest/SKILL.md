
---
name: Ingest
description: >
 прочитать указанный материал llm_wiki/raw/ , создать резюме в llm_wiki/resume/ и каскадно обновить связанные 
 concept-страницы  в llm_wiki/concepts, index.md и log.md.

---

# [[LLM Wiki]] — Ingest Skill

## Purpose

This skill ingests source material from `llm_wiki/raw/` into the derived LLM knowledge base.

The ingest process transforms immutable source material into:

- source-specific summaries in `wiki/resume/`;
- accumulated knowledge in `wiki/concepts/`;
- navigation updates in `wiki/index.md`;
- an append-only activity record in `wiki/log.md`.

Knowledge flow:

```text
raw → resume → concepts
             ├→ index
             └→ log
```

---

# 1. Source Layer

## Raw is immutable

`llm_wiki/raw/` is the source-of-truth layer.

The agent MUST NOT:

- modify files in `raw/`;
- rename files in `raw/`;
- move files in `raw/`;
- delete files in `raw/`;
- generate new derived content inside `raw/`.

The agent may only read source material from this directory.

If a source contains incorrect, outdated, or contradictory information, the original source remains unchanged.

---

# 2. Ingest Workflow

When instructed to ingest a source, perform the following steps.

## Step 1 — Identify the source

Determine the exact source file or files to process.

Process only the requested source unless explicitly instructed otherwise.

Do not infer that all files in `raw/` should be processed.

If the requested source cannot be identified unambiguously, ask for clarification.

---

## Step 2 — Read the source

Read and understand the source before modifying the derived knowledge layer.

Do not create knowledge based only on:

- file names;
- metadata;
- isolated fragments;
- assumptions about the source.

For large materials, process the source systematically while preserving its overall context.

---

# 3. Resume Layer

For every ingested source, create or update a corresponding document in:

```
llm_wiki/wiki/resume/
```

A resume represents knowledge extracted from one specific source.

Its purpose is to answer:

> What useful information does this source contribute to the project?

The resume MUST:

- be substantially shorter than the source;
- preserve important facts and technical details;
- preserve architectural decisions;
- preserve important definitions and relationships;
- distinguish source facts from interpretation where necessary;
- avoid unnecessary repetition;
- link to relevant concept pages;
- preserve a link to the original source.

Recommended structure:

```
# <Source Title>

## Summary

Brief description of the source and its main contribution.

## Key Points

- ...
- ...
- ...

## Important Details

### <Topic>

...

### <Topic>

...

## Related Concepts

- [[concepts/<concept>]]
- [[concepts/<concept>]]

## Source

- [[raw/<source>]]
```

The structure may be adapted when required by the source.

Do not mechanically copy the original material.

---

# 4. Concept Extraction

While processing a source, identify concepts that are useful for long-term project knowledge.

A concept may represent:

- architecture;
- technology;
- workflow;
- principle;
- domain entity;
- methodology;
- recurring design pattern;
- important project idea.

Do not create concept pages for every term appearing in a source.

Create or update a concept only when accumulating knowledge about it across multiple sources is useful.

Before creating a new concept, check whether an equivalent or closely related concept already exists.

Avoid duplicate concepts caused by:

- different spelling;
- singular/plural forms;
- abbreviations;
- slightly different names.

---

# 5. Concept Layer

Concept pages are stored in:

```
llm_wiki/wiki/concepts/
```

A concept page represents accumulated knowledge from multiple sources.

It MUST NOT become a copy of an individual source resume.

When updating a concept:

1. Read the existing concept page.
2. Compare the new source with existing knowledge.
3. Add genuinely new information.
4. Merge duplicated information.
5. Preserve useful existing knowledge.
6. Maintain links to related concepts.
7. Add the relevant resume to the source list.

Recommended structure:

```
# <Concept Name>

## Definition

What this concept represents in the context of the project.

## Knowledge

Accumulated knowledge about the concept.

## Architecture / Usage

Project-specific implementation, usage, or implications.

## Related Concepts

- [[concepts/<related-concept>]]

## Sources

- [[resume/<source-a>]]
- [[resume/<source-b>]]
```

The structure may evolve as the concept develops.

Do not rewrite an entire concept page unless restructuring is necessary.

Prefer incremental accumulation of knowledge.

---

# 6. Provenance

Derived knowledge must remain traceable.

Concept pages should reference the resumes from which their knowledge originates.

Example:

```
## Sources

- [[resume/karpathy-llm-wiki]]
- [[resume/project-memory]]
```

The resume links back to the corresponding source in `raw/`.

Therefore the traceability chain is:

```
Concept
   ↓
Resume
   ↓
Raw Source
```

Do not invent sources or provenance.

---

# 7. Contradictions

If new information contradicts existing knowledge:

1. Do not silently overwrite existing information.
2. Check whether the contradiction is real.
3. Preserve provenance for both positions.
4. Prefer explicit CyberLifeBook project decisions over external recommendations.
5. If the conflict cannot be resolved, document it as unresolved.

Never invent a resolution.

---

# 8. Index

When ingest creates a new resume or concept, update:

```
llm_wiki/wiki/index.md
```

The index is a navigation layer.

It should:

- group related knowledge;
- link to relevant resumes and concepts;
- remain compact;
- avoid duplicating the contents of knowledge pages.

---

# 9. Activity Log

After every successful ingest operation, append a record to:

```
llm_wiki/wiki/log.md
```

The log is append-only.

Never modify or remove previous log entries.

Each entry should contain:

- date;
- processed source;
- created or updated resume;
- created or updated concepts;
- short description of the operation.

Example:

```
# LLM Wiki Activity Log

<!-- Append-only. Never modify or remove historical entries. -->

- 26-08-2026 | INGEST | [[raw/source]] → [[resume/source]] | concepts: [[concept-a]], [[concept-b]]   
- 27-08-2026 | QUERY  | [[queries/query-name]] 
- 28-08-2026 | LINT   | wiki health check completed
```

---

# 10. Quality Check

Before completing an ingest operation, verify:

## Source Integrity

- `raw/` was not modified.
- Original source files remain intact.

## Resume

- A corresponding resume exists.
- The resume captures the useful knowledge from the source.
- The resume is not a copy of the source.
- The resume links to the source.

## Concepts

- Relevant existing concepts were checked.
- Duplicate concept pages were not created.
- New knowledge was integrated with existing knowledge.
- Source provenance was preserved.

## Navigation

- New pages are represented in `index.md`.
- Internal Obsidian links are valid.

## Log

- A new append-only log entry was added.
- Historical log entries remain unchanged.

---

# 11. Restrictions

The agent MUST NOT:

- modify `raw/`;
- delete source material;
- fabricate information;
- invent sources;
- silently resolve contradictions;
- create trivial concept pages;
- duplicate complete source documents in `resume/`;
- store conversation transcripts as Wiki knowledge;
- store query answers as permanent knowledge;
- modify `schema/` unless explicitly instructed by the human.

---

# Operating Principle

The LLM Wiki separates source material from derived knowledge.

```
raw/
    Immutable source material
            ↓
resume/
    Knowledge extracted from individual sources
            ↓
concepts/
    Accumulated and cross-source knowledge
```

The agent maintains the derived knowledge layer while preserving the traceability of every important conclusion back to the original source.