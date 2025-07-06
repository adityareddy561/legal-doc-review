# 📝 Legal Document Review RAG App

This project is an AI-powered legal document review tool using Retrieval-Augmented Generation (RAG).  
It lets users:
✅ Upload PDF legal documents (contracts, NDAs, agreements)  
✅ Extract, chunk, and embed the text  
✅ Store embeddings in a PostgreSQL vector database with `pgvector`  
✅ Generate a smart context-aware summary  
✅ Ask follow-up questions safely using semantic search and your LLM  
✅ Keep context isolated using session state

---

## 📂 **Project Structure**

```
legal-doc-review/
 ├── app.py              # FastAPI app with upload/query routes
 ├── db.py               # DB init script (pgvector & legal_chunks table)
 ├── templates/index.html # Frontend (Jinja2Templates)
 ├── static/style.css    # Stylesheet
 ├── .env                # Your environment variables
 ├── requirements.txt    # Python dependencies
```

---

## ⚙️ **Setup**

### ✅ 1. Clone the repo

```bash
git clone <your-repo-url>
cd legal-doc-review
```

---

### ✅ 2. Create & activate a virtual environment

```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

---

### ✅ 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## 🔑 **4. Create `.env`**

```env
OPENAI_API_KEY=<your-openai-key>
POSTGRES_CONNECTION=postgresql+psycopg://langchain:langchain@localhost:6024/langchain
```

---

## 🐘 **5. Start PostgreSQL + pgvector**

Run Postgres vector DB in Docker:

```bash
docker run --name pgvector-container   -e POSTGRES_USER=langchain   -e POSTGRES_PASSWORD=langchain   -e POSTGRES_DB=langchain   -p 6024:5432   -d pgvector/pgvector:pg16
```

Or use a `docker-compose.yml` if you prefer.

---

## 🗄️ **6. Initialize the DB**

Run:

```bash
python db.py
```

This will:

- Create the `vector` extension (`pgvector`)
- Create the `legal_chunks` table
- Add a composite index for fast retrieval

---

## ⚡ **7. Run the app**

Start your FastAPI server:

```bash
uvicorn app:app --reload
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## 💻 **How it works**

✅ **Upload**

- Upload a PDF → text is extracted, chunked, embedded with OpenAI embeddings.
- Chunks are stored in `pgvector` with `document_id` and `user_id` metadata.
- Server generates a summary using your LLM.
- `document_id` is stored in session so follow-ups use the right context.

✅ **Ask**

- You can ask multiple questions about the same doc.
- The vector store does semantic similarity search, filtering by `document_id` & `user_id`.
- The LLM only uses the retrieved chunks — if there’s no info, it says _“I don’t know.”_

✅ **Frontend**

- Simple upload & query form (`index.html`).
- Styled with `static/style.css`.
- Uses `SessionMiddleware` to keep context across requests.

---

## 🔐 **Session State**

Session cookies store your `document_id` & `user_id` so your queries never mix different uploads.

---

## 🧠 **Agentic AI vs. Basic RAG**

This project is classic RAG:

- Semantic search + rewriting.
- No tool-calling, fallback loops, or planning.

👉 For **Agentic AI**, you’d extend this with:

- Multi-step plans (e.g., fallback to regex if similarity fails)
- Conditional tool use (e.g., keyword search)
- Clarification loops with the user

---

## ✅ **Next Steps**

- [ ] Add fallback keyword/regex match for exact clause lookups.
- [ ] Add metadata: store `clause_number` for fast lookups.
- [ ] Add multi-user auth instead of `demo-user`.
- [ ] Add streaming response for large answers.
- [ ] Deploy to Railway, Render, or your favorite cloud.

---

## 🤝 **License**

MIT — use freely for learning and demos!

---

## 📬 **Questions?**

Open an issue or reach out!

---

**Built with ❤️ using FastAPI, LangChain, pgvector, and OpenAI.**
