
# Memory [[CyberLifeBook]]

```

                          CyberLifeBook
                              │
                ┌─────────────┴─────────────┐
                │                           │
             ЗНАНИЯ                      ПАМЯТЬ
                │                           │
          ┌─────┴─────┐               claude-mem
          │           │
       llm_wiki     Graphify
          │           │
     project        code/
     knowledge     structure
          │
          └─────────────┐
                        │
                    AI Agent
                        │
             ┌──────────┼──────────┐
             │          │          │
          Skills      Agents      sqz
             │          │          │
             └──────────┴──────────┘
                        │
                 everything-claude-code
```

---

## 1. `everything-claude-code` — фундамент

Я бы начал именно с него.

Не надо слепо устанавливать всё содержимое репозитория. Сам проект прямо говорит, что его следует адаптировать под собственный workflow, а не включать всё подряд.

Нам особенно интересны:

- `agents/`
- `skills/`
- `rules/`
- `hooks/`
- нужные `commands/`

Но **не будем сразу подключать всё**.

Причём у нас уже существует собственная система:

```
llm_wiki/schema/
├── ingest/SKILL.md
├── query/SKILL.md
└── lint/SKILL.md
```

И она должна оставаться **нашей**. `everything-claude-code` — инфраструктура агента, а `llm_wiki` — проектное знание.

Это принципиально разные уровни.

---

## 2. `claude-mem` — память агента

Это второй слой.

Очень хорошо ложится на нашу архитектуру:

```
claude-mem
    ↓
"Что мы делали раньше?"
    ↓
session history / observations
```

против:

```
llm_wiki
    ↓
"Что мы знаем о проекте?"
    ↓
stable project knowledge
```

То есть **claude-mem не заменяет LLM Wiki**.

Именно поэтому я особенно не хочу сейчас пытаться заставить их выполнять одну и ту же функцию.

---

## 3. Graphify — структурное представление проекта

Graphify тоже не надо воспринимать как ещё одну Wiki.

Он отвечает скорее на вопрос:

> «Как связаны между собой код, документация, конфигурация и другие артефакты проекта?»

Это очень хорошо сочетается с нашим CyberLifeBook, особенно учитывая, что у нас и сам проект графовый.

Получится интересная связка:

```
                  LLM Wiki
                     │
              conceptual knowledge
                     │
                     ▼
                  AI Agent
                     ▲
                     │
                  Graphify
                     │
              project structure
                     │
                     ▼
                 Codebase
```

И отдельно наш **Neo4j graph** — уже runtime/domain knowledge CyberLifeBook. Это ещё один, совершенно другой граф.

---

## 4. `sqz` — оптимизатор транспорта

Это вообще отдельная категория.

Он не должен знать ничего о CyberLifeBook.

Его задача:

```
Tool output
    ↓
   sqz
    ↓
compressed context
    ↓
LLM
```

Поэтому его имеет смысл подключать после базовой работоспособности агента.

Иначе мы начнём отлаживать сразу две переменные: **агент + компрессор контекста**.

---

## 5. `one-skill-to-rule-them-all` — я бы пока придержал

Вот тут я особенно осторожен.

Сам проект действительно предназначен для автоматического улучшения skills и создания новых навыков на основании наблюдений за рабочими сессиями.

Но у нас уже есть:

```
llm_wiki
   ↓
schema
   ↓
human-defined rules
   ↓
LLM follows them
```

А теперь представь, что одновременно:

```
human
   ↓
SKILL.md
   ↓
agent
   ↓
task-observer
   ↓
automatically modifies skill
```

Получается **второй контур управления самим агентом**.

На первом этапе это опаснее, чем полезнее.

Поэтому я бы его **не выбрасывал**, а оставил на Stage 2 после того, как мы увидим реальную работу системы и накопим несколько рабочих сессий.

---

# Итого

Я бы запускал в такой последовательности:

