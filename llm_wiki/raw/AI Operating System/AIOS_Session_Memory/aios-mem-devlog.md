

# AIOS Persistent Working Memory — Development Log

**Project:** CyberLifeBook / 3D SoNet  
**Subsystem:** AI Operating System / Persistent Working Memory  
**Document class:** Development Log / Engineering Journal  
**Architecture authority:** Architecture Center — Андрей + ChatGPT / Умник  
**Execution layer:** AI Agentura  
**Started:** 2026-11-03

---

## Purpose of this log

This file is the chronological development journal for the CLB AIOS Persistent Working Memory subsystem.

It records:

- research milestones;
    
- experiments;
    
- runtime evidence;
    
- Architecture Center decisions;
    
- implementation phases;
    
- accepted contracts;
    
- unresolved issues;
    
- current development state;
    
- next actions.
    

This file is intentionally chronological.

It is **not** intended to become the final structured AIOS Memory Wiki.

During active development, new accepted milestones are appended to the end of this file. After the subsystem stabilizes, the Development Log, implementation reports, ADRs, and research documents will be consolidated into structured Wiki articles.

Canonical project authority remains:

```
Source / ADR / Roadmap / authoritative Wiki
                    >
          AIOS Working Memory
                    >
             Session state
```

The Development Log records development history and Architecture Center decisions. It does not independently override current Source, ADR, Roadmap, or authoritative Wiki.

---

# 2026-11-02 — Persistent Inter-Session Memory Research Started

## Problem

The existing CLB AIOS already had several persistent knowledge mechanisms:

```
Source
ADR
Roadmap
LLM Wiki
Graphify
Git history
implementation reports
OpenCode session history
Codex session history
Claude Code session history
Claude-Mem
```

However, none guaranteed that a genuinely new AI-agent session would automatically receive the **current operational state of the project before beginning work**.

The missing capability was:

```
new agent session
        ↓
recover current operational state
        ↓
understand current Stage / Slice / Task
        ↓
continue work correctly
```

A file existing on disk was not sufficient.

The earlier `MEMORY.md` experiment demonstrated:

```
memory exists on disk
        ≠
memory is present in model context
```

The core missing component was therefore identified as an executable **runtime bridge** between persistent project memory and the AI-agent lifecycle.

---

# 2026-11-02 — External Memory Architecture Research

Several existing memory approaches and related technologies were studied before selecting the CLB architecture.

Important reference areas included:

- OpenClaw memory architecture;
    
- existing agent-memory implementations;
    
- Hindsight;
    
- MemPalace;
    
- native OpenCode session history;
    
- Codebase Memory MCP;
    
- existing CLB Graphify and Claude-Mem infrastructure.
    

## OpenClaw reference findings

OpenClaw was retained as a **reference architecture**, not as a selected drop-in implementation.

The most important principles adopted from the research were:

```
deterministic lifecycle hydration

small curated hot memory
        ≠
large historical memory

bounded automatic injection

provenance

supersession

capture
        ≠
consolidation

pre-compaction preservation

historical retrieval on demand
```

The research reinforced the conclusion that the failure of the earlier Markdown experiment did **not** invalidate file-based memory.

The failure exposed the absence of a deterministic runtime hydration mechanism.

## Codebase Memory MCP findings

Codebase Memory MCP was classified primarily as persistent code intelligence rather than the primary CLB inter-session Working Memory.

However, it provided useful architectural evidence for:

- OpenCode lifecycle injection;
    
- post-compaction reinjection;
    
- multi-agent integration;
    
- hybrid retrieval;
    
- separation between persistent shared state and agent-specific integration.
    

It remains potentially relevant to future Graphify evolution, but it was not selected as the CLB Working Memory foundation.

---

# 2026-11-02 — CLB-Native Architecture Direction Selected

Architecture Center selected:

> **CLB-native minimal Persistent Working Memory Runtime**

rather than making an external memory platform the authoritative CLB memory subsystem.

The selected conceptual architecture became:

```
                    CLB AIOS

               CANONICAL MEMORY
      Source / ADR / Roadmap / Wiki
                       │
                       ▼
                WORKING MEMORY
        small current operational state
                       │
                       ▼
                   AGENTURA
                       │
                       ▼
                SESSION ARCHIVE
       detailed historical evidence
```

More precisely:

```
CANONICAL MEMORY
        │
        │ authoritative
        ▼
AIOS WORKING MEMORY
        │
        │ deterministic hydration
        ▼
AGENTURA
        │
        │ targeted recall when required
        ▼
SESSION ARCHIVE
```

## Working Memory role

Working Memory was defined as the current operational state necessary to continue project work.

Candidate content:

```
Project Identity
Current Stage
Current Slice / Task
Current Execution State
Accepted Relevant Decisions
Critical Invariants
Active Constraints
Open Questions
Recent Significant Findings
Active Parallel Work
Next Actions
Provenance Pointers
```

Working Memory must remain:

- small;
    
- curated;
    
- current;
    
- project-scoped;
    
- provenance-aware;
    
- replaceable;
    
- supersession-aware.
    

Working Memory must **not** become:

- a transcript archive;
    
