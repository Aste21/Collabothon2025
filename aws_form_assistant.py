import logging
from typing import List, Dict, Any, Sequence, Tuple, Union
from pathlib import Path

from llama_stack_client import LlamaStackClient, RAGDocument

# ==== CONFIG – dostosuj do swojego środowiska ====
BASE_URL = "http://lsd-llama-milvus-inline-service-collabothon.apps.cluster-qmfr5.qmfr5.sandbox265.opentlc.com"
VECTOR_DB_ID = "form_helper_db"  # ten sam co w rag_seed_aws.py
LLM_ID = "granite-31-8b"  # z client.models.list()
LLM_TEMPERATURE = 0
# ================================================


client = LlamaStackClient(base_url=BASE_URL)
logger = logging.getLogger(__name__)

try:
    base_path = Path(__file__).parent
except NameError:
    base_path = Path.cwd()

AWS_KB_PATH = base_path / "aws_architecture_kb.md"


def _build_context(user_question: str) -> str:
    """Run RAG query and build context string for the LLM."""
    rag_result = client.tool_runtime.rag_tool.query(
        content=user_question,
        vector_db_ids=[VECTOR_DB_ID],
    )

    chunks: List[str] = []
    matches = getattr(rag_result, "matches", []) or []
    for match in matches:
        doc = getattr(match, "document", None)
        content = getattr(doc, "content", None) if doc is not None else None
        if isinstance(content, str) and content:
            chunks.append(content)

    if not chunks:
        return "No extra AWS context was retrieved."

    # we keep first few chunks to avoid overly long prompt
    return "\n\n---\n\n".join(chunks[:3])


MessageLike = Union[Dict[str, str], Any]


def _normalize_message(msg: MessageLike) -> Tuple[str, str]:
    """Return (role, content) tuple regardless of incoming object type."""
    if isinstance(msg, dict):
        role = msg.get("role", "user")
        content = msg.get("content", "")
    else:
        role = getattr(msg, "role", "user")
        content = getattr(msg, "content", "")
    return role, content


def _build_conversation_text(
    conversation_history: Sequence[MessageLike], current_message: str
) -> str:
    """Serialize conversation history + current user message."""
    parts: List[str] = []

    for msg in conversation_history:
        role, content = _normalize_message(msg)
        if role == "assistant":
            prefix = "Assistant"
        elif role == "system":
            prefix = "System"
        else:
            prefix = "User"
        parts.append(f"{prefix}: {content}")

    parts.append(f"User: {current_message}")
    return "\n\n".join(parts)


def answer_question(
    current_message: str, conversation_history: Sequence[MessageLike]
) -> str:
    """Answer a user question about AWS using RAG + conversation history.

    Args:
        current_message: The current user message (used for RAG query)
        conversation_history: List of previous messages (dicts with 'role' and 'content')

    Returns:
        The assistant's answer
    """
    # RAG query używa TYLKO aktualnej wiadomości
    context_text = _build_context(current_message)
    conversation_text = _build_conversation_text(
        conversation_history or [], current_message=current_message
    )

    system_prompt = """You are an AWS solutions assistant for non-technical customers.
The user will describe a system they want to build.
Your job is to:
1) Restate their requirements in simple terms.
2) Propose an AWS-based architecture (components + AWS services).
3) Provide a rough monthly cost estimate in clearly labeled tiers,
   based on the scale described (small / medium / large).
4) Explain why this approach on AWS is a good fit.
If you lack key details (like number of users or traffic), ask a short clarification question first.
Always answer in clear, friendly English.

"""

    user_message = (
        "Context from AWS knowledge base:\n"
        f"{context_text}\n\n"
        "Conversation so far:\n"
        f"{conversation_text}\n\n"
        "Please respond to the latest user request. If details are missing, ask a short "
        "clarifying question before proposing an architecture."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]

    try:
        completion = client.chat.completions.create(
            model=LLM_ID,
            messages=messages,
            temperature=LLM_TEMPERATURE,
        )
    except Exception as exc:  # pragma: no cover - network layer
        logger.exception("LLM completion request failed")
        raise RuntimeError("LLM backend request failed") from exc

    answer_text = completion.choices[0].message.content
    return answer_text
