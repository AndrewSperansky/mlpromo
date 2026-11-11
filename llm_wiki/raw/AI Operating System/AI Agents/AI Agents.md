
# Пул агентов и маршрутизация моделей*

## Context  
  
The 3D SoNet project requires a multi-agent AI development environment  
with a central orchestration layer, specialized AI agents, and persistent  
long-term memory.  
  
Different AI agents provide different capabilities and have different  
plugin ecosystems. Claude-Mem is natively integrated with Claude Code,  
while OpenCode provides its own independent plugin and tooling ecosystem.  
  
Attempting to adapt every plugin to every agent would create unnecessary  
coupling and maintenance overhead.  
  
## Decision  
  
* **AIOS** acts as the primary AI orchestrator and agent runtime layer.  
* **Claude Code** is the primary runtime for Claude-specific plugins and  
  Claude-Mem integration.  
* **Claude-Mem** provides the long-term memory layer for AIOS and persists  
  significant project decisions, observations, and context across sessions.  
* **OpenCode** remains a specialized alternative coding agent with its own  
  plugin ecosystem.  
* **Codex** may operate as an additional specialized AI agent within the  
  AIOS agent pool.  
* AIOS is responsible for selecting and coordinating the appropriate agent  
  for a particular task.  
* Claude-specific plugins are not required to be adapted for OpenCode.  
* The AI agent pool is conceptually referred to as the **AI Agentura**.  
  
### AI Agentura  
  
The AI Agentura consists of AI agents participating in the development  
environment.  
  
It may contain:  
  
* **Resident agents** — agents integrated directly into the project or AIOS  
  environment.  
* **External agents** — agents operating outside the project environment and  
  granted access when required.  
  
The terms are architectural concepts and do not imply a specific technical  
implementation.  

Основной агент разработки: - OpenCode 

Вспомогательные: 
- Codex 
- Claude code 
- Hermes 

Основной маршрутизатор
- Open router

В перспективе могут появляться другие агенты. 


В дальнейшем список может расширяться. 


## Архитектура организации работы


                         Андрей
                            │
                            ▼
                    ┌──────────────┐
                    │ ChatGPT/Умник│
                    │ Architecture │
                    │ Knowledge    │
                    │ Orchestration│
                    └──────┬───────┘
                           │
              ┌────────────┼─────────────┐
              ▼            ▼             ▼
          OpenCode     Claude Code      Codex
              │            │             │
        implementation   memory +     implementation
        / exploration    analysis       review/tests
              │            │             │
              └────────────┼─────────────┘
                           ▼
                     PROJECT SOURCE
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
       Graphify        Claude-Mem        LLM Wiki
      structure       session memory   project knowledge




### 1. 🧠 ChatGPT — архитектурный контур

Здесь оставляем то, что мы уже фактически делаем:

концепции → архитектурные решения → аудит → ADR → анализ результатов агентов → контроль целостности Wiki.

После загрузки всей проектной Wiki в Library я смогу гораздо системнее сопоставлять решения из разных документов, а не зависеть от того, какой кусок ты принёс copy-paste.

То есть здесь мы думаем.

### 2. 🔨 OpenCode — основной рабочий агент

Я бы пока не снимал с него статус primary development agent.

Мы его уже настроили:

AGENTS.md
↓
.opencode/opencode.json
↓
.skills/
+
llm_wiki/schema/
↓
source

Он уже понимает нашу инфраструктуру, Wiki и Skills.

Используем его для обычной реализации, локальных изменений и быстрых итераций.

### 3. 🧠 Claude Code — второй взгляд + память

У него уже:

CLAUDE.md
↓
AGENTS.md

.claude/skills/
├── wiki-query
├── wiki-ingest
└── wiki-lint

Claude-Mem

Поэтому Claude особенно интересен там, где полезны история работы, исследование codebase, 
независимый архитектурный анализ и восстановление контекста предыдущих сессий.

### 4. 🚀 Codex — инженерный тяжеловес

Вот здесь у нас появляется новая возможность.

Codex официально ориентирован не только на генерацию кода, но на end-to-end engineering tasks: исследовать repo → внести изменения → запустить команды → прогнать тесты → проверить результат.


## Роли AI агентуры

```
                         AIOS
                    AI orchestrator
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
     Claude Code      OpenCode         Codex
          │              │              │
     Claude plugins   OpenCode       Codex tools
          │           plugins
          ▼
     Claude-Mem
          │
          ▼
   Long-term Memory
```


---

### Agent Instructions

```
 
                Codex Agent Instructions
                            │
                            ▼
                     ┌─────────────┐
                     │    AUDIT    │
                     └──────┬──────┘
                            │
             ┌──────────────┼──────────────┐
             ▼              ▼              ▼
          AGENTS.md     .skills/       llm_wiki/
          общие         процедуры       знания
```


---

### Каждую инструкцию классифицируем:

**GLOBAL** → `AGENTS.md`

**CODEX** → `.codex/AGENTS.md`

**PROCEDURE** → `.skills/`

**KNOWLEDGE** → `llm_wiki/`

**DUPLICATE** → удалить из Codex-файла


**OpenRouter API key** — единственный модельный credential; он не хранится в проектной документации, `.claude`, `opencode.json`, Git или других конфигурационных файлах.


\*Неотъемлемая часть [[AIOS]] 