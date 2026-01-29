"""
FastAPI wrapper for the RAG Chatbot application.
This allows the application to run as a web service on Railpack.
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(
    title="WikiChatbot RAG API",
    description="RAG-based chatbot for Vietnamese Wikipedia content",
    version="1.0.0"
)

# Global RAG instance (lazy loaded)
rag_instance = None

class ChatRequest(BaseModel):
    question: str
    verbose: Optional[bool] = False

class ChatResponse(BaseModel):
    question: str
    answer: str
    status: str

def get_rag_instance():
    """Lazy load RAG instance"""
    global rag_instance
    if rag_instance is None:
        try:
            from src.rag_chat import RAGChat
            rag_instance = RAGChat(
                collection_name="knowledge_base",
                persist_directory="data/chroma_db",
                model_name="gemini-2.5-flash-lite",
                temperature=0.1,
                top_k=10,
                bm25_weight=0.5,
                semantic_weight=0.5
            )
            print("✅ RAG instance initialized successfully")
        except Exception as e:
            print(f"❌ Error initializing RAG: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to initialize RAG: {str(e)}")
    return rag_instance

@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint with HTML interface"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>WikiChatbot RAG API</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 50px auto;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .container {
                background-color: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            h1 {
                color: #333;
                border-bottom: 3px solid #4CAF50;
                padding-bottom: 10px;
            }
            .endpoint {
                background-color: #f9f9f9;
                padding: 15px;
                margin: 10px 0;
                border-left: 4px solid #4CAF50;
                border-radius: 4px;
            }
            .method {
                display: inline-block;
                padding: 4px 8px;
                background-color: #4CAF50;
                color: white;
                border-radius: 4px;
                font-weight: bold;
                margin-right: 10px;
            }
            .method.get {
                background-color: #2196F3;
            }
            code {
                background-color: #f4f4f4;
                padding: 2px 6px;
                border-radius: 3px;
                font-family: monospace;
            }
            a {
                color: #4CAF50;
                text-decoration: none;
            }
            a:hover {
                text-decoration: underline;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 WikiChatbot RAG API</h1>
            <p>Welcome to the RAG-based chatbot for Vietnamese Wikipedia content!</p>
            
            <h2>📚 Available Endpoints:</h2>
            
            <div class="endpoint">
                <span class="method get">GET</span>
                <code>/</code> - This page
            </div>
            
            <div class="endpoint">
                <span class="method get">GET</span>
                <code>/health</code> - Health check endpoint
            </div>
            
            <div class="endpoint">
                <span class="method">POST</span>
                <code>/chat</code> - Chat with the RAG system
                <br><br>
                <strong>Request body:</strong>
                <pre>{
  "question": "Your question here",
  "verbose": false
}</pre>
            </div>
            
            <div class="endpoint">
                <span class="method get">GET</span>
                <code>/docs</code> - Interactive API documentation (Swagger UI)
            </div>
            
            <h2>🔗 Quick Links:</h2>
            <ul>
                <li><a href="/docs">📖 API Documentation (Swagger UI)</a></li>
                <li><a href="/redoc">📘 API Documentation (ReDoc)</a></li>
                <li><a href="/health">💚 Health Check</a></li>
            </ul>
            
            <h2>💡 Example Usage:</h2>
            <pre>curl -X POST "http://localhost:8000/chat" \\
  -H "Content-Type: application/json" \\
  -d '{"question": "Hồ Chí Minh sinh năm nào?"}'</pre>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/health")
async def health_check():
    """Health check endpoint with detailed status"""
    import os.path
    
    gemini_key = os.getenv("GEMINI_API_KEY")
    vector_db_path = "data/chroma_db"
    chunks_file = os.path.join(vector_db_path, "knowledge_base_chunks.pkl")
    
    # Check vector database
    vector_db_exists = os.path.exists(vector_db_path)
    chroma_db_exists = os.path.exists(os.path.join(vector_db_path, "chroma.sqlite3"))
    chunks_file_exists = os.path.exists(chunks_file)
    
    # Overall health status
    is_healthy = (
        bool(gemini_key and gemini_key != "your_gemini_api_key_here") and
        vector_db_exists and
        chroma_db_exists and
        chunks_file_exists
    )
    
    return {
        "status": "healthy" if is_healthy else "unhealthy",
        "service": "WikiChatbot RAG API",
        "checks": {
            "gemini_api_configured": bool(gemini_key and gemini_key != "your_gemini_api_key_here"),
            "vector_db_directory_exists": vector_db_exists,
            "chroma_db_exists": chroma_db_exists,
            "chunks_file_exists": chunks_file_exists
        },
        "vector_db_path": vector_db_path,
        "message": "All systems operational" if is_healthy else "Some components are missing. Please initialize the database."
    }

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat endpoint - Ask questions and get answers from the RAG system
    
    - **question**: Your question in Vietnamese
    - **verbose**: Set to true to see retrieved context (optional)
    """
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    
    try:
        rag = get_rag_instance()
        answer = rag.chat(request.question, verbose=request.verbose)
        
        return ChatResponse(
            question=request.question,
            answer=answer,
            status="success"
        )
    except FileNotFoundError as e:
        error_detail = (
            "Vector database not found. "
            "Please initialize the database first by running: "
            "POST /initialize or running the init_db.py script. "
            f"Details: {str(e)}"
        )
        print(f"❌ FileNotFoundError: {error_detail}")
        raise HTTPException(status_code=404, detail=error_detail)
    except RuntimeError as e:
        error_detail = f"Runtime error: {str(e)}"
        print(f"❌ RuntimeError: {error_detail}")
        raise HTTPException(status_code=500, detail=error_detail)
    except Exception as e:
        error_detail = f"Unexpected error: {str(e)}"
        print(f"❌ Exception: {error_detail}")
        raise HTTPException(status_code=500, detail=error_detail)

@app.get("/info")
async def info():
    """Get information about the RAG system configuration"""
    return {
        "model": "gemini-2.5-flash-lite",
        "collection_name": "knowledge_base",
        "persist_directory": "data/chroma_db",
        "top_k": 10,
        "bm25_weight": 0.5,
        "semantic_weight": 0.5,
        "embedding_model": os.getenv("EMBEDDING_MODEL_NAME", "models/text-embedding-004")
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
