

# CLB AIOS Persistent Working Memory — Roadmap

**Project:** CyberLifeBook / 3D SoNet  
**Subsystem:** AI Operating System / Persistent Working Memory  
**Document class:** Development Roadmap  
**Architecture authority:** Architecture Center — Андрей + ChatGPT / Умник  
**Execution layer:** AI Agentura  
**Status:** ACTIVE  
**Updated:** 2026-11-03

---

## 1. Goal

Build a minimal, reliable, project-native Persistent Working Memory runtime that allows supported AI Agentura sessions to recover the current operational state of CyberLifeBook deterministically across sessions.

The subsystem must preserve the authority hierarchy:

```
Source / ADR / Roadmap / authoritative Wiki
                    >
            Working Memory
                    >
        agent/session observations
```

Working Memory is an operational continuation layer.

It is not a replacement for canonical project knowledge.

---

# 2. Target Architecture

```
CANONICAL PROJECT KNOWLEDGE
Source / ADR / Roadmap / Wiki
             │
             ▼
        CONSOLIDATION
             │
             ▼
      memory/state.json
             │
      ┌──────┴─────────┐
      ▼                ▼
memory/MEMORY.md   checkpoints/
generated view      snapshots
      │
      ▼
AIOS Memory Core
      │
      ▼
Agent Adapter
      │
      ▼
AI Agentura
```

Detailed historical evidence remains available through existing project mechanisms and is not automatically injected into every session.

---

# 3. Development Phases

## Phase 0 — Architecture Research

**Status:** COMPLETE

### Objective

Determine whether CLB should adopt an external memory platform or build a minimal project-native runtime.

### Completed work

- analyzed existing CLB knowledge and memory layers;
    
- studied external/reference memory architectures;
    
- separated Canonical Memory, Working Memory, and Session Archive;
    
- established authority hierarchy;
    
- established hot-memory vs historical-evidence distinction;
    
- selected CLB-native minimal runtime direction;
    
- rejected premature vector database / memory SaaS dependency.
    

### Result

```
CLB-native minimal Persistent Working Memory Runtime
                    SELECTED
```

---

## ✅ Phase 1A — OpenCode Lifecycle Audit

**Status:** COMPLETE

### Objective

Determine whether OpenCode exposes a runtime lifecycle mechanism capable of deterministic Working Memory hydration.

### Result

Selected lifecycle primitive:

```
experimental.chat.system.transform
```

Project-local plugin discovery through:

```
.opencode/plugins/
```

was identified and later runtime-confirmed.

No dedicated session-start hook was required.

---

## ✅ Phase 1B/1C — Deterministic Hydration PoC

**Status:** FINAL PASS

### Objective

Prove that a genuinely new OpenCode session can receive Working Memory automatically without requiring the model to voluntarily read a file.

### Proven capabilities

```
project-local plugin discovery        PROVEN
hook execution                       PROVEN
first-request hydration               PROVEN
system-context mutation               PROVEN
provider/model propagation            PROVEN
model visibility                      PROVEN
tool-free memory use                  PROVEN
causal ON/OFF dependency              PROVEN
```

Causal negative control:

```
PoC ON  → KNOWS
PoC OFF → UNKNOWN
```

### Result

Deterministic hydration is technically viable.

---

## ✅ Phase 2A — Production Working Memory Contract

**Status:** COMPLETE / CONTRACT FROZEN

### Objective

Define the smallest safe production persistence and runtime contract before implementation.

### Accepted decisions

```
P2A-D01  state.json is runtime authority
P2A-D02  minimal V1 persistence shape
P2A-D03  structured provenance + supersession
P2A-D04  bounded deterministic hydration
P2A-D05  capture separated from consolidation
P2A-D06  best-effort pre-compaction checkpoints
P2A-D07  optimistic stateVersion coordination
P2A-D08  shared core + agent-specific adapters
P2A-D09  secret/data hygiene boundary
P2A-D10  compatibility guard + graceful degradation
```

Accepted V1 persistence:

```
memory/
├── state.json
├── MEMORY.md
└── checkpoints/
```

`archive-index/` is deferred.

Initial hydration defaults:

```
maximum active items       32
maximum hydration block    8192 UTF-8 bytes
maximum individual item    2048 UTF-8 bytes
```

These are operational V1 defaults, not permanent architecture invariants.

---

##  ✅ Phase 2B — Minimal Production Working Memory Runtime

**Status:**  FINAL ACCEPTED

## Objective

Replace the experimental hydration PoC with the smallest production implementation of the accepted Phase 2A contract.

## Planned repository surface

```
memory/
├── state.json
├── MEMORY.md
└── checkpoints/

.opencode/
├── plugins/
│   └── aios-memory.js
└── aios-memory/
    └── core.js
```

Exact file impact remains subject to repository inspection before implementation.

## Required capabilities

Phase 2B must implement:

```
state schema validation
        ↓
active-item selection
        ↓
supersession filtering
        ↓
deterministic ordering
        ↓
hydration budget enforcement
        ↓
bounded projection
        ↓
OpenCode system-context injection
```

Persistence support must include:

```
stateVersion

atomic state replacement

conflict detection

generated MEMORY.md projection

secret/data hygiene boundary
```

Pre-compaction checkpoint support may be implemented only according to the frozen Phase 2A contract and must remain best-effort.

## Explicitly out of scope

Phase 2B must not introduce:

```
embeddings
vector database
SQLite memory store
archive index
memory daemon
semantic retrieval
general multi-agent framework
automatic architecture promotion
automatic autonomous consolidation
```


## 📃 Итоговый V1 contract:

 Production runtime: 
- state.json is the machine-readable runtime authority;
- MEMORY.md is generated only;
- deterministic hydration;
- provenance and supersession;
- UTF-8 bounded projection;
- secret/data-hygiene boundary;
- immutable checkpoints;
- optimistic stateVersion stale-write detection;
- atomic same-directory filesystem replacement;
- single-writer consolidation model;
- one active OpenCode production adapter.

## Exit criteria

Phase 2B implementation exists and passes static/unit verification.

Runtime acceptance is performed separately in Phase 2C.

---

## 🚧 Phase 2C — Production Runtime Acceptance

**Status:** 🚧 RUNNING

## Objective

Prove the complete production causal chain in genuinely fresh OpenCode
sessions:

state.json
→ production core
→ production adapter
→ system.transform
→ fresh session
→ model receives current Working Memory

and prove the negative control:

production hydration unavailable
→ fresh session
→ injected-only context is absent.


## Required evidence

A genuinely fresh OpenCode session must recover persisted Working Memory through:

```
memory/state.json
        ↓
AIOS memory core
        ↓
production OpenCode adapter
        ↓
system context
        ↓
fresh model request
```

without:

```
manual MEMORY.md read
repository search
session-history lookup
memory retrieval tool
human reminder
```

Runtime acceptance must verify:

```
valid state hydration
invalid state graceful degradation
missing state graceful degradation
bounded projection
superseded-item exclusion
deterministic ordering
secret filtering
compatibility guard
production plugin discovery
PoC removal / isolation
```

Pre-compaction checkpoint behavior must also be runtime-tested if implemented.

## Exit criterion

```
PRODUCTION DETERMINISTIC HYDRATION
FINAL PASS
```

---

# Phase 3 — Capture and Consolidation

**Status:** PLANNED

## Objective

Implement controlled Working Memory evolution after the production hydration path is stable.

The lifecycle must preserve:

```
agent observation
        ↓
CAPTURE
        ↓
candidate / evidence
        ↓
Architecture Center acceptance
        ↓
CONSOLIDATION
        ↓
active Working Memory
```

## Required capabilities

- capture candidate operational state;
    
- distinguish evidence from accepted state;
    
- supersede obsolete entries;
    
- preserve provenance;
    
- preserve historical references;
    
- regenerate `MEMORY.md`;
    
- update `stateVersion`;
    
- reject conflicting concurrent writes.
    

## Critical invariant

Agentura must not autonomously promote its own observations into accepted architecture.

---

# Phase 4 — Multi-Agent Working Memory

**Status:** PLANNED

## Objective

Make the persisted Working Memory contract reusable by additional Agentura runtimes without creating multiple independent memories.