- another Wiki;
    
- another ADR repository;
    
- another Source index;
    
- another Graphify;
    
- an unrestricted vector database;
    
- an automatically trusted collection of model-generated facts;
    
- a second architecture authority.
    

## V1 technology boundary

Architecture Center selected a deliberately minimal V1.

V1 must not require:

```
embeddings
vector database
new database infrastructure
memory SaaS
general-purpose memory daemon
```

Retrieval evolution was intentionally deferred:

```
V1
structured files + direct provenance references

        ↓ only if justified

V2
SQLite + FTS5 / BM25

        ↓ only if lexical retrieval proves insufficient

V3
hybrid semantic retrieval
```

---

# 2026-11-02 — Phase 1A: OpenCode Lifecycle Audit

## Objective

Determine whether OpenCode exposes a lifecycle mechanism capable of deterministic Working Memory injection.

## Result

**PARTIAL PASS**

Environment inspected:

```
OpenCode CLI             1.18.32
@opencode-ai/plugin      1.18.4
@opencode-ai/sdk         1.18.4
```

The installed plugin API exposed:

```
experimental.chat.system.transform
experimental.chat.messages.transform
experimental.session.compacting
```

No dedicated session-start hook was available.

The most promising mechanism was selected:

```
.opencode/plugins/aios-memory.js
        ↓
experimental.chat.system.transform
        ↓
append bounded Working Memory block
        ↓
model system context
```

`event: session.created` could be useful for lifecycle observation, but was not sufficient by itself for deterministic model-context hydration.

## Phase 1A conclusion

The lifecycle capability existed, but the following had not yet been proven:

```
first-request hydration
model-visible propagation
blind fresh-session restoration
negative-control causality
failure degradation
```

Therefore implementation of a production runtime was not authorized.

Primary evidence:

`docs/aios-opencode-lifecycle-deterministic-hydration-audit.md`

---

# 2026-11-02 — Phase 1B/1C: Minimal Deterministic Hydration PoC

A deliberately small experimental plugin was prepared:

```
.opencode/plugins/aios-memory-poc.js
```

The PoC used:

```
experimental.chat.system.transform
```

and injected a bounded synthetic Working Memory block.

Synthetic experiment marker:

```
AIOS-PERSISTENCE-POC-2026-11
ORBIT-47
```

No production Working Memory persistence was implemented.

Primary preparation report:

`docs/aios-memory-phase1bc-minimal-hydration-poc.md`

---

# 2026-11-02 — Initial Blind Hydration Tests

## Blind Test 1

A new OpenCode session correctly returned:

```
ORBIT-47
```

but searched the repository and found the marker in the PoC source.

Result:

```
correct answer       PASS
fresh session        PASS
no manual read       PASS
causal hydration     NOT PROVEN
```

The result was classified as contaminated.

## Blind Test 2

A stricter tool-free probe instructed the model to answer only from context already available to it.

The model returned:

```
UNKNOWN
```

This provided clean evidence that the marker was not visible under that particular runtime condition.

The hydration mechanism therefore required runtime diagnostics before any architecture conclusion could be made.

---

# 2026-11-03 — Phase 1B/1C-R1 Runtime Hook Diagnostics

Agentura instrumented the PoC runtime without changing the selected hook architecture.

Temporary `DIAG()` instrumentation recorded:

```
module evaluation
plugin factory invocation
hook invocation
session ID
system array state
before/after system entry count
successful append
```

## Runtime chain proven

Controlled reproduction established:

```
project-local plugin discovery
        ↓
module evaluated
        ↓
factory invoked
        ↓
hook registered
        ↓
hook invoked
        ↓
output.system available
        ↓
bounded block appended
        ↓
provider/model receives block
        ↓
model uses injected context
```

A temporary diagnostic nonce was injected only through the system-context block.

Fresh sessions reproduced it without:

- repository search;
    
- file reads;
    
- session-history reads;
    
- memory tools;
    
- other retrieval.
    

This proved:

```
project-local plugin discovery       PASS
hook execution                       PASS
first-request invocation             PASS
system mutation                      PASS
model propagation                    PASS
model visibility                     PASS
tool-free use                        PASS
```

The earlier `UNKNOWN` result could not be reproduced.

Architecture Center therefore classified the historical event as:

```
Hydration mechanism failure: NOT REPRODUCED
Runtime hydration chain:      PROVEN WORKING
Original UNKNOWN anomaly:     ROOT CAUSE UNRESOLVED
```

No unsupported historical cause was accepted.

Primary evidence:

`docs/aios-memory-phase1bc-r1-runtime-hook-diagnostics.md`

---

# 2026-11-03 — Automatic Project-Local Plugin Discovery Confirmed

Runtime diagnostics established that:

```
.opencode/plugins/aios-memory-poc.js
```

is automatically discovered by OpenCode.

The PoC did not need to be added to:

```
.opencode/opencode.json
```

Architecture Center therefore decided:

> Do not add redundant explicit registration merely for explicitness.

The proven path is:

```
.opencode/plugins/
        ↓
automatic project-local discovery
        ↓
plugin execution
```

