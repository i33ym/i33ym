from typing import TypedDict, Literal
from django.conf import settings
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import StateGraph, START, END
from .retrieval import HybridRetriever


class RAGState(TypedDict):
    query: str
    rewritten_query: str
    vector_results: list
    bm25_results: list
    fused_results: list
    reranked_results: list
    is_relevant: bool
    answer: str
    is_grounded: bool
    retry_count: int
    debug_info: dict


def get_llm():
    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        api_key=settings.OPENAI_API_KEY
    )


def rewrite_query(state: RAGState) -> dict:
    llm = get_llm()
    prompt = ChatPromptTemplate.from_template(
        """Перепишите этот запрос для лучшего поиска в документации платежного API.
        Оригинал: {query}
        Переписанный запрос:"""
    )
    chain = prompt | llm | StrOutputParser()
    rewritten = chain.invoke({"query": state["query"]})
    
    return {
        "rewritten_query": rewritten,
        "debug_info": {**state.get("debug_info", {}), "rewritten_query": rewritten}
    }


def retrieve_documents(state: RAGState) -> dict:
    retriever = HybridRetriever(k=10)
    query = state.get("rewritten_query") or state["query"]
    results = retriever.retrieve(query)
    
    return {
        "vector_results": results["vector_results"],
        "bm25_results": results["bm25_results"],
        "fused_results": results["fused_results"],
        "debug_info": {
            **state.get("debug_info", {}),
            "retrieval": {
                "query_used": query,
                "vector_count": len(results["vector_results"]),
                "bm25_count": len(results["bm25_results"]),
                "fused_count": len(results["fused_results"]),
                "vector_preview": [d.page_content[:100] for d in results["vector_results"][:3]],
                "bm25_preview": [d.page_content[:100] for d in results["bm25_results"][:3]],
            }
        }
    }


def rerank_documents(state: RAGState) -> dict:
    llm = get_llm()
    query = state.get("rewritten_query") or state["query"]
    docs = state["fused_results"]
    
    if not docs:
        return {"reranked_results": [], "debug_info": state.get("debug_info", {})}
    
    scored_docs = []
    for doc in docs[:10]:
        prompt = ChatPromptTemplate.from_template(
            """Оцените релевантность от 0 до 10. Ответьте только числом.
            Запрос: {query}
            Документ: {content}"""
        )
        chain = prompt | llm | StrOutputParser()
        try:
            score = float(chain.invoke({
                "query": query,
                "content": doc.page_content[:500]
            }).strip())
        except:
            score = 5.0
        scored_docs.append({"doc": doc, "score": score})
    
    scored_docs.sort(key=lambda x: x["score"], reverse=True)
    reranked = [item["doc"] for item in scored_docs[:5]]
    scores = [item["score"] for item in scored_docs[:5]]
    
    return {
        "reranked_results": reranked,
        "debug_info": {
            **state.get("debug_info", {}),
            "reranking": {
                "scores": scores,
                "top_docs": [d.page_content[:100] for d in reranked[:3]]
            }
        }
    }


def check_relevance(state: RAGState) -> dict:
    llm = get_llm()
    query = state["query"]
    docs = state["reranked_results"]
    
    if not docs:
        return {"is_relevant": False, "debug_info": state.get("debug_info", {})}
    
    context = "\n\n".join([d.page_content[:300] for d in docs[:3]])
    prompt = ChatPromptTemplate.from_template(
        """Может ли этот контекст ответить на вопрос? Ответьте только 'да' или 'нет'.
        Вопрос: {query}
        Контекст: {context}"""
    )
    chain = prompt | llm | StrOutputParser()
    result = chain.invoke({"query": query, "context": context})
    is_relevant = "да" in result.lower() or "yes" in result.lower()
    
    return {
        "is_relevant": is_relevant,
        "debug_info": {
            **state.get("debug_info", {}),
            "relevance_check": {
                "result": is_relevant,
                "raw_response": result
            }
        }
    }


def generate_answer(state: RAGState) -> dict:
    llm = get_llm()
    query = state["query"]
    docs = state["reranked_results"]
    
    if not docs:
        return {
            "answer": "К сожалению, я не нашёл информации по вашему вопросу в документации Multicard."
        }
    
    context = "\n\n---\n\n".join([d.page_content for d in docs])
    sources = list(set([d.metadata.get("source", "unknown") for d in docs]))
    
    prompt = ChatPromptTemplate.from_template(
        """Ты — помощник по документации платежного API Multicard.
Отвечай только на основе предоставленного контекста.
Если в контексте нет ответа, так и скажи.
Включай примеры кода, когда это уместно.
Отвечай на том же языке, что и вопрос.

Контекст:
{context}

Вопрос: {query}

Ответ:"""
    )
    chain = prompt | llm | StrOutputParser()
    answer = chain.invoke({"query": query, "context": context})
    
    return {
        "answer": answer,
        "debug_info": {
            **state.get("debug_info", {}),
            "generation": {
                "sources": sources,
                "context_length": len(context)
            }
        }
    }


