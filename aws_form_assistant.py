import json
import logging
from types import SimpleNamespace
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

from llama_stack_client import LlamaStackClient

from config import get_settings

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


AWS_COMPONENTS = [
    "API-Gateway",
    "Aurora",
    "CloudFront",
    "CloudTrail",
    "CloudWatch",
    "DynamoDB",
    "EC2",
    "Elastic-Container-Registry",
    "Elastic-Container-Service",
    "Elastic-Kubernetes-Service",
    "Elastic-Load-Balancing",
    "EventBridge",
    "Identity-and-Access-Management",
    "IoT-Core",
    "Lambda",
    "Network-Firewall",
    "RDS",
    "Route-53",
    "Secrets-Manager",
    "Simple-Notification-Service",
    "Simple-Queue-Service",
    "Simple-Storage-Service",
    "Step-Functions",
    "Virtual-Private-Cloud",
]


settings = get_settings()
client = LlamaStackClient(base_url=settings.base_url)
logger = logging.getLogger(__name__)


def _run_rag_query(user_question: str) -> str:
    """Run RAG query and return concatenated context chunks."""
    logger.info("Running RAG query for question: %s", user_question)
    rag_result = client.tool_runtime.rag_tool.query(
        content=user_question,
        vector_db_ids=[settings.vector_db_id],
    )

    chunks: List[str] = []
    matches = getattr(rag_result, "matches", []) or []
    for match in matches:
        doc = getattr(match, "document", None)
        content = getattr(doc, "content", None) if doc is not None else None
        if isinstance(content, str) and content:
            chunks.append(content)

    if not chunks:
        logger.info("RAG query returned 0 chunks")
        return "No extra AWS context was retrieved."

    # we keep first few chunks to avoid overly long prompt
    trimmed = chunks[:3]
    logger.info("RAG query returned %d chunk(s), using %d", len(chunks), len(trimmed))
    return "\n\n---\n\n".join(trimmed)


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
    history_len = len(conversation_history or [])
    logger.info("Answering new question; history_len=%d", history_len)

    allowed_components = ", ".join(AWS_COMPONENTS)
    system_prompt = (
        "You are an AWS solutions assistant for non-technical customers.\n"
        "When the user describes what they want to build:\n"
        "- Clarify missing scale details before estimating cost.\n"
        "- Propose an AWS-based architecture (components + AWS services).\n"
        "- Provide rough monthly cost ranges for small / medium / large tiers.\n"
        "- Explain why AWS is a good fit and how it can scale.\n"
        f"Only use the following AWS components in your answers: {allowed_components}.\n"
        "If the user asks for something outside this list, politely say it is"
        " outside scope and offer the closest allowed alternative.\n"
        "Do not disclose tool usage, function calls, or mention retrieve_aws_context "
        "in your reply.\n"
        "Before you attempt any answer about AWS, ALWAYS call the retrieve_aws_context tool, "
        "consume its output, and only then craft the final reply.\n"
        "If the user input is empty or unclear, ask for clarification."
    )

    messages: List[Dict[str, Any]] = [{"role": "system", "content": system_prompt}]

    for msg in conversation_history or []:
        role, content = _normalize_message(msg)
        messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": current_message})

    for attempt in range(1, MAX_TOOL_CALLS + 2):
        logger.info("LLM request attempt %d/%d", attempt, MAX_TOOL_CALLS + 1)
        response_message = _call_llm(messages, use_tools=True)
        tool_calls = getattr(response_message, "tool_calls", None) or []
        assistant_content = response_message.content or ""

        if not tool_calls:
            synthetic_call = _maybe_extract_tool_call_from_content(assistant_content)
            if synthetic_call:
                tool_calls = [synthetic_call]
                assistant_content = ""
                logger.info("Inline JSON tool call detected and converted")

        if tool_calls:
            logger.info("Processing %d tool call(s)", len(tool_calls))
            assistant_content = ""
            messages.append(
                {
                    "role": "assistant",
                    "content": assistant_content,
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
            final_text = _strip_tool_call_json(response_message.content)
            logger.info("Returning final answer (chars=%d)", len(final_text))
            return final_text

        break

    logger.error(
        "LLM did not produce a final answer after %d attempts", MAX_TOOL_CALLS + 1
    )
    raise RuntimeError("LLM did not produce a final answer")


def _call_llm(messages: List[Dict[str, Any]], use_tools: bool = False):
    """Call the LLM with optional tool definitions."""
    logger.info(
        "Invoking LLM model=%s, messages=%d, use_tools=%s",
        settings.model_id,
        len(messages),
        use_tools,
    )
    try:
        # completion = client.chat.completions.create(**request_kwargs)
        completion = client.chat.completions.create(
            model=settings.model_id,
            messages=messages,
            temperature=settings.llm_temperature,
            tool_choice="auto",
            tools=[RAG_TOOL_DEFINITION],
        )
    except Exception as exc:  # pragma: no cover - network layer
        logger.exception("LLM completion request failed")
        raise RuntimeError("LLM backend request failed") from exc

    message = completion.choices[0].message
    tool_calls = getattr(message, "tool_calls", None) or []
    logger.info("LLM response received; tool_calls=%d", len(tool_calls))
    return message


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


def _maybe_extract_tool_call_from_content(
    content: str,
) -> Optional[SimpleNamespace]:
    """Handle models that emit tool instructions as plain JSON text."""
    if not content:
        return None

    text = content.strip()
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return None

    if not isinstance(payload, dict):
        return None

    name = payload.get("name")
    if name != RAG_FUNCTION_NAME:
        return None

    parameters = payload.get("parameters", {})
    if not isinstance(parameters, dict):
        parameters = {}

    return SimpleNamespace(
        id=payload.get("id", ""),
        type="function",
        function=SimpleNamespace(
            name=name,
            arguments=json.dumps(parameters),
        ),
    )


def _strip_tool_call_json(content: str) -> str:
    """Remove any inline JSON tool call description from the final answer."""
    if not content:
        return content

    marker = '"name": "retrieve_aws_context"'
    idx = content.find(marker)
    if idx == -1:
        return content

    start = content.rfind("{", 0, idx)
    if start == -1:
        return content

    depth = 0
    end = start
    while end < len(content):
        char = content[end]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                block = content[start : end + 1]
                before = content[:start].rstrip()
                after = content[end + 1 :].lstrip()
                pieces = [piece for piece in [before, after] if piece]
                logger.info(
                    "Stripped inline tool call JSON block (%d chars)", len(block)
                )
                return "\n\n".join(pieces)
        end += 1

    return content


def _handle_tool_call(tool_call: Any, fallback_question: str) -> str:
    """Execute supported tool calls and return textual output."""
    function_obj = getattr(tool_call, "function", None)
    function_name = getattr(function_obj, "name", "")
    arguments_raw = getattr(function_obj, "arguments", "{}") or "{}"

    try:
        arguments = json.loads(arguments_raw)
    except json.JSONDecodeError:
        arguments = {}

    logger.info(
        "Received tool call: %s with raw args: %s", function_name, arguments_raw
    )

    if function_name != RAG_FUNCTION_NAME:
        logger.warning("Unsupported tool call received: %s", function_name)
        return "Unsupported tool call."

    question = arguments.get("question") or fallback_question
    return _run_rag_query(question)
