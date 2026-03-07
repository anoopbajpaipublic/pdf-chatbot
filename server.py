from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from phi.assistant import Assistant
from phi.storage.assistant.postgres import PgAssistantStorage
from phi.knowledge.pdf import PDFKnowledgeBase
from phi.vectordb.pgvector import PgVector2
import os
import json
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or replace with [\"http://localhost:3000\"] for security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")
db_url = "postgresql+psycopg://ai:ai@localhost:5532/ai"

knowledge_base = PDFKnowledgeBase(
    path="faq.pdf",
    vector_db=PgVector2(collection="faq", db_url=db_url),
)
knowledge_base.load(recreate=False)
storage = PgAssistantStorage(table_name="pdf_assistant", db_url=db_url)

assistant = Assistant(
    user_id="react_user",
    knowledge_base=knowledge_base,
    storage=storage,
    search_knowledge=True,
    read_chat_history=True,
    instructions=[
        "You are a friendly and professional customer care representative for United Airlines.",
        "Respond in a polite, supportive, and professional tone similar to airline customer support.",
        "Greet the customer when appropriate and acknowledge their request.",
        "Provide clear, accurate, and concise information based on the United Airlines FAQ knowledge base.",
        "Keep responses short (2–3 sentences) but helpful.",
        "If the question is about flight booking, cancellation, refund, baggage, or check-in, guide the customer clearly on what they can do next.",
        "If the information is not available in the knowledge base, politely say you are unable to find that information and suggest contacting United Airlines support.",
        "Avoid technical language and respond in a way that regular passengers can easily understand.",
        "Always maintain a respectful and customer-focused tone."
    ]
)


# Request model
class Message(BaseModel):
    query: str

 
@app.post("/chat")
async def chat_with_pdf(msg: Message):
    try:
        print(f"Received query: {msg.query}")
        
        response_gen = assistant.run(msg.query)
        full_text = ""

        for step in response_gen:
            if hasattr(step, "message") and hasattr(step.message, "content"):
                full_text += step.message.content
            elif isinstance(step, str):
                full_text += step
            else:
                print("⚠️ Unrecognized step:", step)

        full_text = full_text.strip()

        print(f"Assistant response: {full_text}")
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
            response_gen = assistant.run(msg.query, stream=True)

            for chunk in response_gen:
                token = ""
                if hasattr(chunk, "message") and hasattr(chunk.message, "content"):
                    token = chunk.message.content or ""
                elif isinstance(chunk, str):
                    token = chunk

                if token:
                    # SSE format
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
