NO_ANSWER_MESSAGE = "I couldn't find information in the available knowledge base that answers this question."

SYSTEM_PROMPT = """You are an enterprise knowledge assistant.

Your task is to answer the user's question using ONLY the provided retrieved context below.

STRICT RULES:
1. Base your answer ONLY on the provided context snippets.
2. Do NOT use outside knowledge or make assumptions beyond what is explicitly stated in the context.
3. Do NOT invent or fabricate facts, dates, names, or numbers.
4. If the retrieved context does NOT contain sufficient information to answer the question, respond EXACTLY with:
   "{no_answer_message}"
5. Keep your answer concise, accurate, and directly address the user's question.
"""

USER_PROMPT_TEMPLATE = """User Question:
{question}

Retrieved Context:
{context}

Provide a clear and grounded answer based strictly on the context above.
"""


def build_context_string(chunks: list) -> str:
    """Formats retrieved context chunks into a readable string block with source headers."""
    if not chunks:
        return "No relevant context found."

    context_blocks = []
    for idx, chunk in enumerate(chunks, 1):
        metadata = chunk.get("metadata", {})
        title = metadata.get("title", "Untitled Source")
        doc_id = metadata.get("document_id", "N/A")
        source_type = metadata.get("source_type", "document")
        content = chunk.get("content", "").strip()

        block = f"[Source {idx}: {title} (ID: {doc_id}, Type: {source_type})]\n{content}"
        context_blocks.append(block)

    return "\n\n---\n\n".join(context_blocks)
