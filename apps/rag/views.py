import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from .services.pipeline import process_query


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