# AI Mentor (Buddy) — not started

This folder is intentionally empty. Nothing imports from it — the
`/api/chat/*` routes in `_not_yet_built.py` return `501` and don't
touch this package. Auth, Profile/Settings, and the database layer
are fully independent of anything here.

## When you're ready to start

- `rag_service.py` — embeds chapter/topic content into ChromaDB,
  retrieves relevant chunks for a student's question.
- `langgraph_agent.py` — the LangGraph graph. Needs at least two entry
  points: a reactive node (message in -> RAG -> reply out) and a
  proactive check-in node (reads streak/last-studied chapter/weak
  subjects and generates the opening message without waiting for the
  student to ask).
- `prompts.py` — system prompts per `buddy_tone` (friendly / strict /
  motivational), already stored on `User.buddy_tone`.
