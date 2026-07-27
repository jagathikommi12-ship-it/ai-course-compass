from fastapi import APIRouter, Depends

from app.agent.claude_agent import DegreeNavigatorAgent
from app.auth import CurrentUser, get_current_user
from app.models import ChatMessageIn, ChatMessageOut

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/chat", response_model=ChatMessageOut)
def chat(body: ChatMessageIn, user: CurrentUser = Depends(get_current_user)):
    """
    Single-turn chat endpoint used by both the React chat widget and the
    Gradio app — both authenticate the same way (Supabase JWT), so the
    agent gives personalized answers ("you still need...") in either
    frontend without any extra wiring.
    """
    agent = DegreeNavigatorAgent(user_id=user.user_id)
    reply = agent.chat(body.message)
    return ChatMessageOut(reply=reply)
