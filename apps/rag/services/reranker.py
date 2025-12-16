from django.conf import settings
from openai import OpenAI


client = OpenAI(api_key=settings.OPENAI_API_KEY)


def rerank_chunks(query, chunks, top_n=3):
    if not chunks:
        return []
    
    scored = []
    
    for item in chunks:
        chunk = item["chunk"]
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Rate how relevant this document is to the query. Reply with only a number from 0 to 10."
                },
                {
                    "role": "user", 
                    "content": f"Query: {query}\n\nDocument: {chunk.content[:1000]}"
                }
            ],
            max_tokens=5,
            temperature=0
        )
        
        try:
            score = float(response.choices[0].message.content.strip())
        except:
            score = 5.0
        
        scored.append({
            "chunk": chunk,
            "fusion_score": item["score"],
            "rerank_score": score,
            "methods": item.get("methods", [])
        })
    
    scored.sort(key=lambda x: x["rerank_score"], reverse=True)
    
    return scored[:top_n]