This remains the preferred OpenCode integration path unless later runtime evidence requires reconsideration.

---

# 2026-11-03 — Phase 1B/1C Causal Negative Control

The final missing experiment was designed to prove causality.

`ORBIT-47` could not be used because it already existed in repository and session evidence.

A fresh one-time nonce was generated:

```
AIOS-NEGCTRL-91D6E61D
```

The decisive experiment was:

```
CONTROL A

PoC enabled
fresh session
nonce available only through injected system context
zero retrieval
        ↓
model returned exact nonce
        ↓
KNOWS
```

Positive session:

```
ses_e60051e06ffeTPNfbZ4mKlI4ij
```

Runtime diagnostics confirmed:

```
module_evaluated
factory_invoked
hook_invoked
appended=true
```

The negative condition then disabled only the PoC hydration plugin through an isolated reversible file rename.

Graphify and OpenCode configuration were not changed.

```
CONTROL B

PoC disabled
fresh session
same semantic probe
zero retrieval
        ↓
model returned exactly
UNKNOWN
```

Negative session:

```
ses_e5fe1238bffe96YqJEew2Fq3a5
```

No PoC hook activity existed for that session.

After the experiment:

- the PoC plugin was restored;
    
- `ORBIT-47` was restored;
    
- the negative-control nonce was removed;
    
- temporary R1 diagnostics were retained pending later cleanup.
    

Acceptance matrix:

```
17 / 17 PASS
```

Primary evidence:

`docs/aios-memory-phase1bc-negative-control.md`

## Architecture Center acceptance

Architecture Center declared:

> **AIOS Memory Phase 1B/1C — FINAL PASS**

The causal dependency is therefore established:

```
PoC ON  → KNOWS
PoC OFF → UNKNOWN
```

This proves that deterministic OpenCode Working Memory hydration is technically viable without requiring the model to voluntarily read a memory file.

---

# 2026-11-03 — Architecture Status After Phase 1

The CLB-native architecture direction moved from research hypothesis to validated direction.

```
CLB-native Persistent Working Memory
DIRECTION VALIDATED

Deterministic hydration primitive    PROVEN
Fresh-session hydration              PROVEN
First-request propagation            PROVEN
Model visibility                     PROVEN
No-retrieval delivery                PROVEN
Causal ON/OFF isolation              PROVEN

Persistent storage                   NOT IMPLEMENTED
Capture                              NOT IMPLEMENTED
Consolidation                        NOT IMPLEMENTED
Checkpointing                        NOT IMPLEMENTED
Supersession                         NOT IMPLEMENTED
Production Working Memory Runtime    NOT IMPLEMENTED
```

The fundamental Phase 1 question:

> Can CLB automatically provide Working Memory to a genuinely new OpenCode session before normal work without instructing the model to read `MEMORY.md`?

was answered:

> **YES**

---

# 2026-11-03 — Phase 2A: Production Working Memory Contract Audit

After deterministic hydration was proven, Architecture Center deliberately did **not** authorize immediate production implementation.

Phase 2A was created to determine the smallest safe production Working Memory contract first.

Primary report:

`docs/aios-memory-phase2a-production-working-memory-contract-audit.md`

Result:

```
AIOS MEMORY PHASE 2A CONTRACT AUDIT COMPLETE
ARCHITECTURE DECISIONS REQUIRED
```

Acceptance matrix:

```
30 / 30 PASS
```

Agentura produced ten decision points:

```
P2A-D01 ... P2A-D10
```

No backend, frontend, canonical Wiki, ADR, Graphify behavior, or Claude-Mem behavior was modified.

---

# 2026-11-03 — Phase 2A Production Persistence Model Accepted

Architecture Center accepted the following V1 persistence architecture:

```
memory/
├── state.json
├── MEMORY.md
└── checkpoints/
    └── *.json

archive-index/
└── DEFERRED
```

## `memory/state.json`

`state.json` is the **single machine-readable runtime source** for V1 Working Memory.

It contains structured current operational state and metadata.

It is the only persisted artifact from which automatic hydration is generated.

## `memory/MEMORY.md`

`MEMORY.md` is a **generated human-readable projection**.

It exists for:

- human inspection;
    
- Git review;
    
- manual fallback/reference.
    

It is **not** an independent runtime authority.

The runtime must never resolve disagreement between `state.json` and `MEMORY.md` by trusting Markdown.

Conceptual rule:

```
state.json
    ↓
generate
    ↓
MEMORY.md
```

Never:

```
state.json  ↔  MEMORY.md
two independent authorities
```

## `memory/checkpoints/`

Checkpoints are immutable operational snapshots.

They are:

- create-only;
    
- non-authoritative;
    
- not automatically hydrated;
    
- primarily intended for recovery, diagnostics, and pre-compaction preservation.
    

## `archive-index/`

Deferred from V1.

Existing native session histories, Git, reports, canonical documentation, and other existing project mechanisms are sufficient until evidence demonstrates the need for another index.

---

# 2026-11-03 — P2A-D01..D10 Architecture Center Decisions

Architecture Center reviewed and accepted all ten Phase 2A decisions.

## P2A-D01 — Runtime Authority

