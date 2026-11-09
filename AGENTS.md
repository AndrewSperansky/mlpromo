# 3D SoNet — Agent Contract

This file defines the common rules for all AI agents working in this repository.

## 1. Instruction Hierarchy

### 1.1. Instruction precedence:

1. More specific `AGENTS.md` overrides a parent `AGENTS.md`.
2. Directory-level instructions apply only within their directory.
3. `CLAUDE.md` is used only by Claude-compatible agents and has the same priority as a local `AGENTS.md`.
4. In case of conflict, the nearest applicable instruction file wins.

Repository hierarchy:

```text
/
├── AGENTS.md              ← common rules for all agents
│ 
├── .codex/
│   └── AGENTS.md          ← Codex-specific rules only
│ 
└── admin/
    └── AGENTS.md          ← admin-specific rules only
```

Agent-specific instruction files must not duplicate common project rules.

### 1.2.  Canonical AdminDash Working Directory

The canonical path for all AdminDash (admin/) commands is the lowercase
`D:\JS_Projects\3dsonet\admin`. Do not use `D:\JS_Projects\3dsonet\Admin`.
Mixed casing causes Next.js/Webpack to see `Admin` and `admin` as distinct
module identities on Windows, splitting the framework/App Router context.

Do not assume shell working directory persists between tool calls. Set it
explicitly in the same invocation, e.g.:

```text
Set-Location D:\JS_Projects\3dsonet\admin; <command>
```


---


## 2. Common Agent Contract

This repository is AI-driven.

All agents must:

* treat the user and agent as development partners;
* address the user as Андрей / Andrey and use informal communication;
* explain important decisions rather than silently applying them;
* insist on the optimal solution when it differs from the user's proposed solution, and explain why;
* respect the user's final authority over project philosophy;
* consider the project as a whole rather than focusing only on the currently opened file;
* search for an existing implementation before creating a new class, service, module, directory, or similar component;
* avoid duplication;
* preserve the existing architecture unless an architectural change has been explicitly discussed;
* make the smallest reasonable change required by the task;
* preserve the existing project style;
* warn about architectural risks;
* never perform significant refactoring silently.

---

## 3. Engineering Principles

The following principles apply to all implementation work:

* Architecture is more important than speed.
* Design before implementation.
* Avoid magic solutions.
* Every significant decision must be explainable.
* Code should remain understandable a year later.
* Prefer established enterprise approaches where appropriate.
* Do not break existing architecture without an explicit architectural decision.
* Do not introduce a new implementation when an existing one can reasonably be extended.
* Do not mix different naming, directory, formatting, or architectural styles within the project.

All code must be written using English identifiers and English-language string literals.

---

## 4. Development Workflow

For non-trivial changes:

1. Determine whether the task requires project-specific knowledge.
2. Use the LLM Wiki Query workflow when the task materially depends on project-specific architecture, domain invariants, accepted historical decisions, terminology, or prior implementation contracts that are not already sufficiently supplied in the active task/context. Do not invoke the Wiki Query workflow for routine, local, or already-explicit implementation work.
3. Analyze the current architecture and relevant existing implementations.
4. Discuss the architectural approach when the change is non-trivial.
5. Create an implementation plan.
6. Implement in small steps.
7. Verify each step.
8. Continue only after the previous step is confirmed to work.
9. After completing the work, determine whether new durable project knowledge was created.
10. If durable knowledge was created or an existing source must be incorporated, use the appropriate LLM Wiki workflow.

The agent must not treat `llm_wiki/raw/` as the primary working knowledge layer. Raw material is ingested into the derived Wiki knowledge layer.

If an architectural change is proposed, the agent must first:

* explain the advantages;
* explain the disadvantages;
* describe the impact on existing code;
* present reasonable alternatives.

Only after this discussion should implementation be proposed.

---


## 5. Code Change Protocol

When proposing code changes:

### File path

Always specify the relative project path before presenting code.

Example:

```text
src/neo4j/migration.service.ts
```

For a small file with many changes, provide the complete revised file.

For a large file, provide the complete function or logical block being changed and show the existing version first.

For a single-line change, show the existing line first and then the replacement.

For structural changes, show the relevant project tree in ASCII format and clearly indicate what should be added or changed.

Existing comments must not be removed unless they are obsolete.

---


## 6. Code Documentation

The relative project path must appear at the beginning of a source file, before the first line of code.

Example:

```typescript
// src/neo4j/migration.service.ts
```

Meaningful structural sections should be explicitly separated.

TypeScript / JavaScript:

```typescript
// =================================
// CONSTRAINTS
// =================================
```

Python:

```python
# =================================
# INITIAL ENTITIES
# =================================
```

Functions and non-obvious logic should contain appropriate comments.

## 7. Project Knowledge and LLM Wiki

The project uses an LLM Wiki as its persistent project knowledge layer.

The LLM Wiki follows a three-layer model:

```text
raw/
    Immutable human-provided source material
          ↓
wiki/
    LLM-maintained derived knowledge
          ↑
schema/
    Human-defined rules governing Wiki operations
```    

### Raw Layer

llm_wiki/raw/ contains source material provided by the human.

Raw material is immutable.

Agents may read it during ingestion but must not modify, rename, move, or delete files in raw/.

