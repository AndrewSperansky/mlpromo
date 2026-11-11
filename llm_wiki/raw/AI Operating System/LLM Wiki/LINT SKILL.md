# [[Wiki]] Lint Skill


---
```markdown

---
name: Lint
description: >
  Проверить целостность и здоровье llm_wiki/, выявить проблемы со структурой,
  ссылками, дублированием, навигацией и provenance, не изменяя raw/ и не выполняя
  исправления без явного разрешения человека.
---

# LLM Wiki — Lint Skill

## Purpose

This skill performs a health check of the LLM Wiki.

The purpose is to detect structural, navigational, and knowledge-organization problems
without silently modifying the Wiki.

Lint is a diagnostic operation.

It identifies:

- broken links;
- missing referenced files;
- orphaned pages;
- possible duplicate concepts;
- inconsistent naming;
- missing provenance;
- stale navigation;
- structural violations;
- inconsistencies between derived knowledge layers.

Lint does not determine whether the original source material is objectively true.

---

# 1. Immutable Source Layer
```

The directory:

```text
llm_wiki/raw/
```


is the immutable source layer.

Lint MUST NOT:

- modify files in `raw/`;
- rename files in `raw/`;
- move files in `raw/`;
- delete files in `raw/`.

The purpose of lint is to inspect the Wiki, not alter the source material.

---

# 2. Structure Validation

Verify that the expected Wiki structure exists:

```
llm_wiki/
├── raw/
├── wiki/
│   ├── index.md
│   ├── log.md
│   ├── resume/
│   ├── concepts/
│   └── queries/
└── schema/
    ├── ingest/
    │   └── SKILL.md
    ├── query/
    │   └── SKILL.md
    └── lint/
        └── SKILL.md
```

Report:

- missing required directories;
- missing required files;
- unexpected structural deviations.

Do not automatically create or remove files.

---

# 3. Resume Validation

For files in:

```
llm_wiki/wiki/resume/
```

check:

- the resume references its source in `raw/`;
- the referenced source exists;
- internal links are valid;
- the resume contains meaningful extracted knowledge;
- the resume is not an unnecessary copy of the source;
- related concepts are referenced where appropriate.

A resume should represent knowledge extracted from a source, not duplicate the entire source.

Report suspicious cases.

Do not automatically rewrite resumes.

---

# 4. Concept Validation

For files in:

```
llm_wiki/wiki/concepts/
```

check:

- possible duplicate concepts;
- inconsistent naming;
- orphaned concepts;
- missing provenance;
- broken internal links;
- concepts that appear to duplicate a single resume instead of accumulating knowledge;
- obviously contradictory information when it can be detected from the available knowledge.

Do not automatically merge, rename, or delete concept pages.

When a possible duplicate is detected, report:

- the pages involved;
- why they may represent the same concept;
- a recommended canonical name when appropriate.

---

# 5. Provenance Validation

Derived knowledge should remain traceable.

Verify the expected provenance chain:

```
concept
   ↓
resume
   ↓
raw source
```

Check for:

- concept pages without expected source references;
- resumes referencing missing raw sources;
- references to missing resume pages;
- broken provenance links.

Do not invent missing provenance.

---

# 6. Link Validation

Check internal Obsidian links across:

```
wiki/index.md
wiki/log.md
wiki/resume/
wiki/concepts/
wiki/queries/
```

Identify:

- broken links;
- references to missing files;
- malformed internal links;
- obsolete navigation references.

Do not automatically repair links.

---

# 7. Orphan Detection

Identify pages that appear to have no meaningful incoming links.

Potential orphans may include:

- resume pages not referenced from relevant concepts;
- concept pages not referenced by other knowledge;
- query records that are not connected to project knowledge;
- pages not reachable through the index when they reasonably should be.

An orphan is not automatically an error.

Some pages may intentionally have no incoming links.

Report them as:

```
WARNING: Possible orphan
```

rather than modifying or deleting them.

---

# 8. Duplicate Detection

Look for possible duplicate or overlapping concepts caused by:

- different spelling;
- singular/plural variations;
- abbreviations;
- translated names;
- alternative terminology;
- concepts with substantially overlapping definitions.

Examples:

```
AIOS
AI Operating System
```

or:

```
Context Engine
Context Management Engine
```

Possible duplicates must be reported, not automatically merged.

---

# 9. Index Validation

Check:

```
llm_wiki/wiki/index.md
```

for:

