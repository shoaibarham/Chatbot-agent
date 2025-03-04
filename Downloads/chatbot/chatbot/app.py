from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from agent import DatabaseAgent
import uvicorn


agent = DatabaseAgent(db_path='gtfs.db', model_name='gemini-2.0-flash')

app = FastAPI(
    title="GTFS Database Chat Agent",
    description="A conversational agent for querying GTFS database",
    version="0.1.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    query: str
    session_id: Optional[str] = 'default'

class ChatResponse(BaseModel):
    response: str
    session_id: str

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Endpoint for processing chat queries with optional session tracking.
    
    :param request: Chat request containing query and optional session ID
    :return: Chat response with agent's output
    """
    try:
        response = agent.query(
            input_text=request.query, 
            session_id=request.session_id or 'default'
        )
        
        return ChatResponse(
            response=response, 
            session_id=request.session_id or 'default'
        )
    
    except Exception as e:
        return ChatResponse(
            response=f"An error occurred: {str(e)}", 
            session_id=request.session_id or 'default'
        )

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)