def check_grounding(state: RAGState) -> dict:
    llm = get_llm()
    docs = state["reranked_results"]
    answer = state["answer"]
    
    if not docs:
        return {"is_grounded": True}
    
    context = "\n\n".join([d.page_content[:500] for d in docs[:3]])
    prompt = ChatPromptTemplate.from_template(
        """Этот ответ основан на контексте? Ответьте только 'да' или 'нет'.
        Контекст: {context}
        Ответ: {answer}"""
    )
    chain = prompt | llm | StrOutputParser()
    result = chain.invoke({"context": context, "answer": answer})
    is_grounded = "да" in result.lower() or "yes" in result.lower()
    
    return {
        "is_grounded": is_grounded,
        "debug_info": {
            **state.get("debug_info", {}),
            "grounding_check": {
                "result": is_grounded,
                "raw_response": result
            }
        }
    }


def route_after_relevance(state: RAGState) -> Literal["generate", "rewrite"]:
    if state.get("is_relevant"):
        return "generate"
    if state.get("retry_count", 0) >= 1:
        return "generate"
    return "rewrite"


def increment_retry(state: RAGState) -> dict:
    return {"retry_count": state.get("retry_count", 0) + 1}


def build_rag_graph():
    workflow = StateGraph(RAGState)
    
    workflow.add_node("retrieve", retrieve_documents)
    workflow.add_node("rerank", rerank_documents)
    workflow.add_node("check_relevance", check_relevance)
    workflow.add_node("rewrite", rewrite_query)
    workflow.add_node("increment_retry", increment_retry)
    workflow.add_node("generate", generate_answer)
    workflow.add_node("check_grounding", check_grounding)
    
    workflow.add_edge(START, "retrieve")
    workflow.add_edge("retrieve", "rerank")
    workflow.add_edge("rerank", "check_relevance")
    workflow.add_conditional_edges(
        "check_relevance",
        route_after_relevance,
        {"generate": "generate", "rewrite": "rewrite"}
    )
    workflow.add_edge("rewrite", "increment_retry")
    workflow.add_edge("increment_retry", "retrieve")
    workflow.add_edge("generate", "check_grounding")
    workflow.add_edge("check_grounding", END)
    
    return workflow.compile()


rag_pipeline = build_rag_graph()


def process_query(query: str, include_debug: bool = False) -> dict:
    initial_state: RAGState = {
        "query": query,
        "rewritten_query": "",
        "vector_results": [],
        "bm25_results": [],
        "fused_results": [],
        "reranked_results": [],
        "is_relevant": False,
        "answer": "",
        "is_grounded": False,
        "retry_count": 0,
        "debug_info": {}
    }
    
    result = rag_pipeline.invoke(initial_state)
    
    sources = []
    for doc in result.get("reranked_results", [])[:3]:
        sources.append({
            "content": doc.page_content[:200] + "...",
            "source": doc.metadata.get("source", "unknown")
        })
    
    response = {
        "answer": result["answer"],
        "sources": sources,
        "is_grounded": result.get("is_grounded", True)
    }
    
    if include_debug:
        response["debug"] = result.get("debug_info", {})
    
    return response

async def process_query_streaming(query: str, include_debug: bool = False):
    """Generator that yields SSE events for each pipeline stage."""
    
    initial_state: RAGState = {
        "query": query,
        "rewritten_query": "",
        "vector_results": [],
        "bm25_results": [],
        "fused_results": [],
        "reranked_results": [],
        "is_relevant": False,
        "answer": "",
        "is_grounded": False,
        "retry_count": 0,
        "debug_info": {}
    }
    
    async for event in rag_pipeline.astream(initial_state, stream_mode="updates"):
        for node_name, node_output in event.items():
            yield {
                "type": "stage",
                "stage": node_name,
                "data": {
                    "debug": node_output.get("debug_info", {}) if include_debug else None
                }
            }
    
    final_state = await rag_pipeline.ainvoke(initial_state)
    
    sources = []
    for doc in final_state.get("reranked_results", [])[:3]:
        sources.append({
            "content": doc.page_content[:200] + "...",
            "source": doc.metadata.get("source", "unknown")
        })
    
    yield {
        "type": "answer",
        "data": {
            "answer": final_state["answer"],
            "sources": sources,
            "is_grounded": final_state.get("is_grounded", True)
        }
    }


async def stream_answer_tokens(query: str, context_docs: list):
    """Stream answer tokens as they're generated."""
    from langchain_openai import ChatOpenAI
    from langchain_core.prompts import ChatPromptTemplate
    
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        api_key=settings.OPENAI_API_KEY,
        streaming=True
    )
    
    context = "\n\n---\n\n".join([d.page_content for d in context_docs])
    
    prompt = ChatPromptTemplate.from_template(
        """Ты — помощник по документации платежного API Multicard.
Отвечай только на основе предоставленного контекста.
Если в контексте нет ответа, так и скажи.
Включай примеры кода, когда это уместно.
Отвечай на том же языке, что и вопрос.

Контекст:
{context}

Вопрос: {query}

Ответ:"""
    )
    
    chain = prompt | llm
    
    async for chunk in chain.astream({"query": query, "context": context}):
        if chunk.content:
            yield chunk.content