Raw material is not the primary long-term retrieval layer for project knowledge.

### Wiki Layer

llm_wiki/wiki/ contains knowledge derived from raw sources and maintained by the LLM.

The main components are:

resume/ — knowledge extracted from individual sources;
concepts/ — accumulated knowledge across multiple sources;
index.md — content-oriented navigation;
log.md — append-only record of Wiki activity;
queries/ — preserved project-relevant retrieval questions.

The Wiki is the project's persistent knowledge layer.

Agents should prefer relevant derived knowledge from wiki/ over repeatedly processing raw sources when the required knowledge has already been incorporated into the Wiki.

### Schema Layer

llm_wiki/schema/ contains the operational rules for maintaining and querying the Wiki.

The primary operations are:

Ingest — transform source material into durable derived knowledge;
Query — retrieve relevant existing knowledge for a task;
Lint — diagnose structural and knowledge-organization problems.

Agents must follow the corresponding Skill when performing these operations.

### Knowledge Separation

The following must remain conceptually separate:
```
raw source
≠
resume
≠
concept knowledge
≠
query
≠
query result
```
A query result is not automatically project knowledge.

Knowledge should enter the persistent Wiki through the defined ingestion or knowledge-maintenance workflow.

### Project Knowledge Retrieval

When a task depends on project-specific knowledge, the agent must determine whether the required knowledge already exists in llm_wiki/wiki/.

If relevant knowledge exists, the agent should retrieve the minimum sufficient context required for the task rather than reading the entire Wiki.

The agent must not read the entire llm_wiki/ by default.

### Knowledge Maintenance

The LLM is responsible for maintaining the derived Wiki knowledge layer according to the defined Skills.

Human-provided source material remains immutable.

Significant contradictions, unresolved knowledge gaps, or architectural decisions must not be silently resolved or overwritten.

The agent must preserve provenance from derived knowledge back to its source material.

---

## 8. Skills and Procedures

Skills define how specific operations are performed.

Agents must use the relevant Skill when a task corresponds to an available procedure.

For LLM Wiki operations:

* use `llm_wiki/schema/query/SKILL.md` when retrieving project knowledge;
* use `llm_wiki/schema/ingest/SKILL.md` when incorporating source material into the Wiki;
* use `llm_wiki/schema/lint/SKILL.md` when performing a Wiki health check.

Do not reproduce detailed Skill procedures inside `AGENTS.md`.

`AGENTS.md` defines when the Wiki workflows must be used.

The corresponding Skill defines how the operation is performed.

The agent must not bypass the defined Wiki workflow by inventing an alternative process for maintaining `llm_wiki/wiki/`.

Do not modify `llm_wiki/schema/` unless explicitly instructed by the human.

---

## 9. Graphify

This project uses Graphify as the structural navigation layer for the codebase.

Conceptual boundary:

```text
Graphify = WHERE
Source   = TRUTH
```

Graphify helps agents locate and understand repository structure.
The current Source remains authoritative for actual implementation behavior.
For codebase questions, agents should use the Graphify Skill when available
rather than relying exclusively on broad raw-source browsing.
Graphify may be used to discover:
- relevant files;
- structural relationships;
- paths between components;
- focused concepts;
- project-level architecture.

Agents may use the existing graphify-out/ during repository discovery.
If graphify-out/ conflicts with the current Source, the Source wins.
In that case, Graphify must be treated as stale until refreshed.
The detailed Graphify procedure belongs to the corresponding Skill and
must not be duplicated here.

#### Graphify Freshness Rule

After user/Андрей  grant FINAL ACCEPTANCE to a change that structurally modifies the Source,
the Agent MUST refresh Graphify and verify that the resulting structural
representation corresponds to the accepted repository state.

A Graphify refresh is required when an accepted change adds, removes, moves,
or materially changes structural source elements such as:
- source files or directories;
- modules;
- classes or services;
- resolvers;
- DTOs, GraphQL inputs, or object types;
- significant imports or dependencies;
- other source structures indexed by Graphify.
A Graphify refresh is not required for documentation-only changes, reports,
ADR text changes, LLM Wiki text changes, or other changes that do not affect
the indexed Source structure.
The canonical closing sequence for a structural Source change is:

```
Implementation
    ↓
Verification
    ↓
Architecture Review
    ↓
FINAL ACCEPTANCE
    ↓
Graphify Refresh + Verification
    ↓
Paperwork / Knowledge Sync
    ↓
Commit / Sync
```


A structural Source change is not considered fully closed until the required
Graphify refresh and verification have completed successfully.

## 10. Communication

Use emojis sparingly to draw attention to important points.

When discussing technology, expand technical acronyms with a short explanation when they first become relevant.

The agent must explain important decisions, identify architectural risks, and distinguish between:

* established project facts;
* assumptions;
* proposed changes.

## 11. Agent-Specific Instructions

Agent-specific instruction files may extend or override this contract only when the behavior is genuinely specific to that agent or directory.

They must not duplicate common project rules.

Examples:

```text
.codex/AGENTS.md
```

may contain Codex-specific behavior.

```text
admin/AGENTS.md
```

may contain rules specific to the `admin` directory.

Common project philosophy, engineering principles, workflow, and documentation rules belong here.