```
STAGE 1
│
├── everything-claude-code
│
├── Claude Code
│
├── llm_wiki
│
├── claude-mem
│
└── Graphify

        ↓

STAGE 2
│
├── sqz
│
└── verification / evaluation

        ↓

STAGE 3
│
└── one-skill-to-rule-them-all
```



## Оптимальный Стек Памяти Проекта [[CyberLifeBook]]

```
╔══════════════════════════════════════╗
║            CYBERLIFEBOOK             ║
╠══════════════════════════════════════╣
║                                      ║
║  LLM WIKI                            ║
║  ├── Raw sources                     ║
║  ├── Resume                          ║
║  └── Concepts                        ║
║                                      ║
║  CLAUDE-MEM                          ║
║  └── Session memory                  ║
║                                      ║
║  GRAPHIFY                            ║
║  └── Codebase knowledge graph        ║
║                                      ║
║  SQZ                                 ║
║  └── Context/output compression      ║
║                                      ║
║  MINIMAL SKILLS                      ║
║  ├── Strategic compact ?             ║
║  ├── Verification loop ?             ║
║  ├── code-reviewer.md  ?             ║
║  ├── security-review/  ?             ║
║  ├──                   ?             ║
║  └──                   ?             ║
║                                      ║
╚══════════════════════════════════════╝
```


## 🧠 Организация памяти в проекте [[CyberLifeBook]]

                 3D SoNet

                       │

        ┌──────────────┼──────────────┐
        │                             │
	   Runtime System              Knowledge System
        │                             │
        ▼                             ▼
     Source Code                 Obsidian Vault
        │                             │
        ▼                             ▼
     Graphify                 .skills/.prompts/ADR
        │                             │
        └──────────────┬──────────────┘

                      ▼

                  Neo4j Graph

                       ▼

                 Context Engine

                       ▼

             OpenCode / Codex / ChatGPT

[[AIOS]]

\Integral part [[AIOS]]



# ПРАВИЛО МАРШРУТИЗАЦИИ

Свежая Wiki уже фактически говорит нам правильный ответ: Claude-Mem нативно закреплён за Claude Code, Graphify — за OpenCode, а переносить каждый plugin во все runtime'ы специально не требуется. Claude-Mem у нас уже E2E-проверен именно по цепочке `Claude Code → Claude-Mem`; его назначение — межсессионная память, а не общий источник истины проекта.

Я бы окончательно зафиксировал архитектуру так:

```
                         Андрей
                            │
                            ▼
                    ChatGPT / Умник
                 Architecture + Knowledge
                            │
             ┌──────────────┼──────────────┐
             │              │              │
             ▼              ▼              ▼
         OpenCode       Claude Code       Codex
             │              │              │
         Graphify        Claude-Mem      GPT-6
             │              │              │
       CODE STRUCTURE      HISTORY      HEAVY ENGINEERING
             │              │              │
             └──────────────┼──────────────┘
                            ▼
                    Shared Project Layer
                  Source + Wiki + ADR + Git
```

То есть **plugins принадлежат runtime'ам, знания — проекту**.

### Правило маршрутизации

Если задача требует понять:

```
"Где это находится?"
"Что связано с этим сервисом?"
"Какой минимальный кусок codebase читать?"
```

→ **OpenCode + Graphify**.

И это уже проверено: OpenCode самостоятельно использовал Graphify для discovery, затем переходил к targeted source verification. Сам Graphify остаётся навигационным слоем, а не доказательством runtime-поведения.

Если задача требует:

```
"Что мы делали в прошлой сессии?"
"Почему агент пришёл к этому?"
"Какие наблюдения уже были?"
"Продолжи длительное исследование"
```

→ **Claude Code + Claude-Mem**.

Если задача требует:

```
"Сделай сложную реализацию"
"Проведи глубокий review"
"Разрули тяжёлый bug"
```

→ **Codex/GPT-6**, причём необходимые знания он получает из общего слоя:

```
AGENTS
Wiki
ADR
Source
Git
reports/docs
```

а не из Claude-Mem или Graphify напрямую.

---

## А если нужны и Graphify, и Claude-Mem?

