# CLAUDE.md - Retriever Project

> **What is this file?** This is the project brain. Claude Code reads this automatically.
> It contains everything needed to understand and build this project.

---

## Project: Retriever

**One-liner:** Real-time retrieval infrastructure for enterprise RAG.

**The demo goal:** A live, interactive demo where an investor watches documents change and sees AI answers update in real-time. Split screen. Visceral. Undeniable.

**Timeline:** 15 hours over 48 hours (weekend sprint)

**Builder:** Systems engineer who built Amazon Ripple (petabyte-scale, 30M+ queries/day, sub-2-second latency) and Deutsche Bank trading systems (sub-100μs latency). Python proficient, vibe-codes with Claude.

---

## The "WOW" Demo Experience

**Screen layout:** Split view - left side shows document folder with sync status, right side shows chat interface.

**The 2-3 minute script:**

1. **"Here's our company knowledge base"** - Show folder with 50-100 documents. Ingest happens in seconds, count ticks up live.

2. **"Let's ask a question"** - Type: "What's our refund policy?" → Answer appears with source citation, latency displayed (47ms).

3. **"Now watch this"** - Open the refund policy doc live on screen, change "30 days" to "45 days", save it.

4. **"The magic"** - Within 2-3 seconds, notification: "1 document re-indexed." Ask same question → New answer reflects the change. Source shows "updated 5 seconds ago."

5. **"And it scales"** - Show pre-built index of 500K documents. Same sub-100ms latency.

**Target reaction:** "Wait, it already knows? How is that possible?"

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Web UI (React)                         │
│  ┌─────────────────────┐    ┌─────────────────────────────┐ │
│  │   Document Viewer   │    │      Chat Interface         │ │
│  │   - File list       │    │   - Query input             │ │
│  │   - Sync status     │    │   - Results + citations     │ │
│  │   - Live updates    │    │   - Latency display         │ │
│  └─────────────────────┘    └─────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   FastAPI Backend                           │
│  - POST /ingest         - POST /query       - GET /status   │
│  - WebSocket /ws for live sync notifications                │
└─────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
   │ File Watcher│    │  Embedding  │    │   Vector    │
   │ (watchdog)  │    │  (OpenAI)   │    │   Store     │
   │             │    │             │    │  (Qdrant)   │
   └─────────────┘    └─────────────┘    └─────────────┘
```

---

## Tech Stack

| Component | Choice | Why |
|-----------|--------|-----|
| Vector DB | **Qdrant** (Docker) | Fast setup, great Python SDK, handles 1M+ vectors |
| Embeddings | **OpenAI text-embedding-3-small** | Fast, cheap, good quality |
| Backend | **FastAPI** | Python, async, WebSockets built-in |
| File watching | **watchdog** | Battle-tested, simple API |
| Frontend | **React + Vite + Tailwind** | Fast to build with Claude |
| Chunking | **LangChain text splitters** or custom | Keep simple for demo |

---

## Project Structure

```
retriever/
├── CLAUDE.md                 # This file
├── README.md                 # Standard project docs
├── docker-compose.yml        # Qdrant + backend
├── .env                      # OPENAI_API_KEY
│
├── backend/
│   ├── main.py               # FastAPI app, all endpoints
│   ├── ingestion.py          # Load → chunk → embed → store
│   ├── query.py              # Vector search → rerank → format
│   ├── watcher.py            # File system monitoring
│   ├── embeddings.py         # OpenAI embedding wrapper
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx           # Main split-pane layout
│   │   ├── components/
│   │   │   ├── DocumentPane.jsx    # Left: file list, sync status
│   │   │   ├── ChatPane.jsx        # Right: query + results
│   │   │   └── SyncNotification.jsx
│   │   └── hooks/
│   │       └── useWebSocket.js     # Live updates
│   ├── package.json
│   └── vite.config.js
│
├── documents/                # Demo documents folder
│   ├── policies/
│   │   └── refund-policy.md
│   ├── product/
│   └── faq/
│
└── scripts/
    ├── generate_demo_docs.py # Create 100 sample docs
    └── generate_scale_index.py # Create 500K doc index for scale demo
