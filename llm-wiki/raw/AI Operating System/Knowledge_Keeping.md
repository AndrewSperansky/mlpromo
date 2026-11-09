
# 🗂 Хранение знаний в рамках [[AIOS]] 

«Xлебные крошки» будем оставлять системно. Причём не в виде хаотичной свалки заметок, а по нашей архитектуре:

- **ADR** → почему мы приняли решение;
- **LLM Wiki** → что мы знаем о проекте;
- **Skills** → как с этим работать;
- **Prompts** → как запускать типовые интеллектуальные задачи;
- **Claude-Mem** → история взаимодействий;
- **Graphify** → структура кода;
- **Context Engine** → что из всего этого дать агенту именно сейчас.


Например

```
LLM Wiki

↓

Долгосрочное знание о проекте
```

```
Kanban в рамках LLM Wiki

↓

оперативные задачи
```

```
ADR

↓

архитектурные решения
```

```
Graphify

↓

автоматический граф
```

```
Knowledge

↓

семантические знания
```


## Knowledge Maintenance lifecycle

Оперативный контур после **каждого блока** остаётся достаточно строгим:

```
FINAL ACCEPTANCE
      ↓
Graphify refresh + verification
      ↓
Logbook update
      ↓
ADR — если появилось/уточнилось архитектурное решение
      ↓
RAW — оперативно фиксируем новое устойчивое знание
      ↓
Commit / Sync
      ↓
NEXT BLOCK
```

То есть **ADR и RAW не откладываем**. Они дешёвые в поддержке и не дают архитектурному знанию потеряться. Derived Wiki при этом может спокойно отставать до недельной синхронизации.

А вот тяжёлый pipeline теперь строго **раз в неделю**:

```
WEEKLY KNOWLEDGE MAINTENANCE

RAW reconciliation
        ↓
ADR ↔ RAW consistency check
        ↓
Wiki INGEST
        ↓
Wiki QUERY
        ↓
Wiki LINT
        ↓
fix only new/current contradictions
        ↓
final QUERY / LINT verification if required
        ↓
Weekly Knowledge Closeout
```

И согласен со второй частью: **это работа для мощной модели**. Здесь модель должна одновременно удерживать изменения нескольких блоков, ADR, RAW, derived Wiki, supersession и искать противоречия. Экономить на reasoning именно здесь неразумно.


Получается три скорости:

|Событие|Что обновляем|
|---|---|
|Обычный accepted code block|**Graphify + Logbook**|
|Архитектурно критическое решение|**Graphify + Logbook + необходимый ADR/RAW**|
|Конец недели|**ADR/RAW reconciliation + Wiki INGEST → QUERY → LINT**|

При этом **Source остаётся TRUTH, Graphify — WHERE, Logbook — оперативная история**, поэтому между weekly Wiki sync мы не теряем состояние проекта.

[[AIOS]] 