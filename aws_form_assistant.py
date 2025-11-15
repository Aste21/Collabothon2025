import json
import logging
from typing import List, Dict, Any, Sequence, Tuple, Union
from pathlib import Path

from llama_stack_client import LlamaStackClient, RAGDocument

# ==== CONFIG – dostosuj do swojego środowiska ====
BASE_URL = "http://lsd-llama-milvus-inline-service-collabothon.apps.cluster-qmfr5.qmfr5.sandbox265.opentlc.com"
VECTOR_DB_ID = "form_helper_db"  # ten sam co w rag_seed_aws.py
LLM_ID = "granite-31-8b"  # z client.models.list()
LLM_TEMPERATURE = 0
MAX_TOOL_CALLS = 3
# ================================================

RAG_FUNCTION_NAME = "retrieve_aws_context"
RAG_TOOL_DEFINITION = {
    "type": "function",
    "function": {
        "name": RAG_FUNCTION_NAME,
        "description": (
            "Fetch relevant excerpts from the AWS architecture knowledge base. "
            "Call this whenever you need accurate AWS service or pricing guidance."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": (
                        "Exact user wording or follow-up question you want to look up."
                    ),
                }
            },
            "required": ["question"],
        },
    },
}


client = LlamaStackClient(base_url=BASE_URL)
logger = logging.getLogger(__name__)

try:
    base_path = Path(__file__).parent
except NameError:
    base_path = Path.cwd()

AWS_KB_PATH = base_path / "aws_architecture_kb.md"


def _run_rag_query(user_question: str) -> str:
    """Run RAG query and return concatenated context chunks."""
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


def answer_question(
    current_message: str, conversation_history: Sequence[MessageLike]
) -> str:
    """Answer a user question about AWS using conversation history + RAG tool calls."""
    system_prompt = (
        "You are an AWS solutions assistant for non-technical customers.\n"
        "When the user describes what they want to build:\n"
        "- Clarify missing scale details before estimating cost.\n"
        "- Propose an AWS-based architecture (components + AWS services).\n"
        "- Provide rough monthly cost ranges for small / medium / large tiers.\n"
        "- Explain why AWS is a good fit and how it can scale.\n"
        "Use the retrieve_aws_context tool whenever you need authoritative AWS info.\n"
        "If the user input is empty or unclear, ask for clarification."
    )

    messages: List[Dict[str, Any]] = [{"role": "system", "content": system_prompt}]

    for msg in conversation_history or []:
        role, content = _normalize_message(msg)
        messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": current_message})

    for _ in range(MAX_TOOL_CALLS + 1):
        response_message = _call_llm(messages, use_tools=True)
        tool_calls = getattr(response_message, "tool_calls", None) or []

        if tool_calls:
            messages.append(
                {
                    "role": "assistant",
                    "content": response_message.content or "",
                    "tool_calls": [_serialize_tool_call(tc) for tc in tool_calls],
                }
            )

            for tool_call in tool_calls:
                tool_output = _handle_tool_call(tool_call, current_message)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": getattr(tool_call, "id", ""),
                        "name": getattr(
                            getattr(tool_call, "function", None),
                            "name",
                            RAG_FUNCTION_NAME,
                        ),
                        "content": tool_output,
                    }
                )
            continue

        if response_message.content:
            return response_message.content

        break

    raise RuntimeError("LLM did not produce a final answer")


def _call_llm(messages: List[Dict[str, Any]], use_tools: bool = False):
    """Call the LLM with optional tool definitions."""
    request_kwargs: Dict[str, Any] = {
        "model": LLM_ID,
        "messages": messages,
        "temperature": LLM_TEMPERATURE,
    }

    if use_tools:
        request_kwargs["tools"] = [RAG_TOOL_DEFINITION]
        request_kwargs["tool_choice"] = "auto"

    try:
        completion = client.chat.completions.create(**request_kwargs)
    except Exception as exc:  # pragma: no cover - network layer
        logger.exception("LLM completion request failed")
        raise RuntimeError("LLM backend request failed") from exc

    return completion.choices[0].message


def _serialize_tool_call(tool_call: Any) -> Dict[str, Any]:
    """Convert SDK tool call object into dict expected by chat completions."""
    function_obj = getattr(tool_call, "function", None)
    return {
        "id": getattr(tool_call, "id", ""),
        "type": getattr(tool_call, "type", "function"),
        "function": {
            "name": getattr(function_obj, "name", RAG_FUNCTION_NAME),
            "arguments": getattr(function_obj, "arguments", "{}"),
        },
    }


def _handle_tool_call(tool_call: Any, fallback_question: str) -> str:
    """Execute supported tool calls and return textual output."""
    function_obj = getattr(tool_call, "function", None)
    function_name = getattr(function_obj, "name", "")
    arguments_raw = getattr(function_obj, "arguments", "{}") or "{}"

    try:
        arguments = json.loads(arguments_raw)
    except json.JSONDecodeError:
        arguments = {}

    if function_name != RAG_FUNCTION_NAME:
        logger.warning("Unsupported tool call received: %s", function_name)
        return "Unsupported tool call."

    question = arguments.get("question") or fallback_question
    return _run_rag_query(question)
