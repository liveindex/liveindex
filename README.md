<!-- GitHub Topics: rag, ai, vector-search, llm, knowledge-base, enterprise, open-source, real-time, embeddings, fastapi -->

<p align="center">
  <img src="https://img.shields.io/badge/LiveIndex-Knowledge_Infrastructure-blue?style=for-the-badge" alt="LiveIndex" />
</p>

<h1 align="center">LiveIndex</h1>

<p align="center">
  <strong>Real-time knowledge infrastructure for AI</strong>
</p>

<p align="center">
  The knowledge layer for AI applications and agents. Always in sync. Always secure. Deploy anywhere.
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#architecture">Architecture</a> •
  <a href="#demo">Demo</a> •
  <a href="https://liveindex.ai">Website</a> •
  <a href="#contributing">Contributing</a>
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License" /></a>
  <a href="https://github.com/liveindex/liveindex/stargazers"><img src="https://img.shields.io/github/stars/liveindex/liveindex?style=social" alt="GitHub Stars" /></a>
  <a href="https://github.com/liveindex/liveindex/issues"><img src="https://img.shields.io/github/issues/liveindex/liveindex" alt="GitHub Issues" /></a>
  <img src="https://img.shields.io/badge/python-3.9+-blue.svg" alt="Python" />
  <img src="https://img.shields.io/badge/react-19-blue.svg" alt="React" />
</p>

---

## What is LiveIndex?

LiveIndex is **real-time knowledge infrastructure** that keeps your AI grounded in reality. When documents change, your AI knows immediately-not hours later, not after a batch job, but in seconds.

**The problem:** Traditional knowledge pipelines are batch-oriented. Documents get stale. Answers become wrong. Users lose trust.

**The solution:** LiveIndex watches your knowledge sources, detects changes instantly, re-indexes on the fly, and serves fresh answers with sub-100ms latency.

---

## Why LiveIndex?

| Tool | Real-time Sync | Permissions | Open Source | Deploy Anywhere |
|------|----------------|-------------|-------------|-----------------|
| **LiveIndex** | ✅ | ✅ | ✅ | ✅ |
| Glean | ⚠️ | ✅ | ❌ | ❌ |
| Pinecone | ❌ | ❌ | ❌ | ❌ |
| DIY RAG | ❌ | ❌ | N/A | ✅ |

---

## Demo

<p align="center">
  <a href="https://youtu.be/CW411Lb5Z1k">
    <img src="https://img.youtube.com/vi/CW411Lb5Z1k/maxresdefault.jpg" alt="LiveIndex Demo" width="600" />
  </a>
</p>
<p align="center">
  <em>Click to watch 3-min demo</em>
</p>

---

## Features

- **Real-time Sync** - File watcher detects changes, re-indexes in milliseconds, not minutes
- **Permission-Aware** - Role-based access control. Employees see public docs, admins see everything
- **Agent-Ready** - Works as a tool for LangChain, LlamaIndex, or custom AI agents
- **Deploy Anywhere** - Docker Compose for dev, Kubernetes for prod, air-gapped supported
- **Connector Plugins** - Local files, Google Drive, S3, Notion, Slack, Confluence (extensible)
- **Sub-100ms Queries** - Qdrant vector search with OpenAI embeddings
- **WebSocket Updates** - Live notifications when documents change
- **Open Source** - MIT licensed, fork it, extend it, contribute back

---

## Quick Start

### Prerequisites

- Docker & Docker Compose
- OpenAI API key

### 1. Clone and configure

```bash
git clone https://github.com/liveindex/liveindex.git
cd liveindex

# Add your OpenAI API key
echo "OPENAI_API_KEY=sk-your-key-here" > .env
```

### 2. Start the stack

```bash
docker-compose up -d
```

### 3. Start the backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### 4. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

### 5. Open the UI

```bash
open http://localhost:5173
```