```

---

## Hour-by-Hour Battle Plan

### Phase 1: Core Engine (Hours 1-5)

| Hour | Task | Deliverable |
|------|------|-------------|
| 1 | Project structure, Docker compose, FastAPI skeleton | `docker-compose up` works, `/health` returns OK |
| 2 | Ingestion pipeline: load → chunk → embed → store | Can ingest a folder of docs |
| 3 | Query endpoint: embed → search → return with sources | Can query and get results with citations |
| 4 | File watcher: detect changes → re-ingest | Modify file, see it re-indexed |
| 5 | WebSocket: push sync events to frontend | Events flow to connected clients |

**Phase 1 Checkpoint:** CLI/API version works end-to-end.

### Phase 2: The UI (Hours 6-10)

| Hour | Task | Deliverable |
|------|------|-------------|
| 6 | React scaffold, split-pane layout, Tailwind setup | Basic layout renders |
| 7 | Left pane: file list from API, sync status indicator | Shows documents |
| 8 | Right pane: chat interface, query submission, results | Can ask questions |
| 9 | WebSocket integration: live "document updated" toasts | See notifications |
| 10 | Polish: latency display, citations, loading states | Looks professional |

**Phase 2 Checkpoint:** Full working demo in browser.

### Phase 3: The "Wow" Touches (Hours 11-15)

| Hour | Task | Deliverable |
|------|------|-------------|
| 11 | Generate large index (500K docs) for scale demo | Can query at scale |
| 12 | Permission filtering demo (toggle user role) | Shows access control |
| 13 | Deployment panel or stats display | Extra polish |
| 14 | Record backup video of perfect demo run | Insurance |
| 15 | Rehearse, test edge cases, prep talking points | Ready to present |

---

## API Endpoints

### POST /ingest
```json
// Request
{ "directory": "./documents" }

// Response
{ "status": "success", "documents_ingested": 142, "time_seconds": 3.2 }
```

### POST /query
```json
// Request
{ "query": "What is our refund policy?", "top_k": 5 }

// Response
{
  "answer": "Refunds are available within 30 days of purchase...",
  "sources": [
    {
      "file": "policies/refund-policy.md",
      "chunk": "Refunds are available within 30 days...",
      "score": 0.92,
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ],
  "latency_ms": 47
}
```

### GET /status
```json
{
  "documents_indexed": 142,
  "last_sync": "2024-01-15T10:30:00Z",
  "watcher_active": true
}
```

### WebSocket /ws
```json
// Server pushes on file changes:
{ "event": "document_updated", "file": "policies/refund-policy.md", "timestamp": "..." }
{ "event": "reindex_complete", "file": "policies/refund-policy.md", "time_ms": 800 }
```

---

## Demo Documents

Create realistic enterprise docs for the demo:

**policies/** (5-10 docs)
- refund-policy.md ← THE KEY DEMO DOC (will be edited live)
- privacy-policy.md
- employee-handbook.md
- security-guidelines.md

**product/** (10-20 docs)
- product-overview.md
- pricing-tiers.md
- feature-roadmap.md
- api-documentation.md

**faq/** (20-30 docs)
- Various Q&A documents

**The key refund-policy.md content:**
```markdown
# Refund Policy

Last updated: January 2024

## Standard Refunds

Refunds are available within **30 days** of purchase. To request a refund:

1. Contact support@company.com
2. Provide your order number
3. Describe the reason for your request

Refunds are processed within 5-7 business days.
```

During demo, change "30 days" to "45 days" and save.

---

## Environment Variables

```bash
# .env
OPENAI_API_KEY=sk-...
QDRANT_HOST=localhost
QDRANT_PORT=6333
DOCUMENTS_PATH=./documents
```

---

## Key Commands

```bash
# Start infrastructure
docker-compose up -d

# Run backend
cd backend && uvicorn main:app --reload

# Run frontend
cd frontend && npm run dev

# Test ingestion
curl -X POST http://localhost:8000/ingest -H "Content-Type: application/json" -d '{"directory": "./documents"}'

# Test query
curl -X POST http://localhost:8000/query -H "Content-Type: application/json" -d '{"query": "What is our refund policy?"}'
```

---

## Coding Conventions

- **Python:** Use type hints, async/await for I/O operations
- **Error handling:** Always return structured errors with status codes
- **Logging:** Use structured logging (loguru or stdlib)
- **Frontend:** Functional components, hooks, Tailwind for styling
- **No over-engineering:** This is a demo. Optimize for speed of development, not production perfection.

---

## The Pitch Context

When demoing, the narrative is:

> "Most RAG demos show you a chatbot. I'm showing you the infrastructure underneath. When that document changed, my system detected it in under a second, re-embedded the relevant chunks, and updated the index. The next query reflected the change. That's what I built at Amazon scale, and that's what every enterprise deploying AI actually needs."

---

## What Success Looks Like

After 15 hours:
1. ✅ Docker compose brings up Qdrant + backend
2. ✅ Can ingest 100 documents in seconds
3. ✅ Beautiful split-screen UI
4. ✅ Query returns results with citations and latency
5. ✅ Edit a document → see live notification → re-query shows updated answer
6. ✅ 500K document index ready for scale demo
7. ✅ Backup video recorded
8. ✅ Rehearsed and ready

---

## Notes for Claude

When helping with this project:
- Prioritize speed of implementation over perfection
- Generate complete, working code (not pseudocode)
- Keep files focused and modular
- Test commands should work on first try
- When in doubt, choose the simpler approach
- This is a demo for investors, not a production system

---

*Last updated: [Current sprint start]*
