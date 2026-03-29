from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from phi.agent import Agent
from phi.model.ollama import Ollama
from phi.storage.agent.postgres import PgAgentStorage
from phi.knowledge.pdf import PDFKnowledgeBase
from phi.vectordb.pgvector import PgVector2
from phi.embedder.ollama import OllamaEmbedder
import os
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Read DB URL from environment (Render injects DATABASE_URL automatically).
# phi/pgvector requires the psycopg driver prefix: postgresql+psycopg://
_raw_db_url = os.getenv("DATABASE_URL", "postgresql+psycopg://ai:ai@localhost:5532/ai")
db_url = _raw_db_url.replace("postgresql://", "postgresql+psycopg://", 1)

# OLLAMA host (defaults to localhost:11434 if not set)
ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")

knowledge_base = PDFKnowledgeBase(
    path="CetaphilBabySkinCare.pdf",
    vector_db=PgVector2(
        collection="cetaphil",
        db_url=db_url,
        embedder=OllamaEmbedder(
            model="nomic-embed-text",
            host=ollama_host,
            dimensions=768,  # nomic-embed-text output size
        ),
    ),
)
knowledge_base.load(recreate=True)

storage = PgAgentStorage(table_name="pdf_agent", db_url=db_url)

agent = Agent(
    user_id="react_user",
    model=Ollama(id="llama3.1", host=ollama_host),
    knowledge=knowledge_base,
    storage=storage,
    search_knowledge=True,
    read_chat_history=True,
    instructions=[
        "You are an expert dermatologist specialized in Cetaphil products and baby skincare.",
        "Respond in a warm, polite, and reassuring tone suitable for speaking with parents and caregivers.",
        "Greet the user when appropriate and acknowledge their concerns about their baby's skin.",
        "Provide clear, accurate, and concise information based on the Cetaphil Baby Skincare knowledge base.",
        "Keep responses short (2-3 sentences) but highly practical and helpful.",
        "Address queries regarding baby skincare routines, common skin issues, and recommend appropriate Cetaphil products.",
        "If the information is not available in the knowledge base, politely state so and suggest they consult their pediatrician for personalized medical advice.",
        "Avoid overly complex medical jargon and explain concepts in a way that parents can easily understand.",
        "Always maintain a respectful, caring, and professional tone.",
    ],
)


# Request model
class Message(BaseModel):
    query: str


@app.post("/chat")
async def chat_with_pdf(msg: Message):
    try:
        print(f"Received query: {msg.query}")

        run_response = agent.run(msg.query)

        # phidata v2: RunResponse has a .content attribute
        if hasattr(run_response, "content") and run_response.content:
            full_text = run_response.content
        else:
            # Fallback: iterate if it's a generator
            full_text = ""
            for chunk in run_response:
                if hasattr(chunk, "content") and chunk.content:
                    full_text += chunk.content
                elif isinstance(chunk, str):
                    full_text += chunk

        full_text = full_text.strip()
        print(f"Agent response: {full_text}")
        return {"response": full_text or "No response generated."}

    except Exception as e:
        print("❌ Error:", e)
        return {"error": str(e)}


@app.post("/chat/stream")
async def chat_stream(msg: Message):
    """
    Server-Sent Events streaming endpoint.
    Each token is sent as:  data: <token>\n\n
    A final  data: [DONE]\n\n  marks the end of the stream.
    """
    async def event_generator():
        try:
            print(f"[stream] Received query: {msg.query}")
            response_gen = agent.run(msg.query, stream=True)

            for chunk in response_gen:
                token = ""
                if hasattr(chunk, "content") and chunk.content:
                    token = chunk.content
                elif isinstance(chunk, str):
                    token = chunk

                if token:
                    yield f"data: {token}\n\n"

            yield "data: [DONE]\n\n"

        except Exception as e:
            print("❌ Stream error:", e)
            yield f"data: [ERROR] {str(e)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