Architecture:

```
             memory/state.json
                    │
             shared contract
                    │
        ┌───────────┼───────────┐
        ▼           ▼           ▼
    OpenCode     Claude Code    Codex
    adapter        adapter      adapter
```

## Principles

- one project-scoped Working Memory;
    
- shared persistence contract;
    
- runtime-specific adapters;
    
- no duplicated memory truth;
    
- no mandatory central daemon;
    
- optimistic concurrency remains the default coordination mechanism unless evidence requires stronger coordination.
    

OpenCode remains the first and reference adapter.

---

# Phase 5 — Retrieval Evolution

**Status:** CONDITIONAL

This phase is not automatically required.

## Trigger

Implement only if real project use demonstrates that direct provenance pointers and existing project search mechanisms are insufficient.

Possible progression:

```
V1
structured Working Memory
+
direct provenance references
+
native histories

        ↓ if insufficient

V2
SQLite
+
FTS5 / BM25 lexical retrieval

        ↓ if still insufficient

V3
hybrid retrieval
lexical + semantic
```

## Rule

No vector database or embedding infrastructure is introduced merely because it is technically available.

Retrieval complexity must be justified by observed retrieval failures.

---

# Phase 6 — Production Hardening

**Status:** PLANNED

## Objective

Validate long-term operational reliability of the subsystem.

Potential work includes:

- schema migration strategy;
    
- corruption recovery;
    
- backup/restore behavior;
    
- checkpoint retention validation;
    
- OpenCode version compatibility tests;
    
- performance measurement;
    
- hydration-budget tuning;
    
- conflict diagnostics;
    
- security review;
    
- secret-filter effectiveness;
    
- failure telemetry;
    
- multi-agent contention testing where applicable.
    

The Working Memory subsystem must continue to fail gracefully without preventing normal Agentura operation.

---

# Phase 7 — Documentation Consolidation

**Status:** PLANNED / FINAL

## Objective

Convert the development evidence accumulated during implementation into stable structured project knowledge.

Primary inputs:

```
aios-mem-devlog.md
aios-mem-roadmap.md
docs/aios-memory-*.md
accepted ADRs
production Source
runtime acceptance evidence
```

Outputs may include structured Wiki articles for:

```
AIOS Persistent Working Memory Architecture

Working Memory Data Model

Deterministic Hydration

Capture and Consolidation

Provenance and Supersession

Agent Adapter Contract

Memory Operations and Recovery
```

Obsolete research notes and superseded development descriptions should not be retained as competing current architecture documents.

---

# 4. Current Position

```
Phase 0     Architecture Research             COMPLETE
Phase 1A    OpenCode Lifecycle Audit          COMPLETE
Phase 1B/C  Deterministic Hydration PoC       FINAL PASS
Phase 2A    Production Contract               COMPLETE
                                              CONTRACT FROZEN

────────────────────────────────────────────────────────

Phase 2B    Minimal Production Runtime        NEXT

Phase 2C    Production Runtime Acceptance     PLANNED
Phase 3     Capture & Consolidation            PLANNED
Phase 4     Multi-Agent Working Memory         PLANNED
Phase 5     Retrieval Evolution                CONDITIONAL
Phase 6     Production Hardening               PLANNED
Phase 7     Wiki Consolidation                 PLANNED
```

---

# 5. Immediate Next Step

```
Phase 2A contract
        FROZEN
          ↓
Phase 2B
Minimal Production Working Memory Runtime
          ↓
Phase 2C
Runtime Acceptance
```

No Phase 3 work begins until the production hydration runtime has passed Phase 2C acceptance.

---

# 6. Architectural Guardrails

Throughout all phases:

```
Canonical project knowledge
        >
Working Memory
        >
Agent observations
```

and:

```
Working Memory
        ≠
Wiki

Working Memory
        ≠
ADR

Working Memory
        ≠
Session Archive

Working Memory
        ≠
Graphify

Working Memory
        ≠
Claude-Mem
```

The subsystem exists to provide **small, current, deterministic operational continuity across AI-agent sessions**.

It must remain smaller and simpler than the project knowledge systems it connects.