**ACCEPTED**

```
state.json = runtime source
MEMORY.md  = generated projection
```

No dual authority.

---

## P2A-D02 — V1 Persistence Shape

**ACCEPTED**

V1 contains:

```
state.json
MEMORY.md
checkpoints/
```

`archive-index/` is deferred.

---

## P2A-D03 — Structured Schema, Provenance and Supersession

**ACCEPTED**

V1 uses structured schema metadata.

Important Working Memory items carry provenance and lifecycle state.

No event-sourcing platform will be introduced.

Candidate provenance taxonomy:

```
SOURCE
ADR
ROADMAP
WIKI
ARCHITECTURE_CENTER_DECISION
AGENT_OBSERVATION
RUNTIME_EVIDENCE
REPORT
```

Agent observations never become Architecture Center decisions merely because they were persisted.

---

## P2A-D04 — Hydration Budget

**ACCEPTED AS V1 OPERATIONAL DEFAULT**

Initial bounds:

```
maximum active items       32
maximum complete block     8192 UTF-8 bytes
maximum individual item    2048 UTF-8 bytes
```

Truncation occurs only between items, never in the middle of a structured item.

Space must always remain for:

- wrapper;
    
- project identity;
    
- truncation indication.
    

These values are **operational defaults**, not permanent architectural invariants.

They may be tuned later using runtime evidence without redesigning the memory architecture.

---

## P2A-D05 — Capture and Consolidation Authority

**ACCEPTED**

Capture and consolidation are separate operations.

```
CAPTURE
record evidence / candidate operational state

        ≠

CONSOLIDATION
decide what becomes active Working Memory
```

Normal Agentura task completion may create evidence or a consolidation proposal.

It must not independently promote model observations into accepted architecture.

Architecture Center acceptance may trigger deterministic consolidation of explicitly accepted state.

---

## P2A-D06 — Pre-Compaction Checkpoints

**ACCEPTED WITH RUNTIME VERIFICATION REQUIRED**

The intended V1 behavior is:

```
pre-compaction
      ↓
best-effort immutable checkpoint
      ↓
normal compaction
```

No automatic consolidation occurs during compaction.

Checkpoint failure must never prevent compaction or normal OpenCode operation.

The `experimental.session.compacting` hook still requires production runtime verification before this behavior is considered proven.

Initial retention:

```
newest 10 checkpoints
OR
14 days

whichever is smaller
```

Checkpoint files are immutable and are never automatically hydrated as current state.

---

## P2A-D07 — Multi-Agent Write Coordination

**ACCEPTED**

V1 uses:

```
optimistic stateVersion
        +
atomic replacement
        +
explicit conflict preservation
```

Conceptual write flow:

```
read stateVersion = N
        ↓
prepare candidate N+1
        ↓
verify current stateVersion still N
        ↓
atomic replacement

if current version changed
        ↓
DO NOT overwrite
        ↓
preserve/report conflict
```

No lock-file protocol, SQLite coordination database, or coordination daemon is required for V1.

Only one approved consolidation writer should normally update active Working Memory at a time.

---

## P2A-D08 — Shared Core vs Agent Adapter

**ACCEPTED**

The persisted Working Memory contract is agent-independent.

Agent lifecycle integration is agent-specific.

V1 implements only the already proven OpenCode adapter.

Conceptual future boundary:

```
             memory/state.json
                    │
          shared memory contract
                    │
        ┌───────────┼───────────┐
        ▼           ▼           ▼
    OpenCode     Claude Code    Codex
    adapter      future         future
      V1
```

No general multi-agent daemon or speculative adapter framework will be introduced in V1.

---

## P2A-D09 — Secret / Data Hygiene Boundary

**ACCEPTED**

Working Memory persistence must reject or redact at minimum:

```
passwords
API keys
provider keys
OAuth tokens
refresh tokens
private credentials
private certificates
transient secrets
diagnostic nonces
session cookies
raw authentication headers
unrestricted environment dumps
unnecessarily large raw tool output
full conversation transcripts
```

Filtering belongs before persistence.

V1 does not require a generalized DLP platform.

---

## P2A-D10 — Experimental OpenCode Compatibility

**ACCEPTED**

Because the selected OpenCode lifecycle hook is currently experimental, the production adapter must provide:

```
compatibility check
        ↓
supported
        ↓
normal hydration

OR

unsupported / changed API
        ↓
diagnostic warning
        ↓
no-op memory adapter
        ↓
OpenCode continues normally
```

Memory subsystem failure must never prevent normal OpenCode operation.

OpenCode upgrades require hydration compatibility revalidation.

No redundant explicit plugin registration or alternate hook is introduced without evidence.

---

# 2026-11-03 — Accepted V1 Working Memory Lifecycle

The current accepted lifecycle is:

```
CANONICAL PROJECT KNOWLEDGE
Source / ADR / Roadmap / Wiki
             │
             ▼
       consolidation
             │
             ▼
     memory/state.json
             │
      ┌──────┴────────┐
      │               │
      ▼               ▼
 MEMORY.md        checkpoints/
 generated         immutable
 projection        snapshots
      │
      │
      └──────┐
             ▼
      validate state
             ↓
      filter active
             ↓
      remove superseded
             ↓
   deterministic ordering
             ↓
       enforce budget
             ↓
  bounded system projection
             ↓
OpenCode system.transform adapter
             ↓
      fresh agent session
```

