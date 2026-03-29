# pdf-chatbot (OLLAMA Edition)

AI-powered chatbot that answers natural language questions based on the content of a PDF using vector search and a **100% local** LLM. Built with FastAPI, pgvector, phidata, and OLLAMA — **no API keys, no cloud costs**.

---

## Prerequisites

| Tool | Minimum Version |
|------|----------------|
| Python | 3.10+ |
| Docker | Any recent version |
| [OLLAMA](https://ollama.com/download) | Latest |

---

## Step 1 — Install OLLAMA and Pull Models

```bash
# macOS
brew install ollama

# Start the OLLAMA server (keep this running in a separate terminal)
ollama serve

# Pull the chat model (llama3.1 supports the tool-calling required for knowledge)
ollama pull llama3.1

# Pull the embedding model (used to index your PDF)
ollama pull nomic-embed-text
```

---

## Step 2 — Clone the Repo and Set Up Virtual Environment

```bash
git clone https://github.com/anoopbajpaipublic/pdf-chatbot.git
cd pdf-chatbot

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

---

## Step 3 — Configure Environment Variables

```bash
cp dot-env.sample .env
```

The defaults work out of the box with the Docker setup below. Edit `.env` only if your setup differs:

```env
OLLAMA_HOST=http://localhost:11434
DATABASE_URL=postgresql+psycopg://ai:ai@localhost:5532/ai
```

---

## Step 4 — Start PostgreSQL + pgvector via Docker

```bash
docker run --name pgvector \
  -e POSTGRES_USER=ai \
  -e POSTGRES_PASSWORD=ai \
  -e POSTGRES_DB=ai \
  -p 5532:5432 \
  -d ankane/pgvector
```

---

## Step 5 — Add Your PDF

Place your PDF in the project root. The default file is `CetaphilBabySkinCare.pdf`.  
To use a different file, update the `path=` argument in `server.py`.

---

## Step 6 — Run the App

```bash
uvicorn server:app --reload
```

On first run the PDF is automatically chunked, embedded with `nomic-embed-text`, and stored in pgvector. Subsequent runs reuse the stored embeddings.

---

## Step 7 — Test the Endpoints

### Non-streaming chat

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the cancellation policy?"}'
```

Expected:

```json
{"response": "United Airlines allows cancellations within 24 hours..."}
```

### Streaming chat (SSE)

```bash
curl -N -X POST http://localhost:8000/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"query": "How do I check in online?"}'
```

Tokens stream back in real-time, ending with `data: [DONE]`.

---

## Directory Structure

```
pdf-chatbot/
├── .env
├── dot-env.sample
├── server.py
├──CetaphilBabySkinCare.pdf
├── requirements.txt
└── .venv/
```

---

## Notes

- **First run**: PDF is loaded and indexed automatically (`recreate=False` skips re-indexing on subsequent starts).
- **No API keys needed**: Everything runs locally via OLLAMA.
- **Switch models**: Change `id="llama3"` in `server.py` to any model you have pulled locally (e.g. `llama3.2`, `mistral`, `gemma3`).
