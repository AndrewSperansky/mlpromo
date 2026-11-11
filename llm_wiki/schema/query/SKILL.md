
---
name: Query
description: >
  Найти и собрать релевантные знания из llm_wiki/wiki/ для ответа на вопрос
  или выполнения задачи. При необходимости сохранить сам запрос в
  llm_wiki/wiki/queries/, не изменяя знания в resume/ и concepts/.

---


# LLM Wiki — Query Skill

## Purpose

This skill retrieves relevant knowledge from the LLM Wiki for a specific question or task.

The purpose of query is not to ingest new knowledge or modify the knowledge base.

The purpose is:

> Identify the relevant project knowledge, assemble the minimum sufficient context,
> and use it to answer the requested question or perform the requested task.

For questions or tasks that can be meaningfully addressed using project knowledge:

1. Preserve the query when it is relevant for future reuse.
2. Retrieve the minimum sufficient context from the LLM Wiki.
3. Use the retrieved context to answer the question or perform the task.

The query record stores the retrieval intent, not the generated answer.
```

# Query Workflow

Question / Task
       ↓
Determine whether project knowledge is relevant
       ↓
   ┌───┴────┐
  YES       NO
   ↓         ↓
Preserve?   Stop Wiki query
   ↓
 ┌──┴────┐
YES      NO
 ↓       ↓
Save    Continue
query    │
 └──┬────┘
      ↓
Retrieve relevant context
      ↓
Answer / Perform task
```

# Query Preservation

The directory:

```text
llm_wiki/wiki/queries/
```

stores relevant project queries.

A query record contains the query itself and preserves the retrieval intent.

It MUST NOT contain the generated answer as a replacement for project knowledge.

Before retrieving knowledge, determine whether the current question or task
can be meaningfully addressed using project knowledge.

If it is relevant to the project, determine whether the query is worth preserving.

Preserve the query when it:

- concerns CyberLifeBook architecture or design;
- concerns a recurring project problem;
- may be useful as a future entry point into project knowledge;
- connects multiple concepts or areas of the project;
- represents an important design or implementation question;
- is explicitly requested by the human to be preserved.

Do not preserve trivial, temporary, or unrelated questions.

A query record should contain:

```markdown
# Query Title

## Query Title

[The original question or retrieval request]

## Scope

[Relevant project area or concepts]

## Related Knowledge

- [[concepts/...]]
- [[resume/...]]
```

The generated answer is not automatically stored in the query record.