Normal hydration must use only valid active non-superseded Working Memory.

Historical evidence remains outside automatic hydration.

---

# 2026-11-03 — Accepted Authority Boundary

The following authority hierarchy is now a core AIOS Memory invariant:

```
Source / ADR / Roadmap / authoritative Wiki
                    >
            Working Memory
                    >
        agent/session observations
```

Working Memory may reference accepted architecture.

Working Memory does not create architecture.

Agentura may:

```
observe
capture evidence
propose
report
```

Architecture Center:

```
Андрей + ChatGPT / Умник
        ↓
accept / reject / modify
        ↓
canonical project state
        ↓
Working Memory consolidation
```

This boundary must be preserved in all future automatic memory features.

---

# 2026-11-03 — Current Production Implementation Boundary

At this point:

```
Research architecture                 COMPLETE
Deterministic hydration PoC           FINAL PASS
Causal ON/OFF proof                   FINAL PASS
Production contract audit             COMPLETE
P2A-D01..D10                          ACCEPTED

Production runtime                    NOT YET IMPLEMENTED
```

Expected minimal Phase 2B repository surface:

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

Exact implementation remains subject to repository inspection during Phase 2B.

The PoC:

```
.opencode/plugins/aios-memory-poc.js
```

must not simply grow indefinitely into production infrastructure.

Phase 2B should replace the experimental PoC with the approved production boundary and subsequently remove temporary diagnostic instrumentation when verification is complete.

---

# 2026-11-03 — Current AIOS Memory Status

```
CLB AIOS PERSISTENT WORKING MEMORY

Architecture direction
        VALIDATED

Phase 1A — lifecycle audit
        COMPLETE

Phase 1B/1C — deterministic hydration PoC
        FINAL PASS

Phase 1B/1C-R1 — runtime diagnostics
        COMPLETE

Causal negative control
        FINAL PASS

Phase 2A — production contract audit
        COMPLETE

P2A-D01..D10
        ARCHITECTURE CENTER ACCEPTED

Phase 2B — production runtime implementation
        READY
        NOT STARTED
```

Validated capabilities:

```
project-local plugin discovery        PROVEN
deterministic system injection        PROVEN
fresh-session hydration               PROVEN
first-request propagation             PROVEN
model visibility                      PROVEN
tool-free delivery                    PROVEN
causal ON/OFF dependency              PROVEN
```

Not yet production-proven:

```
state.json persistence
schema validation
MEMORY.md generation
atomic state replacement
stateVersion conflict handling
supersession filtering
secret filtering
bounded production projection
pre-compaction checkpointing
checkpoint retention
graceful production degradation
production plugin replacement
```

---

# Next Action

The next development slice is:

> **AIOS Memory Phase 2B — Minimal Production Working Memory Runtime**

Phase 2B must implement only the accepted V1 contract.

It must not introduce:

```
vector database
embeddings
SQLite memory store
archive index
memory daemon
general multi-agent framework
automatic architecture promotion
automatic semantic retrieval
```

Phase 2B must preserve the central design principle:

> **The smallest reliable deterministic Working Memory runtime is preferable to a general-purpose memory platform.**

After Phase 2B implementation, runtime acceptance must prove that a genuinely new OpenCode session receives current persisted Working Memory from `state.json` through the production adapter without repository retrieval or manual memory instructions.

**Current handoff state:**

```
Phase 2A
CONTRACT FROZEN
        ↓
Phase 2B
IMPLEMENTATION READY
```

---

###  ✅ Phase 2B Minimal Production Working Memory Runtime 

FINAL ACCEPTED ✔  (2026-11-03) 

Architecture Center accepted the first production-quality CLB-native
Persistent Working Memory runtime.

Accepted production surface:
- memory/state.json — sole machine-readable runtime source;
- memory/MEMORY.md — deterministic generated human-readable projection;
- memory/checkpoints/ — immutable operational snapshots;
- .opencode/aios-memory/core.js — shared Working Memory core;
- .opencode/plugins/aios-memory.js — OpenCode production adapter.

V1 persistence model:
- single-writer consolidation;
- Architecture Center-controlled consolidation is the only authorized
  logical writer of canonical state;
- agents/adapters may read, hydrate, observe and produce proposals,
  but do not autonomously promote observations into canonical state;
- stateVersion provides optimistic stale-write detection;
- same-directory temporary file + direct rename provides atomic filesystem
  replacement;
- atomic replacement is NOT filesystem compare-and-swap (CAS);
- independent concurrent canonical writers are outside the V1 model;
- future multi-writer requirements require a new Architecture Center decision.

Production runtime boundary verified during Phase 2B:
- Windows;
- Node.js v26.4.0;
- OpenCode 1.18.32.

Node 22 replacement semantics were not runtime-verified and are not a
Phase 2B acceptance requirement.