- broken links;
- references to missing pages;
- obsolete references;
- missing major knowledge areas;
- significant pages that cannot be reached through normal navigation.

The index is a navigation layer.

It does not need to contain every page.

Do not report intentional selective indexing as an error.

---

# 10. Query Validation

For:

```
llm_wiki/wiki/queries/
```

verify that query records:

- contain the original query;
- preserve the retrieval intent;
- are not being used as permanent storage for generated answers;
- contain valid internal links when related knowledge is referenced.

Do not require every query record to have identical structure.

Do not treat every user question as a query record.

---

# 11. Log Validation

For:

```
llm_wiki/wiki/log.md
```

verify:

- the file follows the append-only principle;
- entries use the established one-line format;
- referenced files exist where applicable;
- historical entries have not been silently rewritten.

Expected format:

```
DD-MM-YYYY | OPERATION | TARGET | DETAILS
```

Example:

```markdown
- 27-08-2026 | INGEST | [[raw/source]] → [[resume/source]] | concepts: [[concept-a]], [[concept-b]]
```

Report formatting problems only when they affect readability, consistency, or machine processing.

Do not rewrite historical log entries automatically.

---

# 12. Cross-Layer Consistency

Check consistency between:

```
raw/
resume/
concepts/
queries/
index.md
log.md
```

Look for situations such as:

- a resume references a source that does not exist;
- a concept references a resume that does not exist;
- an index entry points to a missing page;
- a log entry references a missing artifact;
- a query references concepts that do not exist.

Report inconsistencies without modifying the affected files.

---

# 13. Severity Levels

Classify findings using three levels.

## ERROR

A structural problem that prevents reliable operation of the Wiki.

Examples:

- broken required internal link;
- referenced source does not exist;
- required directory is missing;
- required file is missing.

## WARNING

A potential problem requiring human review.

Examples:

- possible duplicate concept;
- possible orphan;
- missing provenance;
- inconsistent naming;
- suspicious cross-layer inconsistency.

## INFO

A non-critical observation.

Examples:

- concept has only one source;
- query has no related knowledge links;
- unusually large resume;
- page is not listed in the index.

Do not promote warnings or informational observations to errors without clear evidence.

---

# 14. Lint Report

The result of a lint operation should contain:

```
LLM Wiki Health Report

ERROR
- ...

WARNING
- ...

INFO
- ...

SUMMARY

Files checked: ...
Errors: ...
Warnings: ...
Info: ...
```

If no problems are detected:

```
LLM Wiki Health Report

Status: HEALTHY

No structural errors detected.
```

The report should be concise but contain enough information to locate every reported problem.

---

# 15. Repair

Lint does not automatically repair the Wiki.

The default workflow is:

```
LINT
  ↓
REPORT
  ↓
HUMAN REVIEW
  ↓
APPROVED FIXES
  ↓
REPAIR
```

The agent may propose:

- link corrections;
- concept merges;
- renaming;
- provenance restoration;
- index updates;
- structural corrections.

Repairs require explicit human authorization.

---

# 16. Restrictions

The agent MUST NOT:

- modify `raw/`;
- delete files automatically;
- merge concepts automatically;
- rename pages automatically;
- rewrite historical log entries;
- invent provenance;
- silently resolve contradictions;
- convert warnings into errors without evidence;
- perform repairs without explicit authorization.

---

# Operating Principle

Lint protects the quality and structural integrity of the LLM Wiki.

It is a diagnostic tool, not an autonomous editor.

```
Detect
  ↓
Report
  ↓
Review
  ↓
Approve
  ↓
Repair
```

The default behavior is:

> Observe first. Change only with explicit authorization.






### Почему именно так

У нас теперь получается очень чистая тройка:


```text
                 LLM Wiki
                    │
        ┌───────────┼───────────┐
        ▼           ▼           ▼
      INGEST       QUERY       LINT
        │           │           │
     Write        Read        Check
        │           │           │
        ▼           ▼           ▼
     Knowledge    Context      Report
```

И особенно важно, что **`lint` не получает права самостоятельно «улучшать» Wiki**. Иначе однажды агент решит, что два концепта похожи, сольёт их, перепишет ссылки, а потом мы будем искать, куда исчезла половина архитектурных решений. Это нам совершенно не нужно.

После фиксации этого файла **вся тройка Skills будет готова**. Тогда уже можно будет перейти к следующему уровню — настройке `Claude-mem`, Graphify и взаимодействия этих инструментов с нашей LLM Wiki. Запускать ingest пока действительно не будем.


