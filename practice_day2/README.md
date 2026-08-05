# Practice Day 2: RAG Knowledge Base

## Goal

Extend the Day 1 coding agent with a **Retrieval-Augmented Generation (RAG)**
knowledge base — so the agent can review code against your team's coding
standards, testing guidelines, and review checklist.

## Setup (5 min)

Same as Day 1. If you already ran `uv sync` and configured `.env`, skip this.

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh   # macOS / Linux
uv sync
cp .env.example .env                              # add OPENAI_API_KEY
```

## Project Structure

```
practice_day2/
├── config.py              # Shared config (KNOWLEDGE_BASE_PATH)
├── prompts.py             # System prompt (code reviewer persona)
├── knowledge_base/        # 3 markdown docs the RAG will index
│   ├── python_standards.md
│   ├── testing_guidelines.md
│   └── code_review_checklist.md
├── rag.py                 # ⭐ YOUR FILE — set up vector store + search tool
├── agent.py               # ⭐ YOUR FILE — combine Day 1 tools + RAG tool
├── chat.py                # Interactive chat (uses solution_agent by default)
├── solution_rag.py        # Full solution — don't peek until you're done!
├── solution_agent.py      # Full solution — don't peek until you're done!
└── hardening/             # Production hardening sprint (see below)
```

**Note:** `agent.py` imports Day 1 tools directly via `sys.path`:

```python
sys.path.insert(0, str(Path(__file__).parent.parent / "practice_day1"))
from solution_tools import all_tools as day1_tools
```

So your Day 1 tools become part of Day 2 automatically — you only add the
new RAG tool on top.

## How RAG Works

### 1. Indexing (one-time, at startup)

Documents → chunks → vectors → FAISS index. Runs once when `rag.py` is
imported. Since FAISS lives in RAM, **this runs again on every restart**
(and re-pays the embedding cost).

```
knowledge_base/*.md
        │
        ▼
┌──────────────────────┐
│   DirectoryLoader    │  load .md files
└──────────────────────┘
        │
        ▼
┌──────────────────────────────────┐
│  RecursiveCharacterTextSplitter  │  chunk_size=500, overlap=50
└──────────────────────────────────┘
        │
        ▼  (text chunks)
┌──────────────────────┐
│   OpenAIEmbeddings   │  API call — one per chunk
└──────────────────────┘
        │
        ▼  (vectors)
┌──────────────────────┐
│        FAISS         │  in-memory index (RAM only)
└──────────────────────┘
```

### 2. Query (per user message)

The agent decides to call `search_knowledge_base(query)` → query gets
embedded → FAISS finds the top-k nearest chunks → those chunks are
returned to the LLM as grounding context.

```
User query: "naming conventions?"
        │
        ▼
┌──────────────────────┐
│   OpenAIEmbeddings   │  embed the query
└──────────────────────┘
        │
        ▼  (query vector)
┌──────────────────────┐
│   FAISS retriever    │  top-k=3 nearest chunks
└──────────────────────┘
        │
        ▼  (3 relevant text chunks)
┌──────────────────────┐
│         LLM          │  answers grounded in retrieved context
└──────────────────────┘
        │
        ▼
   Answer to user
```

### 3. Agent architecture

The LangGraph loop is the same as Day 1 — the only change is one extra
tool in the toolbox. The LLM picks which tool(s) to call per turn.

```
┌─────────────────────────────────────────────────┐
│                LangGraph Agent                  │
│                                                 │
│      ┌──────────┐         ┌──────────────┐      │
│      │ chatbot  │ ──────► │   ToolNode   │      │
│      │  (LLM)   │ ◄────── │              │      │
│      └──────────┘         └──────┬───────┘      │
│           ▲                      │              │
│           │ MemorySaver          │              │
│           │ (checkpointer)       │              │
│                                  │              │
└──────────────────────────────────┼──────────────┘
                                   │
            ┌──────────────────────┼──────────────────────┐
            ▼                      ▼                      ▼
      Day 1 tools         search_knowledge_base       (future
   (read_file, list_dir,           │                   tools…)
    run_tests, …)                  │
                                   ▼
                              FAISS + docs
```

## Task (25 min)

| Step | Where      | What to do                                                           | Time  |
| ---- | ---------- | -------------------------------------------------------------------- | ----- |
| 1    | `rag.py`   | **Load** documents with `DirectoryLoader` (glob `*.md`)              | 3 min |
| 2    | `rag.py`   | **Split** into chunks with `RecursiveCharacterTextSplitter` (500/50) | 3 min |
| 3    | `rag.py`   | **Embed** + store in FAISS, expose `retriever` (`k=3`)               | 5 min |
| 4    | `rag.py`   | **Tool** — implement `search_knowledge_base(query)` body             | 4 min |
| 5    | `agent.py` | **Combine tools** — `day1_tools + [search_knowledge_base]`           | 2 min |
| 6    | `agent.py` | **Graph** — same pattern as Day 1 (chatbot + ToolNode + edges)       | 5 min |
| 7    | `agent.py` | **Checkpointer** — `MemorySaver` + `compile(checkpointer=…)`         | 3 min |

### ✅ Checkpoint after Step 4

Before wiring the agent, run `rag.py` standalone to verify RAG works:

```bash
uv run python practice_day2/rag.py
```

Uncomment the `if __name__ == "__main__"` block at the bottom. You should
see:

```
✅ Loaded 3 documents
✅ Split into 14 chunks
✅ Vector store ready
--- Test search: 'error handling' ---
<relevant chunk of text>
```

If this works, you're safe to move on to `agent.py`.

## Testing Your Agent

By default `chat.py` imports from `solution_agent.py`. Once your own
`agent.py` is done, switch the import:

```python
# in chat.py
from agent import graph   # was: from solution_agent import graph
```

Then run:

```bash
uv run python practice_day2/chat.py
```

## Demo Queries to Try

1. **Code review with RAG (wow moment)**

   ```
   Review utils.py against our coding standards.
   ```

   The agent reads the file _and_ calls `search_knowledge_base` on its own —
   you didn't have to tell it to.

2. **No-RAG path** — shows the agent picks when to retrieve

   ```
   Find bugs in utils.py.
   ```

   Should NOT call the RAG tool — bug hunting is about logic, not standards.

3. **Testing guidelines**

   ```
   What do our testing guidelines say about coverage? Does this project follow them?
   ```

4. **Follow-up (tests checkpointer)**
   ```
   And what about the naming conventions — any violations in the same file?
   ```
   The agent should remember which file "the same file" refers to (thanks to
   Step 7, same as Day 1).

## Bonus Challenges

1. **Add another doc** — drop a new `.md` into `knowledge_base/` (e.g. security
   checklist). Re-run and watch the agent pick it up automatically.
2. **Swap the vector store** — replace FAISS with Chroma (persists to disk, no
   re-embed on each run).
3. **Re-ranker** — call `retriever.invoke(query)` with `k=10`, then re-rank the
   10 chunks with a small LLM call, keep top 3. Usually improves relevance.
4. **Metadata filter** — tag each doc by category (`standards` / `testing` /
   `review`) and let the agent filter by category in the query.

## Production Hardening Sprint (35 min)

After the core task, `hardening/` contains a 3-phase sprint:

```bash
# Phase 1: Baseline + LangSmith tracing
uv run python practice_day2/hardening/hardening_langsmith.py

# Phase 2: Attack your own agent with 5 prompt injections
uv run python practice_day2/hardening/hardening_injections.py

# Phase 3: Pick ONE defense — guardrail / cost / HITL
uv run python practice_day2/hardening/option_a_guardrail.py
uv run python practice_day2/hardening/option_b_cost.py
uv run python practice_day2/hardening/option_c_hitl.py
```

### Demo: Option C — Human-in-the-Loop

The agent asks for approval before calling **risky** tools (`get_git_diff`).
All other tools (`get_file_content`, `search_codebase`,
`search_knowledge_base`) are auto-approved — otherwise HITL becomes annoying
fast.

Run all three queries in the same chat session:

1. **Safe path — no approval needed**

   ```
   Find bugs in utils.py.
   ```

   The agent makes 2–3 tool calls (`get_file_content`, `search_codebase`)
   without asking anything.

2. **Risky path — deny**

   ```
   Write a PR summary for the last 3 commits.
   ```

   You should see:

   ```
   ⚠️  Agent wants to call: get_git_diff({'commit_a': 'HEAD~3', 'commit_b': 'HEAD'})
      Approve? (y/n):
   ```

   Type `n` — the agent receives "Action denied" and adapts (tries a
   different approach, or says it can't proceed without the diff).

3. **Risky path — approve**
   ```
   Show me the git diff between HEAD~3 and HEAD.
   ```
   Type `y` → normal flow, the agent shows the diff and writes the summary.

**Discussion takeaway:** safe tools run without approval — otherwise HITL
becomes annoying and people start rubber-stamping. We marked as risky only
tools that can leak sensitive data (a git diff exposes all changes). In a
real product, the same gate goes around: `write_file`, `run_shell`,
`send_email`, `delete_record`.
