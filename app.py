import os
import uuid
from collections import defaultdict
from typing import Dict, List, Literal, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# IMPORT z modułu z RAG-iem
from aws_form_assistant import answer_question

#
# === CONFIG ===
#
# Możesz nadpisać to zmiennymi środowiskowymi:
#   LLAMA_BASE_URL, LLAMA_MODEL_ID
#
BASE_URL = os.getenv(
    "LLAMA_BASE_URL",
    "http://lsd-llama-milvus-inline-service-collabothon.apps.cluster-qmfr5.qmfr5.sandbox265.opentlc.com",
)
MODEL_ID = os.getenv("LLAMA_MODEL_ID", "granite-31-8b")

app = FastAPI(
    title="LLM Chat API",
    description=(
        "Prosty FastAPI wrapper na Llama Stack (RAG AWS Form Assistant) "
        "z prostą historią rozmowy po stronie serwera."
    ),
    version="0.3.0",
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
    message: str = Field(..., description="Nowa wiadomość użytkownika.")
    conversation_id: Optional[str] = Field(
        default=None,
        description=(
            "Identyfikator konwersacji. Jeśli pusty, serwer utworzy nowy "
            "i zwróci go w odpowiedzi."
        ),
    )


class ChatResponse(BaseModel):
    answer: str
    model_id: str
    conversation_id: str = Field(
        ..., description="Id tej konwersacji – frontend powinien go zapamiętać."
    )


# Pamięć konwersacji w RAM-ie: conversation_id -> lista Message
ConversationHistory = List[Message]
conversation_store: Dict[str, ConversationHistory] = defaultdict(list)


def _append_to_history(
    conversation_id: str,
    user_message: Message,
    assistant_message: Message,
) -> None:
    """Zapisz parę (user, assistant) w historii i przytnij do MAX_HISTORY_MESSAGES."""
    history = conversation_store[conversation_id]
    history.append(user_message)
    history.append(assistant_message)

    # Przytnij historię do ostatnich N wiadomości
    if len(history) > MAX_HISTORY_MESSAGES:
        conversation_store[conversation_id] = history[-MAX_HISTORY_MESSAGES:]


# Funkcja _build_conversation_text() usunięta - nie jest już potrzebna
# Bo historię przekazujemy bezpośrednio do answer_question()


@app.get("/health")
def health_check() -> dict:
    """Prosty endpoint zdrowotny."""
    return {"status": "ok", "model_id": MODEL_ID, "base_url": BASE_URL}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """
    Główne wejście dla frontendu / klienta.

    Przyjmuje:
    - `message`: aktualne pytanie użytkownika,
    - `conversation_id`: opcjonalny identyfikator konwersacji (session / chat id).

    Zwraca:
    - `answer`: odpowiedź LLM,
    - `conversation_id`: id konwersacji, które frontend powinien zapamiętać
      i przesyłać przy kolejnych zapytaniach.
    """
    # 1) Ustal conversation_id (nowy albo istniejący)
    if request.conversation_id:
        conversation_id = request.conversation_id
    else:
        conversation_id = str(uuid.uuid4())

    history = conversation_store[conversation_id]

    # 2) Bieżąca wiadomość usera (model Message)
    user_msg = Message(role="user", content=request.message)

    # 3) Wywołaj RAG-owego AWS Form Assistanta
    #    Przekazujemy samą wiadomość (dla RAG query) + historię (dla LLM)
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

    # 5) Zapisz do historii
    _append_to_history(conversation_id, user_msg, assistant_msg)

    # 6) Zwróć odpowiedź + conversation_id
    return ChatResponse(
        answer=answer_text,
        model_id=MODEL_ID,
        conversation_id=conversation_id,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8080")),
        reload=True,
    )
