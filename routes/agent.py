from fastapi import APIRouter, HTTPException, Header, Request
from pydantic import BaseModel
from typing import List, Optional
from services.workflow import app, AgentState
from utils import serialize_mongo_obj

router = APIRouter(prefix="/agent", tags=["AI Agent"])

class ChatRequest(BaseModel):
    query: str
    history: List[dict] = []

@router.post("/chat")
async def chat_endpoint(request: ChatRequest, authorization: Optional[str] = Header(None)):
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
    
    # Initialize State
    initial_state: AgentState = {
        "query": request.query,
        "chat_history": request.history,
        "token": token,
        "user_info": None,
        "intent": None,
        "product": None,
        "quantity": 1,
        "address": None,
        "payment_method": None,
        "messages": [],
        "next_step": None
    }
    
    try:
        # Run the graph
        final_state = app.invoke(initial_state)
        
        return {
            "messages": final_state.get("messages", []),
            "next_step": final_state.get("next_step"),
            "data": {
                "product": serialize_mongo_obj(final_state.get("product")),
                "order_status": "created" if final_state.get("next_step") == "end" else None
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
