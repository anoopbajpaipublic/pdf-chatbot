from fastapi import FastAPI, Request
from pydantic import BaseModel
from phi.assistant import Assistant
from phi.storage.assistant.postgres import PgAssistantStorage
from phi.knowledge.pdf import PDFKnowledgeBase
from phi.vectordb.pgvector import PgVector2
import os
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or replace with ["http://localhost:3000"] for security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")
db_url = "postgresql+psycopg://ai:ai@localhost:5532/ai"

knowledge_base = PDFKnowledgeBase(
    path="ThaiRecipes.pdf",
    vector_db=PgVector2(collection="recipes", db_url=db_url),
)
storage = PgAssistantStorage(table_name="pdf_assistant", db_url=db_url)

assistant = Assistant(
    user_id="react_user",
    knowledge_base=knowledge_base,
    storage=storage,
    search_knowledge=True,
    read_chat_history=True,
    instructions=[
        "Reply briefly with one or two lines of clear and useful information only. "
        "Avoid long explanations or unnecessary details."
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
