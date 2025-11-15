import uuid
from collections import defaultdict
from typing import Dict, List, Literal, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel, Field

from aws_form_assistant import answer_question
from config import get_settings

settings = get_settings()

app = FastAPI(
    title="LLM Chat API",
    description=(
        "FastAPI wrapper around the Llama Stack AWS form assistant with simple "
        "server-side conversation history."
    ),
    version="0.3.0",
)

origins = [
    settings.frontend_origin
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ====== KONFIG HISTORII ======

SYSTEM_PROMPT = (
    "You are an AWS solutions assistant for non-technical customers. "
    "Use the conversation history to keep context."
)

# Ile ostatnich wiadomości trzymać (łącznie: user + assistant)
MAX_HISTORY_MESSAGES = 20


class Message(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    message: str = Field(..., description="Latest user message.")
    conversation_id: Optional[str] = Field(
        default=None,
        description="Conversation identifier. Leave empty to start a new chat.",
    )


class ChatResponse(BaseModel):
    answer: str
    model_id: str
    conversation_id: str = Field(
        ..., description="Conversation identifier that the client must store."
    )


ConversationHistory = List[Message]
conversation_store: Dict[str, ConversationHistory] = defaultdict(list)


def _append_to_history(
    conversation_id: str,
    user_message: Message,
    assistant_message: Message,
) -> None:
    """Persist a (user, assistant) message pair and trim the stored history."""
    history = conversation_store[conversation_id]
    history.append(user_message)
    history.append(assistant_message)

    if len(history) > settings.max_history_messages:
        conversation_store[conversation_id] = history[-settings.max_history_messages :]


@app.get("/health")
def health_check() -> dict:
    """Expose a simple health endpoint for readiness probes."""
    return {
        "status": "ok",
        "model_id": settings.model_id,
        "base_url": settings.base_url,
    }


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """
    Primary entrypoint for the chat frontend or API clients.

    Accepts:
    - `message`: the latest user utterance
    - `conversation_id`: optional conversation identifier (session / chat id)

    Returns:
    - `answer`: LLM response
    - `conversation_id`: identifier to be reused on subsequent turns
    """
    if request.conversation_id:
        conversation_id = request.conversation_id
    else:
        conversation_id = str(uuid.uuid4())

    history = conversation_store[conversation_id]

    user_msg = Message(role="user", content=request.message)

    try:
        answer_text = answer_question(
            current_message=request.message,
            conversation_history=history,
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=502,
            detail="LLM backend timed out. Please retry in a moment.",
        ) from exc

    assistant_msg = Message(role="assistant", content=answer_text)

    _append_to_history(conversation_id, user_msg, assistant_msg)

    return ChatResponse(
        answer=answer_text,
        model_id=settings.model_id,
        conversation_id=conversation_id,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=settings.api_port,
        reload=True,
    )
