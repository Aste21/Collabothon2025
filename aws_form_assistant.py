from typing import List

from llama_stack_client import LlamaStackClient

# ==== CONFIG – dostosuj do swojego środowiska ====
BASE_URL = "http://lsd-llama-milvus-inline-service:8321/"
VECTOR_DB_ID = "form_helper_db"          # ten sam co w rag_seed_aws.py
LLM_ID = "llama-32-8b-instruct"          # z client.models.list()
# ================================================


client = LlamaStackClient(base_url=BASE_URL)


def _build_context(user_question: str) -> str:
    """Run RAG query and build context string for the LLM.

    Steps:
    1) Call rag_tool.query with the user's question.
    2) Extract document contents from the top matches.
    3) Join them into a single text block.
    """
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


def answer_question(user_question: str) -> str:
    """Answer a user question about AWS and the deployment form.

    Steps:
    1) Build a context using RAG (vector DB).
    2) Construct a system and user message for the LLM.
    3) Call LlamaStack chat.completions.
    4) Return the assistant's text answer.
    """
    context_text = _build_context(user_question)

    system_prompt = (
        """You are an AWS solutions assistant for non-technical customers.
        The user will describe a system they want to build.
         Your job is to:
        1) Restate their requirements in simple terms.
        2) Propose an AWS-based architecture (components + AWS services).
        3) Provide a rough monthly cost estimate in clearly labeled tiers,
           based on the scale described (small / medium / large).
        4) Explain why this approach on AWS is a good fit.
        If you lack key details (like number of users or traffic), ask a short clarification question first.
        Always answer in clear, friendly English."""
    )

    # user message includes both context and the actual question
    user_message = (
        f"Context:\n{context_text}\n\n"
        f"User question: {user_question}\n\n"
        "Answer in clear, friendly English."
    )

    completion = client.chat.completions.create(
        model=LLM_ID,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
    )

    # message is an object, not a dict
    answer_text = completion.choices[0].message.content
    return answer_text


if __name__ == "__main__":
    # Simple CLI for quick manual testing
    print("AWS Form Assistant – type your question (or 'exit'):\n")
    while True:
        try:
            q = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break

        if not q:
            continue
        if q.lower() in {"exit", "quit"}:
            print("Bye!")
            break

        reply = answer_question(q)
        print(f"\nAssistant: {reply}\n")
