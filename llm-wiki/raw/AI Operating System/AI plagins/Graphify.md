# Graphify Plug-in
#### Graphify Plug-in это неотъемлемая часть [[AI Agents]] pool.

[https://github.com/Graphify-Labs/graphify](https://github.com/Graphify-Labs/graphify)

Graphify (graphifyy 0.9.53) установлен нативно в Windows.

Graphify отвечает на вопрос "где искать и что связано?", а не "как система работает на самом деле?".

## Проектный граф:  
  
graphify-out/graph.json  
~1218 nodes / ~1691 edges на момент тестов  
Graphify строит knowledge graph из проекта и документации.  
Query использует lexical matching + IDF + обход графа.  
Embeddings/vector DB при query не используются.  
LLM участвует преимущественно при построении/semantic extraction графа.  
  
## Главный принцип:  
  
Graphify = navigation/context-discovery layer, а не source of truth.  
  
Graphify node или relationship никогда не доказывает существование runtime-кода. Важные архитектурные выводы должны подтверждаться реальным TypeScript source.  
  
## OpenCode integration  
  
.opencode/opencode.json подключает:  
  
.opencode/plugins/graphify.js  
  
Plugin один раз за сессию напоминает агенту использовать Graphify для focused codebase questions.  
  
AGENTS.md содержит правила:  
  
```  
graphify query "<question>" — поиск контекста;  
graphify path "<A>" "<B>" — relationship/path;  
graphify explain "<concept>" — focused concept;  
graphify-out/wiki/index.md — broad navigation;  
GRAPH_REPORT.md — только для broad architecture review;  
после изменения кода: graphify update ..  
```  
  
## Integration tests  
  
### Test 1 — Graphify as architectural navigator  
  
PASS.  
  
Показал, что Graphify способен находить архитектурные компоненты и связи, но не полностью понимает NestJS decorator/DI semantics.  
  
### Test 2 — Graphify + runtime verification  
  
PASS.  
  
Проверенный runtime path:  
  
GraphQL Resolver  
→ OntologyService  
→ GraphService  
→ GRAPH_PROVIDER  
→ Neo4jProvider  
→ NEO4J_DRIVER  
→ Neo4j Driver  
→ session.run()  
→ Neo4j  
  
Graphify обнаруживает этот путь, но DI semantics и некоторые NestJS runtime relationships ему недоступны.  
  
### Test 3 — Autonomous Graphify usage  
  
PASS.  
  
OpenCode получил задачу без инструкции "Use Graphify first" и самостоятельно выбрал Graphify для discovery, затем перешёл к targeted source verification.  
  
Это является важным доказательством того, что Graphify уже начинает работать как естественный discovery/context layer OpenCode.  
  
## Главный архитектурный вывод  
  
AIOS должен строиться вокруг принципа:  
  
>Discovery → compact context → source verification → implementation  
  
а не:  
  
>read whole repository → huge LLM context → reason.  
  
Graphify должен помогать агенту сначала определить минимальный relevant subgraph, после чего агент проверяет критические факты в source.  
  
Information layers  
  
В проекте присутствуют:  
  
AGENTS.md  
.skills/  
.prompts/  
llm_wiki/  
Graphify knowledge graph  
source code  
  
Предварительная гипотеза распределения ответственности:  
  
llm_wiki — project knowledge / architecture / rationale  
.skills — agent procedures / how-to  
.prompts — reusable workflows / scenarios  
AGENTS.md — thin routing / project-level rules  
Graphify — machine-oriented context discovery/navigation  
Source — implementation truth  
  
Эту модель ещё следует отдельно проаудировать перед окончательным закреплением.  
  
## Important warning  
  
В документации обнаруживается drift и дублирование. Поэтому документация используется как архитектурный сигнал, но не как доказательство реализации.  
  
Особенно важно не путать:  
  
documentation/planned architecture;  
Graphify representation;  
actual runtime implementation.

### Механизм по шагам

Запрос:

```
What are the main architectural components of 3D SoNet?
```

сначала превращается в набор поисковых терминов.

Упрощённо:

```
"What are the main architectural components of 3D SoNet?"
                    ↓
              tokenization
                    ↓
what
are
the
main
architectural
components
of
3D
SoNet
                    ↓
          filtering / normalization
                    ↓
       meaningful query terms
```

Затем Graphify смотрит **не на исходный код**, а на labels узлов уже построенного `graph.json`.

Например, у тебя есть:

```
components
3D SoNet Project
main.ts
AppModule
GraphModule
Neo4jModule
...
```

Для каждого узла он вычисляет **score** — насколько хорошо label этого узла соответствует терминам запроса.

---

## А что такое IDF здесь?

Вот это самое существенное.

Graphify вычисляет:

**IDF — Inverse Document Frequency (обратная частота документа)**.

В данном случае вместо документов используются узлы графа.

Условно:

```
IDF(term) = log(1 + N / (1 + DF(term)))
```

где:

- `N` — количество узлов графа;
- `DF(term)` — сколько узлов содержат этот термин.

Это прямо есть в реализации Graphify.

Поэтому редкий термин получает большой вес:

```
Neo4jModule
```

а очень распространённый:

```
module
```

получает маленький.

---

## Затем применяется несколько уровней совпадения

Graphify не просто делает:

```
term == label
```

У него есть несколько уровней:

```
EXACT
  ↓
PREFIX
  ↓
SUBSTRING
  ↓
SOURCE
```

То есть условно:

```
query term: "components"

label: "components"
       ↑
     EXACT
```

получает огромный bonus.

А:

```
query term: "main"

label: "main.ts"
       ↑
    PREFIX
```

тоже получает высокий score.

А:

```
query term: "architectural"

label: "Architecture Skill"
```

может вообще не совпасть — **Graphify сам по себе не знает, что architectural ≈ architecture**. Это принципиальное ограничение: внутри query нет stemming, synonyms или cross-language semantic matching.

---

# Поэтому твой `Start:` — это результат ranking

Получается примерно такая схема:

```
                         QUERY
                           │
                           ▼
                 tokenize / normalize
                           │
                           ▼
                  query terms
                           │
                           ▼
              ┌─────────────────────┐
              │  score every node   │
              │                     │
              │ exact               │
              │ prefix              │
              │ substring           │
              │ source              │
              │ IDF weighting       │
              └──────────┬──────────┘
                         │
                         ▼
                    rank nodes
                         │
                         ▼
                  select top seeds
                         │
                         ▼
              ['components',
               '3D SoNet Project',
               'main.ts']
                         │
                         ▼
                  BFS depth = 2
                         │
                         ▼
                    81 nodes
```

И **вот это** отвечает на твой вопрос.

Graphify не спрашивает:

> «LLM, какие узлы соответствуют этому вопросу?»

Он делает **локальный информационно-поисковый алгоритм над графом**.

---

## Но есть один очень интересный нюанс

У Graphify есть специальный механизм **query expansion**, но он находится **на уровне agent/skill**, а не внутри самого низкоуровневого `graphify query`.

В документации Graphify прямо написано: сначала нужно взять vocabulary из самого графа, затем подобрать из него термины, соответствующие смыслу вопроса.

Например:

```
User:
"What are the main architectural components of 3D SoNet?"

             ↓

Agent / Graphify skill
             ↓
graph vocabulary:
appmodule
graphmodule
neoj4module
graphqlmodule
context
engine
...
             ↓
выбирает релевантные токены
             ↓
graphify query "graphmodule graphqlmodule neo4j ..."
             ↓
BFS
```

**Вот здесь уже может работать LLM/агент**, потому что он способен понять, что:

> "architectural components"

имеет отношение к:

> `GraphModule`, `Neo4jModule`, `GraphqlModule`, `Context Engine` и т.д.

Но сам бинарный `graphify query` этого семантического шага **не делает**.

### Поэтому ответ совсем точно такой:

**`graphify query` использует:**

- tokenization/normalization;
- case-folding;
- substring/prefix/exact matching;
- **IDF (обратную частоту)**;
- ranking/scoring узлов;
- выбор нескольких лучших seed nodes;
- затем BFS/DFS по рёбрам графа.

**LLM внутри этого поиска не нужен.**

**LLM используется на этапе построения графа**, когда ты делал `extract --backend openai --model ...`, и может использоваться **внешним агентом перед `graphify query` для semantic query expansion**.

И теперь, кстати, становится понятно, **зачем Graphify вообще нужен Claude/OpenCode skill**: skill выполняет недостающий semantic bridge между естественным языком человека и vocabulary графа, а `graphify query` остаётся быстрым детерминированным retrieval-механизмом.


**Под капотом у Graphify нет векторной БД и embeddings.**

В твоей версии `graphify 0.9.28` механизм примерно такой:

```
Текстовый вопрос
      │
      ▼
tokenization / normalization
      │
      ▼
поиск совпадений по labels/source
      │
      ▼
IDF-взвешивание
      │
      ▼
выбор стартовых узлов
      │
      ▼
BFS / DFS по реальным рёбрам графа
      │
      ▼
scoped subgraph
```

То есть это **не**:

```
question → embedding → vector DB → top-K → LLM
```

а:

```
question → lexical scoring → graph traversal
```

В исходниках `query` действительно виден `_compute_idf()` и scoring по exact/prefix/substring совпадениям; затем выбранные узлы используются как точки старта обхода.

Причём сами авторы Graphify прямо подчёркивают: **no embeddings, no vector store**.

### А вот интересный момент

У Graphify **LLM всё-таки присутствует**, но в другом месте.

Когда ты делал:

```
graphify extract ...
```

с

```
--backend openai
--model nvidia/nemotron-3-ultra-550b-a55b
```

LLM участвовал в **semantic extraction** — помогал извлекать понятия/отношения и строить граф.

А потом:

```
graphify query "..."
```

уже работает **по готовому графу локально**.

Поэтому твой результат:

```
Start: ['components', '3D SoNet Project', 'main.ts']
```

означает не «три ближайших embedding-вектора», а примерно:

> «Вот три узла, которые получили наибольший lexical/IDF score для этого вопроса; от них теперь начинаем обход графа».

И это, кстати, **очень интересная архитектурная особенность Graphify для нашего AIOS**: граф может выступать не как vector-RAG, а как **структурированный retrieval layer**, где LLM получает уже связный кусок topology проекта.

Есть даже открытый issue у Graphify на тему добавления embeddings — то есть это рассматривается как будущая функция, а не существующая основа текущего query-механизма.

Если хочешь, следующим шагом я могу разобрать **конкретно на твоём запросе `"Каковы основные архитектурные компоненты 3D SoNet?"`**, почему именно `components`, `3D SoNet Project` и `main.ts` получили статус `Start` — вплоть до формулы scoring.

---

- `query` не делает машинный перевод и не понимает смысл русского текста как LLM.
- Он ищет **лексические совпадения** между словами запроса и названиями/текстом узлов.
- Поэтому если граф построен преимущественно с английскими labels (`AppModule`, `Context Engine`, `main.ts`, `components`), русский запрос вроде:
    
    > «Каковы основные архитектурные компоненты?»
    
    почти ничего полезного сам по себе не даст.
    
- Английский запрос:
    
    > `What are the main architectural components of 3D SoNet?`
    
    естественно лучше совпадает с англоязычными узлами.
    

**Но:** это не означает, что Graphify принципиально «знает только английский». Если граф содержит русские labels, русский запрос тоже может находить их — механизм просто работает по совпадениям строк, а не по языковой семантике.

И вот здесь появляется очень интересная роль LLM:

```
Русский вопрос
      ↓
LLM понимает смысл
      ↓
английские термины графа
      ↓
graphify query
      ↓
релевантный подграф
```

То есть для нашего AIOS я бы **не заставлял пользователя формулировать запросы на английском**. Пусть пользователь говорит на любом языке, а AIOS передаёт Graphify уже нормализованный набор терминов, соответствующих vocabulary самого графа.

Это как раз тот слой, которого сейчас не хватает твоему `.opencode/plugins/graphify.js`: он пока только напоминает агенту о Graphify, а не является настоящим **semantic adapter между вопросом и graphify query**.

---

**Graphify уже имеет штатную интеграцию с OpenCode** — команда `graphify opencode install` устанавливает `AGENTS.md` и `tool.execute.before` plugin.

фактически плагин Graphify установлен только в проектной интеграции **OpenCode**:

- [graphify.js](D:\\JS_Projects\\3dsonet.opencode\\plugins\\graphify.js) — OpenCode hook `tool.execute.before`;
- [opencode.json](D:\\JS_Projects\\3dsonet.opencode\\opencode.json) подключает `.skills` проекта.

Для Codex и Claude полноценная Graphify-интеграция не установлена:
но для того чтобы агенты могли использовать Graphify мы используем следующую чистую структуру:

```
3dsonet/
│
├── .skills/                         ← SOURCE OF TRUTH
│   ├── graphify-context/
│   │   └── SKILL.md
│   └── graphify-update/
│       └── SKILL.md
│
├── .claude/skills/                  ← Claude adapters
│   ├── graphify-context/SKILL.md
│   └── graphify-update/SKILL.md
│
└── .opencode/
    └── opencode.json                ← direct .skills discovery
```



И это хороший общий стандарт для проекта:

> **Canonical procedure lives in the project domain; agent-specific skill contains only a thin adapter to that canonical procedure.**


Graphify semantic extraction через OpenCode Desktop 1.18.32 сейчас не работает из-за несовместимости @agent dispatch; это не блокирует использование code graph.

