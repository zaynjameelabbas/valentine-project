from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import os
import requests
from typing import List, Dict
from fastapi.staticfiles import StaticFiles 

# Import the RAG logic from your local file
from rag_pipeline import ingest_documents, query_protocol

app = FastAPI(
    title="Iron & Spine Clinic API",
    description="High-performance RAG API for Dr. Jay Toor's surgical protocols.",
    version="1.0.0"
)

# Enable CORS so your frontend (localhost:5500) can talk to this API (localhost:8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serves the PDFs in the /data folder so the browser can display them
app.mount("/data", StaticFiles(directory="data"), name="data")

class ChatRequest(BaseModel):
    procedure_id: str
    query: str
    chat_history: List[Dict[str, str]] = []

@app.post("/api/chat", summary="Query a specific performance protocol")
def chat_with_protocol(request: ChatRequest):
    try:
        print(f"Processing {request.procedure_id} query: '{request.query}'...")
        
        # Calls RAG pipeline with the history and specific procedure ID
        answer = query_protocol(request.query, request.procedure_id, request.chat_history)      

        return {
            "status": "success",
            "procedure_id": request.procedure_id,
            "response": answer
        }
        
    except Exception as e:
        print(f"Error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while processing the request.")

@app.on_event("startup")
async def startup_event():
    """Runs automatically when the server starts."""
    db_path = "./vector_store/chroma.sqlite3"
    
    # 1. Ensure the database is built from the PDFs
    if not os.path.exists(db_path):
        print("Database not found. Initializing protocol ingestion...")
        success = ingest_documents()
        if success:
            print("Protocol database built successfully.")
    else:
        print("Protocol database online.")

    # 2. Verify connection to the local Ollama instance
    try:
        response = requests.get("http://localhost:11434/api/tags")
        if response.status_code == 200:
            print("Local Ollama connection verified.")
    except Exception as e:
        print(f"CRITICAL: Could not reach local Ollama: {e}")
    
@app.get("/health")
def health_check():
    """Quick endpoint to verify system status."""
    db_exists = os.path.exists("./vector_store/chroma.sqlite3")
    return {
        "status": "online", 
        "database_ready": db_exists,
        "clinic_name": "Iron & Spine"
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

# HUGGING FACE
# from fastapi import FastAPI, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel
# import uvicorn
# import os
# from typing import List, Dict
# from fastapi.staticfiles import StaticFiles 

# from rag_pipeline import ingest_documents, query_protocol

# app = FastAPI(title="Iron & Spine Clinic API")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"], 
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # 1. Mount Data (PDFs)
# app.mount("/data", StaticFiles(directory="data"), name="data")

# # 2. Mount Frontend (Must come AFTER specific API routes if you have conflicts, but here is fine)
# # By setting html=True, FastAPI will automatically serve index.html when someone visits the root URL.
# app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

# class ChatRequest(BaseModel):
#     procedure_id: str
#     query: str
#     chat_history: List[Dict[str, str]] = []

# @app.post("/api/chat")
# def chat_with_protocol(request: ChatRequest):
#     try:
#         answer = query_protocol(request.query, request.procedure_id, request.chat_history)      
#         return {
#             "status": "success",
#             "procedure_id": request.procedure_id,
#             "response": answer
#         }
#     except Exception as e:
#         print(f"Error occurred: {e}")
#         raise HTTPException(status_code=500, detail="Internal server error.")

# @app.on_event("startup")
# async def startup_event():
#     db_path = "./vector_store/chroma.sqlite3"
#     if not os.path.exists(db_path):
#         print("Database not found. Initializing protocol ingestion...")
#         ingest_documents()
#     else:
#         print("Protocol database online.")
#     # Removed Ollama health check since we are using Groq API now

# # Change the run configuration to use host 0.0.0.0 and port 7860 for Hugging Face
# if __name__ == "__main__":
#     uvicorn.run("main:app", host="0.0.0.0", port=7860)