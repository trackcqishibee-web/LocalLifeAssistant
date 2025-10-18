from fastapi import APIRouter, HTTPException
from typing import List
from ..models import ChatRequest, ChatResponse, ChatMessage
from ..rag_engine import RAGEngine
from datetime import datetime

router = APIRouter(prefix="/api", tags=["chat"])

# Initialize RAG engine
rag_engine = RAGEngine()

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint for conversational recommendations
    """
    try:
        # Get LLM provider from request or use default
        llm_provider = request.llm_provider or "openai"
        
        # Get response and recommendations
        response, recommendations = await rag_engine.chat_with_context(
            message=request.message,
            conversation_history=request.conversation_history,
            llm_provider=llm_provider
        )
        
        return ChatResponse(
            message=response,
            recommendations=recommendations,
            llm_provider_used=llm_provider
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat request: {str(e)}")

@router.post("/chat/simple")
async def simple_chat(message: str, llm_provider: str = "openai"):
    """
    Simplified chat endpoint for basic queries
    """
    try:
        response, recommendations = await rag_engine.get_recommendations(
            query=message,
            llm_provider=llm_provider
        )
        
        return {
            "message": response,
            "recommendations": [
                {
                    "type": rec.type,
                    "data": rec.data.dict(),
                    "relevance_score": rec.relevance_score,
                    "explanation": rec.explanation
                }
                for rec in recommendations
            ],
            "llm_provider_used": llm_provider
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing simple chat: {str(e)}")
