# Перспектива  [[AIOS]]

## Четыре независимых слоя.

```
                Human
                  │
      ┌───────────┴────────────┐
      │                        │
  OpenCode                 ChatGPT
      │                        │
      ├────────────┬───────────┤
      │            │           │
    Codex        Hermes     Future AI
      │            │           │
      └────────────┴───────────┘
                   │
            AI Operating System
                   │
 ┌────────────────────────────────────┐
 │                                    │
 │   Memory Layer                     │
 │   Knowledge Layer                  │
 │   Context Layer                    │
 │   Workflow Layer                   │
 │                                    │
 └────────────────────────────────────┘
                   │
      Llm-Wiki / Graphify / Claude-Mem
                   │
             GitHub / Kanban
```

Главная идея —

**ни один AI не хранит знания у себя.**

Все знания находятся в AIOS.

Любой агент является лишь вычислителем.

---

# Разделение информации

Не по инструментам.

А по ответственности.

---

## Layer 1

# Source Layer

Источники истины.

```
GitHub
Code

Kanban
Tasks

Graphify
Code Graph

Claude-Mem
Conversation Memory

Llm-Wiki
Knowledge Base
```

Здесь ничего не вычисляется.

Только хранится.

---

## Layer 2

# Knowledge Layer

Это уже абстракции.

Например

```
Prompt Library

Skills

ADR

LLM-Wiki
```

Это долговременные знания.

Практически не меняются.

---

## Layer 3

### Context Layer

Самый интересный уровень.

Он вообще отсутствует почти во всех AI Workspace.

Именно он отвечает за экономию токенов.

Здесь появляются сущности:

```
Context

Working Set

Session

Focus

Dependencies

Memory Snapshot

Topic

Conversation State
```

То есть AI никогда не читает весь Vault.

Он получает только Context.

Например

```
Current Sprint

+

Current Module

+

Relevant ADR

+

Relevant Skills

+

Current Prompt

+

Current Memory
```

Получается компактный пакет.

---

## Layer 4

Operational Layer

То, что постоянно изменяется.

```
Sprint

Roadmap

Current Tasks

Issues

Backlog

Review

Meeting Notes

Daily Notes

Experiments
```

---

## Layer 5

History Layer

То, что уже завершено.

```
ADR

Archive

Old Roadmaps

Release Notes

Postmortem

Decision Log

Changelog
```

---

## Layer 6

AI Layer

Это вообще отдельный мир.

Каждый агент имеет собственную конфигурацию.

Например

```
OpenCode

Capabilities

Skills

Memory

System Prompt

Restrictions

Token Budget

Tools
```

ChatGPT

```
Capabilities

Prompt

Memory

Strengths

Weaknesses

Routing Rules
```

Hermes

```
Prompt

Memory

Capabilities
```

и т.д.

---

## Граф объектов

Я бы вообще отказался от хранения знаний "по папкам".

Вместо этого хранить знания как **граф объектов**.

Например документ:

```
DDD.md
```

это не файл.

Это объект.

У него есть свойства.

```
Type

Pattern

Status

Owner

Tags

Dependencies

AI relevance

Priority

Last Used

Embedding

Token Cost
```

Тогда Vault становится просто способом редактирования объектов.

Не наоборот.

---

## Context Engine

Он уже не ищет документы.

Он строит минимальный граф знаний на основании графа объектов.

Например

```
Запрос

↓

Разработка Neo4j

↓

Graphify

↓

Найдены зависимости

↓

Ontology

↓

Skills

↓

ADR

↓

MEMORY.md

↓

Current Sprint

↓

Собрать Context Bundle

↓

Передать AI
```

То есть агент никогда не получает весь Vault.

Он получает только Context Bundle.

---


## Orchestration Layer

Это слой, который определяет, **кто** и **что** должен получить.

```
Task

↓

Router

↓

Choose AI

↓

Choose Context

↓

Choose Skills

↓

Choose Prompt

↓

Assemble Context

↓

Execute

↓

Update Memory

↓

Update Graph

↓

Update Vault
```

Тогда можно без изменений архитектуры добавить нового агента (например, Gemini, Grok или другого): достаточно описать его возможности, доступные инструменты и правила маршрутизации.