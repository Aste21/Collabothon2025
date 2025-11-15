from typing import List, Dict, Any
from pathlib import Path

from llama_stack_client import LlamaStackClient, RAGDocument

# ==== CONFIG – dostosuj do swojego środowiska ====
BASE_URL = "http://lsd-llama-milvus-inline-service-collabothon.apps.cluster-qmfr5.qmfr5.sandbox265.opentlc.com"
VECTOR_DB_ID = "form_helper_db"  # ten sam co w rag_seed_aws.py
LLM_ID = "granite-31-8b"  # z client.models.list()
LLM_TEMPERATURE = 0
# ================================================


client = LlamaStackClient(base_url=BASE_URL)

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


def answer_question(
    current_message: str, conversation_history: List[Dict[str, str]]
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

    system_prompt = f"""You are an AWS solutions assistant for non-technical customers.
The user will describe a system they want to build.
Your job is to:
1) Restate their requirements in simple terms.
2) Propose an AWS-based architecture (components + AWS services).
3) Provide a rough monthly cost estimate in clearly labeled tiers,
   based on the scale described (small / medium / large).
4) Explain why this approach on AWS is a good fit.
If you lack key details (like number of users or traffic), ask a short clarification question first.
Always answer in clear, friendly English.

Here is relevant AWS knowledge base context for this question:
{context_text}
"""

    # Budujemy messages array z pełną historią
    messages: List[Dict[str, Any]] = [{"role": "system", "content": system_prompt}]

    # Dodaj całą historię rozmowy
    for msg in conversation_history:
        messages.append(
            {
                "role": msg["role"] if isinstance(msg, dict) else msg.role,
                "content": msg["content"] if isinstance(msg, dict) else msg.content,
            }
        )

    # Dodaj aktualną wiadomość użytkownika
    messages.append({"role": "user", "content": current_message})

    completion = client.chat.completions.create(
        model=LLM_ID,
        messages=messages,
        temperature=LLM_TEMPERATURE,
    )

    answer_text = completion.choices[0].message.content
    return answer_text
