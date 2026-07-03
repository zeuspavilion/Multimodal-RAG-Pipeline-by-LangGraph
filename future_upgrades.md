# Future Upgrades — Zeus

A living document to track planned features, improvements, and technical debt for the Zeus Multimodal RAG Agent.

---

## 🟢 Short-Term (Low Effort, High Impact)

### UX / Chat Features
- [ ] **Conversation Renaming** — Double-click a conversation title in the sidebar to rename it in place (inline edit, save on Enter/blur).
- [ ] **Conversation Search** — Add a search bar at the top of the sidebar to filter conversations by title or message content.
- [ ] **Copy Response Button** — Add a "Copy" icon on each assistant message bubble for one-click clipboard copy.
- [ ] **Clear All Chats** — Add a "Clear all conversations" option in the user account block (with confirmation).
- [ ] **Keyboard Shortcuts** — `Ctrl+K` to open new chat, `Escape` to cancel streaming.

### File Support Expansion
- [ ] **DOCX support** — Add a `python-docx` reader in the backend executor workers.
- [ ] **CSV / Excel support** — Parse tabular files and inject them as markdown tables into the LLM context.
- [ ] **PPTX support** — Extract slide text and images via `python-pptx`.

### Backend / Infrastructure
- [ ] **Upstash Redis setup** — Configure real Redis caching for conversation context (replace the current optional/no-op fallback).
- [ ] **Real Embedding Model** — Ship `all-MiniLM-L6-v2` in the Docker image instead of downloading at startup (eliminates the HuggingFace network dependency at runtime).
- [ ] **Rate Limiting** — Add per-user API rate limits using `slowapi` to prevent abuse.

---

## 🟡 Medium-Term (Architecture Improvements)

### Streaming & Performance
- [ ] **Token-by-token LLM Streaming** — Replace the current word-splitting fake-stream with actual LLM token streaming via `astream_events` for a more responsive feel.
- [ ] **Background Task Queue** — Move heavy file processing (PDF parsing, audio transcription) to a Celery or ARQ background queue instead of blocking the SSE stream.
- [ ] **Request Cancellation** — Allow users to cancel a running stream mid-generation (frontend `AbortController` + backend graceful stop).

### Conversation Management
- [ ] **Conversation Export** — Allow users to export a chat as `.md`, `.txt`, or `.pdf`.
- [ ] **Conversation Sharing** — Generate a shareable read-only link for a conversation.
- [ ] **Starred / Pinned Chats** — Pin important conversations to the top of the sidebar.
- [ ] **Conversation Folders / Tags** — Organize conversations into labeled folders.

### User Experience
- [ ] **User Settings Page** — Allow users to change display name, password, preferred model, and UI theme.
- [ ] **Dark Mode Toggle** — Implement a CSS variable-based dark mode (the design tokens in `index.css` are already structured for this).
- [ ] **Responsive / Mobile Layout** — Collapsible sidebar for tablet and mobile screen sizes.

---

## 🔴 Long-Term (Infrastructure & Scale)

### Deployment
- [ ] **Production Docker Setup** — Multi-stage Dockerfile with pre-baked embedding models; `docker-compose.local.yml` for local full-stack testing.
- [ ] **CI/CD Pipeline** — GitHub Actions workflow to run lint + type checks on PRs and auto-deploy to Railway/Render on merge to `main`.
- [ ] **Hosted Deployment** — Deploy backend to Railway/Render; frontend to Vercel or Cloudflare Pages.
- [ ] **Sentry Integration** — Add error tracking to both frontend (Sentry JS SDK) and backend (Sentry Python SDK).

### Database & Storage
- [ ] **pgvector for Semantic Search** — Replace in-memory vector store with a `pgvector`-powered PostgreSQL table for persistent document embeddings across sessions.
- [ ] **File Storage (S3/R2)** — Move uploaded files from local disk to S3-compatible object storage so the backend can scale horizontally.
- [ ] **Database Migrations Tool** — Replace the custom `migrations.py` script with Alembic for versioned, rollback-safe DB migrations.

### Model & AI
- [ ] **Model Selector UI** — Let users choose between multiple LLMs (e.g., Gemini Flash vs Pro, GPT-4o, Claude) per conversation.
- [ ] **RAG Evaluation Pipeline** — Integrate RAGAS or TruLens to measure retrieval quality (faithfulness, context recall) for every query.
- [ ] **Multimodal Output** — Allow the agent to generate and return images (e.g., charts from data) in its responses.
- [ ] **Agent Memory** — Implement long-term user-scoped memory (facts the user has stated) that persists across conversations.
- [ ] **Tool Expansion** — Add more executor workers: web search (Tavily), Wikipedia, code execution sandbox.

---

## 📝 Technical Debt

- [ ] Remove development-only `print` / `console.log` statements before production.
- [ ] Add type hints throughout all backend Python files.
- [ ] Write unit tests for core graph nodes (`planner`, `executor_worker`, `generate`).
- [ ] Write frontend component tests with Vitest + React Testing Library.
- [ ] Audit all hardcoded `localhost` URLs and replace with environment variables.

---

*Last updated: 2026-06-03*