Drop documents in the `documents/` folder and start querying. Edit a document and watch the magic happen.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         LiveIndex Architecture                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                      React Frontend                              │   │
│   │  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐   │   │
│   │  │  Document Pane   │  │    Chat Pane     │  │   Metrics    │   │   │
│   │  │  - File list     │  │  - Query input   │  │   Panel      │   │   │
│   │  │  - Sync status   │  │  - Results       │  │              │   │   │
│   │  │  - Live updates  │  │  - Citations     │  │              │   │   │
│   │  └──────────────────┘  └──────────────────┘  └──────────────┘   │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                    │                                     │
│                                    │ WebSocket + REST                    │
│                                    ▼                                     │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                      FastAPI Backend                             │   │
│   │                                                                  │   │
│   │   POST /ingest    POST /query    GET /status    WS /ws          │   │
│   │                                                                  │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│              │                │                │                         │
│              ▼                ▼                ▼                         │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐          │
│   │   Watcher    │  │  Embeddings  │  │     Vector Store     │          │
│   │  (watchdog)  │  │   (OpenAI)   │  │      (Qdrant)        │          │
│   │              │  │              │  │                      │          │
│   │  Detects     │  │  text-       │  │  1M+ vectors         │          │
│   │  changes in  │  │  embedding-  │  │  Sub-10ms search     │          │
│   │  < 1 second  │  │  3-small     │  │  Persistent storage  │          │
│   └──────────────┘  └──────────────┘  └──────────────────────┘          │
│              │                                                           │
│              ▼                                                           │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                      Connector Plugins                           │   │
│   │                                                                  │   │
│   │   LocalFiles │ GoogleDrive │ S3 │ Notion │ Slack │ Confluence   │   │
│   │      ✓       │    stub     │stub│  stub  │ stub  │    stub      │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## API Reference

### Ingest Documents

```bash
POST /ingest
{
  "directory": "./documents"
}

# Response
{
  "status": "success",
  "documents_ingested": 42,
  "chunks_created": 156,
  "time_seconds": 2.3
}
```

### Query

```bash
POST /query
{
  "query": "What is our refund policy?",
  "top_k": 5
}

# Response
{
  "answer": "Refunds are available within 30 days...",
  "sources": [
    {
      "file": "policies/refund-policy.md",
      "chunk": "Refunds are available within 30 days...",
      "score": 0.92
    }
  ],
  "latency_ms": 47
}
```

### WebSocket Events

```javascript
// Connect to ws://localhost:8000/ws

// Server pushes on file changes:
{ "event": "document_updated", "file": "refund-policy.md" }
{ "event": "reindex_complete", "file": "refund-policy.md", "time_ms": 150 }
```

---

## Project Structure

```
liveindex/
├── backend/
│   ├── main.py              # FastAPI app
│   ├── ingestion.py         # Document processing
│   ├── query.py             # Vector search
│   ├── watcher.py           # File system monitor
│   ├── embeddings.py        # OpenAI wrapper
│   └── connectors/          # Plugin architecture
│       ├── base.py          # Abstract connector
│       ├── local_files.py   # File system connector
│       ├── google_drive.py  # Google Drive (stub)
│       ├── s3.py            # AWS S3 (stub)
│       ├── notion.py        # Notion (stub)
│       ├── slack.py         # Slack (stub)
│       └── confluence.py    # Confluence (stub)
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx          # Main layout
│   │   ├── components/
│   │   │   ├── DocumentPane.jsx
│   │   │   ├── ChatPane.jsx
│   │   │   └── SyncNotification.jsx
│   │   └── hooks/
│   │       └── useWebSocket.js
│   └── package.json
│
├── documents/               # Your documents go here
├── landing/                 # Marketing landing page
├── docker-compose.yml       # Qdrant + services
└── README.md
```

---

## Configuration

### Environment Variables

```bash
# .env
OPENAI_API_KEY=sk-...        # Required: OpenAI API key
QDRANT_HOST=localhost        # Qdrant host (default: localhost)
QDRANT_PORT=6333             # Qdrant port (default: 6333)
DOCUMENTS_PATH=./documents   # Path to watch for documents
```

---

## Contributing

We welcome contributions! Here's how to get started:

1. **Fork the repo** and create your branch from `main`
2. **Make your changes** - add features, fix bugs, improve docs
3. **Test your changes** - make sure everything works
4. **Submit a PR** - describe what you changed and why

### Good First Issues

- Implement a connector (Google Drive, S3, Notion, Slack, Confluence)
- Add support for more file types (PDF, DOCX, PPTX)
- Improve the UI/UX
- Add tests
- Improve documentation

See [backend/connectors/README.md](backend/connectors/README.md) for the connector implementation guide.

---

## Roadmap

- [ ] PDF and Office document support
- [ ] Implement cloud connectors (Drive, S3, Notion)
- [ ] Kubernetes Helm chart
- [ ] Authentication & multi-tenancy
- [ ] Hybrid search (vector + keyword)
- [ ] Analytics dashboard

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

<p align="center">
  <strong>Built with focus by the LiveIndex team</strong>
</p>

<p align="center">
  <a href="https://liveindex.ai">liveindex.ai</a>
</p>
