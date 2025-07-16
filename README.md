# pdf-chatbot
AI-powered chatbot that answers natural language questions based on the content of a PDF using vector search and LLMs (Groq/OpenAI). Built with FastAPI, pgvector, and Phi.

🛠️ Prerequisites
Python 3.10+ installed

Docker installed and running

Git (optional)

Internet connection

✅ Step 1: Clone or Copy the Code
bash

git clone <your-repo-url> pdf-chatbot
cd pdf-chatbot
Or manually copy server.py and related files.

✅ Step 2: Create Virtual Environment and Install Dependencies
bash
 
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
If no requirements.txt, create one manually:

txt
 
fastapi
uvicorn
python-dotenv
phi
✅ Step 3: Set Up Environment Variables
Create a .env file in the root folder:

env

GROQ_API_KEY=sk-xxxxxx   # Replace with your key
OPENAI_API_KEY=sk-xxxxxx # Optional, in case you're using OpenAI
✅ Step 4: Get Your API Keys
🔑 Get Groq API Key
Go to https://console.groq.com/

Sign in or sign up.

Navigate to API Keys.

Generate and copy the key.

Paste into your .env.

🔑 Get OpenAI API Key (if needed)
Go to https://platform.openai.com/

Create an account.

Visit https://platform.openai.com/api-keys

Generate a key and copy it.

Paste into your .env.

✅ Step 5: Run PostgreSQL + pgvector via Docker
bash
 
docker run --name pgvector \
  -e POSTGRES_USER=ai \
  -e POSTGRES_PASSWORD=ai \
  -e POSTGRES_DB=ai \
  -p 5532:5432 \
  -d ankane/pgvector
You can check logs:

bash
 
docker logs -f pgvector
✅ Step 6: Load PDF into Vector DB (Automatically Handled)
In your code:

python
 
knowledge_base = PDFKnowledgeBase(
    path="ThaiRecipes.pdf",
    vector_db=PgVector2(collection="recipes", db_url=db_url),
)
When the app runs the first time, the PDF will be loaded into the vector DB using pgvector (as long as the recipes collection doesn't already exist).

📌 Make sure ThaiRecipes.pdf is placed in the project root.

✅ Step 7: Run the App
bash
 
uvicorn server:app --reload
You should see:

nginx
 
Uvicorn running on http://127.0.0.1:8000
✅ Step 8: Test the Endpoint
Run this in your terminal:

bash
 
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "What recipes use coconut milk?"}'
Expected result:

json
 
{"response":"Coconut milk is used in Thai green curry and some soups."}
(Response may vary based on your PDF content)

📂 Directory Structure Example

bash
 
pdf-chatbot/

├── .env

├── server.py

├── ThaiRecipes.pdf

├── requirements.txt

└── .venv/


bash
 
pip install -r requirements.txt
💡 Notes
On first run, PDFKnowledgeBase loads & indexes the file.

No need to run any manual SQL for vector; PgVector2 handles it.
