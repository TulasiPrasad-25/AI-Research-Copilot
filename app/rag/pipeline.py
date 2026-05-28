from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import Document
from typing import List
from app.rag.vectorstore import similarity_search
from app.core.config import settings

PROMPT = ChatPromptTemplate.from_template("""
You are an AI research assistant. Answer the question based on the provided context from research documents.
Be precise, cite the sources, and if the answer is not in the context, say so clearly.

Context:
{context}

Question: {question}

Answer:
""")


def get_llm() -> ChatOpenAI:
    if not settings.OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is required to answer questions.")
    return ChatOpenAI(
        model="gpt-4o",
        temperature=0.2,
        openai_api_key=settings.OPENAI_API_KEY,
    )


def run_rag_pipeline(user_id: int, question: str) -> dict:
    docs: List[Document] = similarity_search(user_id, question, k=5)

    if not docs:
        return {
            "answer": "No relevant documents found. Please upload research papers first.",
            "sources": [],
        }

    context = "\n\n".join([f"[{i+1}] {doc.page_content}" for i, doc in enumerate(docs)])

    chain = PROMPT | get_llm()
    response = chain.invoke({"context": context, "question": question})

    sources = []
    for doc in docs:
        meta = doc.metadata
        sources.append({
            "content": doc.page_content[:300],
            "document_title": meta.get("document_title") or meta.get("source", "Unknown"),
            "page": meta.get("page", None),
        })

    return {
        "answer": response.content,
        "sources": sources,
    }