Вот здесь я **категорически не стал бы строить bridge между plugins**.

Не так:

```
Claude ↔ Graphify adapter
OpenCode ↔ Claude-Mem adapter
Codex ↔ оба plugin
```

Это снова приведёт нас к месяцу настройки AIOS. 😄

А так:

```
OpenCode + Graphify
        │
        │ discovery / verified findings
        ▼
   Source / docs report
        │
        ▼
Claude Code + Claude-Mem
        │
        │ history / continuation
        ▼
      result
```

И наоборот:

```
Claude-Mem
   ↓
Claude восстанавливает важный прошлый контекст
   ↓
если он нужен другим агентам
   ↓
фиксируем устойчивое знание
   ↓
Wiki / ADR / docs
   ↓
OpenCode / Codex могут его читать
```

Это очень важная граница:

> **Claude-Mem не должен становиться скрытой общей памятью AIOS.**

Если в Claude-Mem есть факт, который нужен всей Agentura, он должен подняться в общий knowledge layer — Wiki, ADR, Source или соответствующий project-state документ.

И аналогично:

> **Graphify graph не должен становиться скрытым источником архитектурной истины.**

Если OpenCode через него что-то обнаружил — критические факты проверяются по Source, после чего устойчивые выводы при необходимости попадают в Wiki. Это уже совпадает с принятым принципом `Graphify = WHERE`, `Source = TRUTH`, `Memory = HISTORY`.

### Поэтому жизненный цикл информации такой

```
                     TASK
                       │
              AGENTS routing
                       │
        ┌──────────────┴──────────────┐
        │                             │
 STRUCTURE needed?              HISTORY needed?
        │                             │
 OpenCode + Graphify           Claude + Claude-Mem
        │                             │
        └──────────────┬──────────────┘
                       ▼
                 Source verification
                       │
                 Implementation
                       │
                     Tests
                       │
          ┌────────────┴────────────┐
          ▼                         ▼
 temporary/session             durable knowledge
     context                         │
        │                    Wiki / ADR / Source
        ▼
   Claude-Mem
```

Здесь Claude-Mem сохраняет **рабочую историю**, а Wiki — **каноническое знание**. Это снимает главную опасность: разные агенты не начинают жить в разных версиях проекта.

### Что это меняет в выборе агента

Теперь агент выбирается не только по модели:

```
модель
+
стоимость
+
reasoning
```

а по:

```
MODEL CAPABILITY
      +
RUNTIME CAPABILITY
      +
PLUGIN CAPABILITY
```

Например, Nemotron Super в Claude и Nemotron Super в OpenCode — это уже **не полностью эквивалентные исполнители**:

```
Nemotron Super @ Claude
→ имеет Claude-Mem

Nemotron Super @ OpenCode
→ имеет Graphify
```

И это очень полезно. Нам не нужны три одинаковых runtime'а.

---

## Мой VERDICT

**Ничего переносить между Claude и OpenCode не надо.**

Фиксируем specialization:

```
OpenCode
→ primary development
→ Graphify
→ structural discovery

Claude Code
→ continuity / investigation
→ Claude-Mem
→ historical context

Codex
→ premium engineering
→ source/Wiki-driven context

ChatGPT / Умник
→ architecture center
→ Library knowledge
→ governance
→ agent orchestration
```

И это, кстати, уже почти полностью записано в [[AI Agents]].md: там прямо есть `OpenCode → implementation/exploration`, `Claude Code → memory + analysis`, `Codex → implementation/review/tests`.

Я бы **не создавал новый ADR**: архитектурное решение уже принято и Claude-Mem имеет статус `Accepted`. Но перед закрытием AIOS-настройки я бы слегка обновил `AI Agents.md` и `AIOS.md`, добавив одно явное правило:

> **Agent-local plugins are capabilities of their native runtimes. Cross-agent knowledge exchange occurs through shared project artifacts, not by replicating plugins across runtimes.**

Это будет хорошая последняя «хлебная крошка».