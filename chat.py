# file: rag_service.py

import os
from typing import List, Tuple
from langchain.chains import ConversationalRetrievalChain
from langchain_astradb import AstraDBVectorStore
from local_models import get_local_embeddings, get_local_llm

# ─────────── Environment ───────────
ASTRA_DB_COLLECTION     = os.getenv("ASTRA_DB_COLLECTION")
ASTRA_DB_API_ENDPOINT   = os.getenv("ASTRA_DB_API_ENDPOINT")
ASTRA_DB_APPLICATION_TOKEN = os.getenv("ASTRA_DB_APPLICATION_TOKEN")

# ───────── Embeddings & Store ────────
embeddings = get_local_embeddings()
if embeddings:
    vectorstore = AstraDBVectorStore(
        embedding=embeddings,
        collection_name=ASTRA_DB_COLLECTION,
        api_endpoint=ASTRA_DB_API_ENDPOINT,
        token=ASTRA_DB_APPLICATION_TOKEN
    )
    
    # ───────── Retriever (k=2) ─────────
    retriever = vectorstore.as_retriever(
        search_kwargs={"k": 2}
    )
    
    # ─────────── LLM & Chain ───────────
    llm = get_local_llm()
    if llm:
        chain = ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=retriever,
            return_source_documents=True
        )
    else:
        chain = None
else:
    vectorstore = None
    retriever = None
    llm = None
    chain = None

def rag_chat(
    query: str,
    session_chat_history: List[Tuple[str, str]] = None
) -> Tuple[str, List[int]]:
    """
    Run a conversational RAG query.

    Returns:
      - answer (str)
      - sorted list of page numbers (List[int]) used as sources
    """
    if not chain:
        return "Error: RAG chain not initialized. Please check if models are loaded correctly.", []
    
    # keep only the last 5 turns
    history = session_chat_history[-5:] if session_chat_history else []

    try:
        # run the chain
        result = chain({
            "question": query,
            "chat_history": history
        })

        answer = result["answer"]
        source_docs = result.get("source_documents", [])

        # extract page numbers from metadata
        pages = []
        for doc in source_docs:
            md = getattr(doc, "metadata", {}) or {}
            if "page" in md:
                pages.append(md["page"])
            elif isinstance(md.get("metadata"), dict) and "page" in md["metadata"]:
                pages.append(md["metadata"]["page"])

        return answer, sorted(set(pages))
    except Exception as e:
        return f"Error processing query: {str(e)}", []
