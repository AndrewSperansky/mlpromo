# Artificial Intellect Operating System 

> 3D_SoNet Knowladge
## 🎯Цели и задачи AIOS проекта [[Promo-ML]]

Это отдельный проект, задача которого — создать долговременную "память" проекта, уменьшить расход токенов, обеспечить устойчивый контекст между сессиями и организовать совместную работу нескольких AI-агентов. 

Главная цель Построить полноценную AI Workspace Architecture. Это не просто Vault Obsidian. Это единая Meta-архитектура проекта. Она должна описывать: 
• структуру знаний; 
• память AI;
• память проекта; 
• жизненный цикл знаний; 
• взаимодействие AI-агентов; 
• организацию контекста; 
• минимизацию расхода токенов; 
• систему хранения промптов; 
• систему хранения skills; 
• систему хранения архитектурных решений; 
• систему хранения Roadmap; 
• систему хранения состояния проекта. 

Предполагается разделение памяти минимум на несколько уровней. 
Например 
1. Project Knowledge Архитектура самого проекта. 
2. AI Knowledge Знания, необходимые агентам. 
3. Agent Memory Краткосрочная и долгосрочная память AI. 
4. Project State Текущее состояние разработки. 
5. Operational Knowledge Kanban, Sprint, Goals Loop. 
6. Historical Knowledge ADR, решения, история изменений. 

Graphify рассматривается как автоматический источник знаний из кода. 
Claude-Mem рассматривается исключительно как механизм межсессионной памяти AI и экономии токенов. 
Kanban является оперативным источником текущих задач. 
MEMORY.md является кратким состоянием проекта. 

В процессе проектирования необходимо определить: 
- структуру Vault; 
- правила хранения информации; 
- жизненный цикл документов; 
- правила именования; 
- структуру AI Knowledge; 
- структуру Skills; 
- структуру Prompt Library; 
- структуру Context Engine; 
- структуру Project State; 
- взаимодействие Graphify, 
- Claude-Mem и Obsidian. 

Важно 
Мы не хотим просто красивую Wiki. Мы строим полноценную AI Operating System для проекта. Все решения должны приниматься с учетом: 
- масштабируемости; - повторного использования; 
- минимизации энтропии; 
- уменьшения расхода токенов; 
- удобства работы нескольких AI
- агентов одновременно; 
- автоматизации получения контекста. 

ChatGPT должен выступать как архитектор этой системы и предлагать наиболее устойчивые решения, даже если они отличаются от привычной организации Obsidian Vault.


Используемые инструменты 

- Obsidian 
- Kanban 
- Graphify 
- Claude-Mem 
- GitHub 
- Skills 
- Prompt Library 
- ADR 


## Граница ответственности инструментов AIOS

Skill       → HOW
Prompt      → WHAT TASK / SCENARIO
Wiki        → WHAT / WHY
Graphify    → WHERE
Source      → TRUTH
Memory      → HISTORY
AGENTS      → ROUTING


**WHY → ADR**  
**WHAT → LLM Wiki**  
**HOW → Skills / Prompts**  
**WHO / RUNTIME → Agents**  
**HISTORY → Claude-Mem**  
**CODE STRUCTURE → Graphify**  
**ASSEMBLY → Context Engine**


## AIOS Architecture — Knowledge, Agents & Memory


```
                         CyberLifeBook / 3D SoNet
                         AIOS Architecture
                                │
                        ┌───────▼──────┐
                        │   AGENTS.md  │
                        │ AIOS Contract│
                        └───────┬──────┘
                                │
              ┌─────────────────┼─────────────────┐
              │                 │                 │
              ▼                 ▼                 ▼
       ┌────────────┐    ┌────────────┐    ┌────────────┐
       │  OpenCode  │    │   Claude   │    │   Codex    │
       │  Runtime   │    │  Runtime   │    │  Runtime   │
       └─────┬──────┘    └────────────┘    └────────────┘
             │
             ├───────────────┐
             ▼               ▼
      ┌─────────────┐  ┌─────────────┐
      │    Skills   │  │   Prompts   │
      │   HOW       │  │    WHAT     │
      └──────┬──────┘  └─────────────┘
             │
             ▼
      ┌──────────────┐
      │  LLM Wiki    │
      │ Project      │
      │ Knowledge    │
      └──────┬───────┘
             │
       ┌─────┼──────────────┐
       ▼     ▼              ▼
     raw   schema           wiki
      │      │               │
   HUMAN   AI PROCEDURES   PERSISTENT
   SOURCE  Ingest/Query/   KNOWLEDGE
           Lint                │
                               │
                    ┌──────────┼──────────┐
                    ▼          ▼          ▼
                 resume     concepts     index
                    │          │          │
                    └──────────┼──────────┘
                               ▼
                             log
                               │
                               ▼
                       Long-Term Project
                            Memory

       ┌──────────────┐                 ┌──────────────┐
       │     ADR      │                 │  Graphify    │
       │     WHY      │                 │ STRUCTURE    │
       └──────────────┘                 └──────────────┘
              │                                │
              └──────────────┬─────────────────┘
                             ▼
                       AIOS Context
                         Assembly
                             │
                             ▼
                    ┌─────────────────┐
                    │ Context Engine  │
                    └─────────────────┘
```