Verification:
- 15/15 focused tests PASS;
- syntax checks PASS;
- deterministic MEMORY.md generation PASS;
- stale-write/conflict preservation PASS;
- secret/data-hygiene boundary PASS;
- exactly one active hydration injector;
- production adapter uses OpenCode-supplied project directory;
- Phase 2C has not started.



### Выявленный operational gap:

> Architecture Center consolidation must use the production writer/generator path; direct manual replacement of `memory/state.json` is not an approved normal consolidation workflow.


Architecture Center verdict:
PHASE 2B — ✔ FINAL ACCEPTED.

Next:
Phase 2C — Production Runtime E2E Acceptance.



---

### Фиксируем следующую архитектуру:

Hydration читает canonical state; изменения выполняются только через явно запущенные операции с manager lock.

![604](data:image/svg+xml;charset=utf-8,%3Csvg%20font-family%3D%22-apple-system-body%2C%20ui-sans-serif%2C%20-apple-system%2C%20system-ui%2C%20%26quot%3BSegoe%20UI%26quot%3B%2C%20Helvetica%2C%20%26quot%3BApple%20Color%20Emoji%26quot%3B%2C%20Arial%2C%20sans-serif%2C%20%26quot%3BSegoe%20UI%20Emoji%26quot%3B%2C%20%26quot%3BSegoe%20UI%20Symbol%26quot%3B%22%20font-weight%3D%22400%22%20data-d-component%3D%22svg%22%20fill%3D%22currentColor%22%20style%3D%22color%3Argb\(237%2C%20237%2C%20237\)%22%20viewBox%3D%220%200%20340%20234%22%20width%3D%22100%25%22%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%3E%3Crect%20x%3D%2284%22%20y%3D%228%22%20width%3D%22172%22%20height%3D%2234%22%20rx%3D%228%22%20fill%3D%22%2364748b%22%20fill-opacity%3D%22.15%22%20stroke%3D%22%2394a3b8%22%2F%3E%3Ctext%20x%3D%22170%22%20y%3D%2229%22%20font-size%3D%2212%22%20text-anchor%3D%22middle%22%20fill%3D%22currentColor%22%20font-weight%3D%22600%22%3EAIOS%20Memory%3C%2Ftext%3E%3Crect%20x%3D%2212%22%20y%3D%2284%22%20width%3D%22144%22%20height%3D%2238%22%20rx%3D%227%22%20fill%3D%22%2364748b%22%20fill-opacity%3D%22.10%22%20stroke%3D%22%2394a3b8%22%2F%3E%3Ctext%20x%3D%2284%22%20y%3D%22107%22%20font-size%3D%2210.5%22%20text-anchor%3D%22middle%22%20fill%3D%22currentColor%22%3EOpenCode%20hydration%3C%2Ftext%3E%3Crect%20x%3D%22184%22%20y%3D%2284%22%20width%3D%22144%22%20height%3D%2238%22%20rx%3D%227%22%20fill%3D%22%2364748b%22%20fill-opacity%3D%22.10%22%20stroke%3D%22%2394a3b8%22%2F%3E%3Ctext%20x%3D%22256%22%20y%3D%22107%22%20font-size%3D%2210.5%22%20text-anchor%3D%22middle%22%20fill%3D%22currentColor%22%3EExplicit%20CLI%20%2F%20Watcher%3C%2Ftext%3E%3Cpath%20d%3D%22M170%2042%20V62%20H84%20V84%20M170%2062%20H256%20V84%22%20fill%3D%22none%22%20stroke%3D%22%2394a3b8%22%20stroke-width%3D%221.5%22%2F%3E%3Crect%20x%3D%2212%22%20y%3D%22136%22%20width%3D%22144%22%20height%3D%2232%22%20rx%3D%226%22%20fill%3D%22%2316a34a%22%20fill-opacity%3D%22.12%22%20stroke%3D%22%2316a34a%22%2F%3E%3Ctext%20x%3D%2284%22%20y%3D%22156%22%20font-size%3D%2211%22%20text-anchor%3D%22middle%22%20fill%3D%22currentColor%22%3ERead-only%3C%2Ftext%3E%3Crect%20x%3D%22184%22%20y%3D%22136%22%20width%3D%22144%22%20height%3D%2232%22%20rx%3D%226%22%20fill%3D%22%23d97706%22%20fill-opacity%3D%22.12%22%20stroke%3D%22%23d97706%22%2F%3E%3Ctext%20x%3D%22256%22%20y%3D%22156%22%20font-size%3D%2211%22%20text-anchor%3D%22middle%22%20fill%3D%22currentColor%22%3EManaged%20writes%3C%2Ftext%3E%3Cpath%20d%3D%22M84%20122%20V136%20M256%20122%20V136%22%20stroke%3D%22%2394a3b8%22%20stroke-width%3D%221.5%22%2F%3E%3Crect%20x%3D%2276%22%20y%3D%22192%22%20width%3D%22188%22%20height%3D%2234%22%20rx%3D%227%22%20fill%3D%22%2364748b%22%20fill-opacity%3D%22.10%22%20stroke%3D%22%2394a3b8%22%2F%3E%3Ctext%20x%3D%22170%22%20y%3D%22213%22%20font-size%3D%2211%22%20text-anchor%3D%22middle%22%20fill%3D%22currentColor%22%3ECanonical%20memory%2Fstate.json%3C%2Ftext%3E%3Cpath%20d%3D%22M84%20168%20V180%20H170%20V192%20M256%20168%20V180%20H170%22%20stroke%3D%22%2394a3b8%22%20stroke-width%3D%221.5%22%20fill%3D%22none%22%2F%3E%3C%2Fsvg%3E)

