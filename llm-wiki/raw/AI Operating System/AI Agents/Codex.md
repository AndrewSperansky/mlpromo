

### 🚀 Codex — инженерный тяжеловес

Вот здесь у нас появляется новая возможность.

Codex официально ориентирован не только на генерацию кода, но на **end-to-end engineering tasks**: исследовать repo → внести изменения → запустить команды → прогнать тесты → проверить результат.

А ещё важнее для нашей архитектуры: Codex **нативно работает с `AGENTS.md`**. OpenAI прямо рекомендует использовать его для постоянного контекста репозитория.

То есть фундамент у нас уже есть:

```
                 AGENTS.md
                /    |     \
               /     |      \
        OpenCode   Claude    Codex
```

Это именно то, к чему мы шли.

---

## ⚡ Где Codex даст нам новую силу

Например, начинается **Stage 6 Context Engine**.

Вместо того чтобы одному агенту сказать:

> Реализуй Context Engine.

можно разделить работу:

```
                    Stage 6
                       │
               архитектура — мы
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
     OpenCode        Codex         Claude
 implementation    independent     architecture/
                    review          memory check
        │              │              │
        └──────────────┼──────────────┘
                       ▼
                 final review
                       │
                       ▼
                    LLM Wiki
```

Или ещё интереснее: Codex app позволяет нескольким агентам работать **параллельно в отдельных worktrees**, не сталкивая изменения друг с другом.

Например:

```
Codex Agent A → Context domain model
Codex Agent B → Neo4j repositories
Codex Agent C → GraphQL integration
Codex Agent D → tests / architecture audit
```

А мы затем рассматриваем результаты и решаем, что принимать.


[[AI Agents]]