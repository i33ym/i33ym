import json
from django.shortcuts import render
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from asgiref.sync import sync_to_async
from .services.pipeline import process_query, rag_pipeline, get_llm
from .services.retrieval import HybridRetriever


def chat_page(request):
    show_debug = request.GET.get("debug", "").lower() == "true"
    return render(request, "rag/chat.html", {"show_debug": show_debug})


@csrf_exempt
@require_http_methods(["POST"])
def chat_api(request):
    try:
        data = json.loads(request.body)
        query = data.get("query", "").strip()
        include_debug = data.get("debug", False)
        
        if not query:
            return JsonResponse({"error": "Query is required"}, status=400)
        
        result = process_query(query, include_debug=include_debug)
        return JsonResponse(result)
    
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def chat_stream(request):
    try:
        data = json.loads(request.body)
        query = data.get("query", "").strip()
        include_debug = data.get("debug", False)
        
        if not query:
            return JsonResponse({"error": "Query is required"}, status=400)
        
        return StreamingHttpResponse(
            stream_rag_response(query, include_debug),
            content_type="text/event-stream"
        )
    
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def stream_rag_response(query: str, include_debug: bool = False):
    """Synchronous generator for SSE streaming."""
    import time
    from django.conf import settings
    from langchain_openai import ChatOpenAI
    from langchain_core.prompts import ChatPromptTemplate
    
    stages = [
        ("retrieve", "🔍 Поиск в документации..."),
        ("rerank", "📊 Ранжирование результатов..."),
        ("check_relevance", "✅ Проверка релевантности..."),
        ("generate", "💬 Генерация ответа..."),
        ("check_grounding", "🔒 Проверка достоверности...")
    ]
    
    yield f"data: {json.dumps({'type': 'stage', 'stage': 'start', 'message': '🚀 Начинаю обработку...'})}\n\n"
    
    result = None
    current_stage_idx = 0
    
    try:
        retriever = HybridRetriever(k=10)
        
        yield f"data: {json.dumps({'type': 'stage', 'stage': 'retrieve', 'message': stages[0][1]})}\n\n"
        retrieval_results = retriever.retrieve(query)
        fused_docs = retrieval_results["fused_results"]
        
        if include_debug:
            debug_data = {
                "vector_count": len(retrieval_results["vector_results"]),
                "bm25_count": len(retrieval_results["bm25_results"]),
                "fused_count": len(fused_docs)
            }
            yield f"data: {json.dumps({'type': 'debug', 'stage': 'retrieve', 'data': debug_data})}\n\n"
        
        yield f"data: {json.dumps({'type': 'stage', 'stage': 'rerank', 'message': stages[1][1]})}\n\n"
        
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            api_key=settings.OPENAI_API_KEY
        )
        
        scored_docs = []
        for doc in fused_docs[:10]:
            prompt = ChatPromptTemplate.from_template(
                "Оцените релевантность от 0 до 10. Ответьте только числом.\nЗапрос: {query}\nДокумент: {content}"
            )
            chain = prompt | llm
            try:
                result = chain.invoke({"query": query, "content": doc.page_content[:500]})
                score = float(result.content.strip())
            except:
                score = 5.0
            scored_docs.append({"doc": doc, "score": score})
        
        scored_docs.sort(key=lambda x: x["score"], reverse=True)
        reranked_docs = [item["doc"] for item in scored_docs[:5]]
        scores = [item["score"] for item in scored_docs[:5]]
        
        if include_debug:
            yield f"data: {json.dumps({'type': 'debug', 'stage': 'rerank', 'data': {'scores': scores}})}\n\n"
        
        yield f"data: {json.dumps({'type': 'stage', 'stage': 'check_relevance', 'message': stages[2][1]})}\n\n"
        
        yield f"data: {json.dumps({'type': 'stage', 'stage': 'generate', 'message': stages[3][1]})}\n\n"
        
        if not reranked_docs:
            yield f"data: {json.dumps({'type': 'token', 'content': 'К сожалению, я не нашёл информации по вашему вопросу.'})}\n\n"
        else:
            context = "\n\n---\n\n".join([d.page_content for d in reranked_docs])
            
            streaming_llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0,
                api_key=settings.OPENAI_API_KEY,
                streaming=True
            )
            
            prompt = ChatPromptTemplate.from_template(
                """Ты — помощник по документации платежного API Multicard.
Отвечай только на основе предоставленного контекста.
Включай примеры кода, когда это уместно.
Отвечай на том же языке, что и вопрос.

Контекст:
{context}

Вопрос: {query}

Ответ:"""
            )
            
            chain = prompt | streaming_llm
            
            for chunk in chain.stream({"query": query, "context": context}):
                if chunk.content:
                    yield f"data: {json.dumps({'type': 'token', 'content': chunk.content})}\n\n"
        
        yield f"data: {json.dumps({'type': 'stage', 'stage': 'check_grounding', 'message': stages[4][1]})}\n\n"
        
        sources = [{"source": d.metadata.get("source", "unknown")} for d in reranked_docs[:3]]
        yield f"data: {json.dumps({'type': 'done', 'sources': sources})}\n\n"
        
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"