Это означает:

- `.opencode/plugins/aios-memory.js` остаётся исключительно read-only адаптером.
    
- `.opencode/aios-memory/cli.js` и `.opencode/aios-memory/watcher.js` сохраняют явное управление reconciliation.
    
- Автоматические записи при `session.created`, возобновлении сессии или инициализации плагина не разрешаем.
    
- Option B оставляем возможным будущим улучшением диагностики, Option C — не утверждаем.



---


---

## AIOS Memory Phase 2B.1 R1: Runtime Acceptance and Lifecycle Decision 

(2026-11-05) 

**Architecture Center:** Андрей + ChatGPT / Умник  
**Implementation:** Corrective Patch R1  
**Core status:** **ACCEPTED**  
**Full runtime acceptance:** **PENDING — 2 BLOCKED**  
**Lifecycle architecture:** **OPTION A APPROVED**

### 1. Phase 2B.1 R1 — Runtime Acceptance

Architecture Center reviewed the independent Windows runtime acceptance report and the subsequent closure investigation.

Primary evidence:

- `docs/aios-memory-phase2b1-state-management-recovery-implementation.md`
    
- `docs/aios-memory-phase2b1-runtime-acceptance-r1.md`
    
- `docs/aios-memory-phase2b1-r1-runtime-closure.md`
    

Acceptance results:

```
Baseline syntax checks       5 PASS
Baseline Node tests         66 PASS
Runtime scenarios           17 PASS
                              2 BLOCKED

TOTAL                       88 PASS
                             0 FAIL
                             2 BLOCKED
```

The following capabilities were confirmed using disposable Windows fixtures:

- Immutable content-addressed snapshots and SHA-256 verification.
    
- NTFS hard-link publication and fail-closed behavior.
    
- Multiprocess manager locking and ownership verification.
    
- Stale-lock fail-closed behavior without automatic takeover.
    
- Watcher reconciliation, external edit detection and bounded retries.
    
- Invalid-state quarantine without rewriting canonical bytes.
    
- Restore API with monotonically increasing `stateVersion`.
    
- RESTORE provenance stored in ledger metadata rather than canonical state.
    
- Post-commit failure reporting through `PARTIAL_SUCCESS`.
    
- Preservation of canonical state on invalid or missing current state.
    

No implementation defect was confirmed.

**Architecture Center decision: Phase 2B.1 R1 core implementation ACCEPTED within the verified scope.**

This decision does not constitute full runtime acceptance.

### 2. Remaining Runtime Limitations

Two scenarios remain open.

#### Interactive CLI Restore Confirmation

```
Scenario: Genuine interactive CLI Yes
Status:   BLOCKED_BY_ENVIRONMENT
```

The available Windows ConPTY harness did not establish a genuine TTY for the Node process.

Observed:

```
stdinTTY  = false
stdoutTTY = false
```

Consequently, the CLI followed its non-interactive cancellation path.

The underlying restore API passed runtime verification, but API success does not prove interactive CLI confirmation.

No `--yes` bypass or modification of the CLI confirmation contract was introduced.

### Watcher SIGINT Graceful Shutdown

```
Scenario: CLI SIGINT handler and watcher.close()
Status:   BLOCKED_BY_ENVIRONMENT / INCONCLUSIVE
```

The actual watcher started successfully, completed initial reconciliation and remained alive.

Process termination was observed, but the test environment could not independently establish that the registered SIGINT handler executed and invoked `watcher.close()`.

Process termination alone is insufficient evidence of graceful shutdown.

### Acceptance Classification

```
Implementation defect          NOT CONFIRMED
Core implementation            ACCEPTED
Interactive CLI Yes            BLOCKED
SIGINT graceful shutdown       BLOCKED / INCONCLUSIVE
Full runtime acceptance        PENDING
```

These limitations must remain visible until genuine interactive Windows runtime evidence is available.

Repeated automated tests using the same inadequate terminal environment are not required.

### 3. OpenCode Lifecycle Research

Architecture Center reviewed:

`docs/aios-memory-opencode-startup-lifecycle-research.md`

Verified environment:

```
OpenCode CLI          1.18.32
@opencode-ai/plugin   1.18.4
@opencode-ai/sdk      1.18.4
```

The current production adapter:

`.opencode/plugins/aios-memory.js`

uses:

```
experimental.chat.system.transform
        ↓
AIOSMemoryCore.produceHydrationBlock()
        ↓
output.system
```

The adapter remains read-only.

The installed OpenCode API confirms the existence of lifecycle notification hooks, including:

```
event
session.created
session.updated
session.compacted
```

However, the research did not establish guarantees for:

- Exactly-once plugin initialization.
    
- Deterministic startup event ordering.
    
- Blocking reconciliation before the first model request.
    
- Hook serialization.
    
- Guaranteed session-resume semantics.
    
- Safe automatic mutation across concurrent OpenCode processes.
    

Therefore, lifecycle notification events cannot currently be treated as a verified production startup-reconciliation boundary.

### 4. Architecture Center Decision — Option A

**APPROVED: Option A — Explicit CLI / Watcher Reconciliation Only.**

Accepted execution boundary:

```
                    AIOS Memory
                         |
             +-----------+-----------+
             |                       |
             v                       v
      OpenCode Hydration       Explicit CLI / Watcher
             |                       |
             v                       v
         READ-ONLY             MANAGED MUTATION
             |                       |
             |                 Manager Lock
             |                       |
             +-----------+-----------+
                         |
                         v
                memory/state.json
                Canonical Authority
```

Architecture rules:

1. OpenCode hydration reads validated canonical Working Memory and does not mutate it.
    
2. Reconciliation is initiated only through explicitly invoked CLI or watcher operations.
    
3. Managed mutation remains protected by the accepted R1 manager-lock protocol.
    
4. Lock contention and ambiguous stale locks fail closed.
    
5. Opening or resuming an OpenCode session must not implicitly create history, snapshots, quarantine records or regenerated projections.
    
6. `session.created` is not authorized as an automatic reconciliation trigger.
    
7. Startup failures must not introduce hidden memory mutations or prevent ordinary read-only hydration.
    
8. Architecture Center retains authority over canonical Working Memory consolidation.
    

### Deferred Alternatives

**Option B — Read-only Startup Health Assessment**

Deferred. May be considered as a separate diagnostic capability after defining lifecycle and observability requirements.

It is not reconciliation and must not be described as such.

**Option C — Automatic Startup Reconciliation**

Not approved.

Requires separate Architecture Center authorization and verified lifecycle ordering, concurrency, retry and failure semantics.

No automatic startup-reconciliation implementation is authorized by this Devlog entry.

## 5. Production Integrity

Runtime verification and closure investigation used disposable synthetic fixtures.

Production integrity was preserved.

```
memory/state.json       SHA-256 unchanged
memory/MEMORY.md        SHA-256 unchanged
memory/history/         not created
Production watcher      not started
Production lock         absent
Remaining fixtures      0
```

Verified SHA-256 values:

```
state.json:
D5EF1194C7C846A63958BE581773F2E1F26CBEF0A50B86A3DDADBF27EB91CD52

MEMORY.md:
36BF914CC44558D7B528188CF3A1BA3C03138544FD1CC42CD150F55F9B45179E
```

No implementation source, OpenCode configuration, ADR, Wiki or Logbook changes were made by the verification agents.

No Git commit was created.

## 6. Architecture and Scope Preservation

Phase 2B.1 R1 preserves the previously accepted AIOS Memory principles:

- `memory/state.json` is the canonical runtime authority.
    
- `memory/MEMORY.md` is a generated human-readable projection.
    
- Snapshots and checkpoints are non-authoritative recovery evidence.
    
- Agent observations cannot independently become accepted architecture.
    
- Architecture Center controls canonical consolidation.
    
- OpenCode hydration remains deterministic and read-only.
    
- Reconciliation and recovery use explicit managed operations.
    
- No background memory daemon or automatic session-triggered mutation is introduced.
    

The R1 manager-lock mechanism provides transaction-like exclusion for managed filesystem operations; it does not turn filesystem replacement into a database transaction or authorize arbitrary concurrent canonical writers.

No additional memory infrastructure is approved by this entry.

## 7. Current AIOS Memory Status

```
Phase 1A
Lifecycle Audit
COMPLETE

Phase 1B / 1C
Deterministic Hydration PoC
FINAL PASS

Phase 2A
Production Working Memory Contract
ACCEPTED

Phase 2B
Minimal Production Working Memory Runtime
FINAL ACCEPTED

Phase 2B.1 R1
State Management & Recovery Core
ACCEPTED

Phase 2B.1 R1
Full Windows Runtime Acceptance
PENDING — 2 ENVIRONMENT-BLOCKED

OpenCode Startup Lifecycle
OPTION A APPROVED

Automatic Startup Reconciliation
NOT AUTHORIZED
```

## 8. Next Actions

1. Preserve the two outstanding runtime scenarios as explicit acceptance limitations.
    
2. Perform genuine interactive Windows CLI verification when an appropriate terminal environment is available.
    
3. Keep production OpenCode hydration read-only.
    
4. Do not implement automatic startup reconciliation.
    
5. Synchronize Devlog, relevant Wiki and project memory records with the approved lifecycle decision.
    
6. Review Git changes separately from Stage 7 S6-C4 before committing.
    

**Architecture Center conclusion:**

Phase 2B.1 R1 core is accepted. The accepted lifecycle model is explicit CLI/watcher reconciliation with read-only OpenCode hydration. Two interactive Windows runtime scenarios remain open, and full Phase 2B.1 runtime acceptance is not yet declared.

---