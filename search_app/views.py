from django.shortcuts import render
from django.http import JsonResponse
from elasticsearch import Elasticsearch
import os
from dotenv import load_dotenv
from search_engine.llm import enhance_search_results

# Load environment variables
load_dotenv()

# Get Elasticsearch host from environment variables
ES_HOST = os.getenv("ELASTICSEARCH_HOST", "http://localhost:9200")
INDEX_NAME = os.getenv("INDEX_NAME", "msmarco_passages")

# Initialize Elasticsearch client
es = Elasticsearch(
    ES_HOST,
    retry_on_timeout=True,
    max_retries=3,
    request_timeout=30
)

def index(request):
    """Render the search homepage"""
    return render(request, 'search_app/index.html')

def search(request):
    """Handle search requests and return results with LLM enhancement"""
    query = request.GET.get('q', '')
    
    if not query:
        return JsonResponse({'error': 'Please provide a search query'}, status=400)
    
    # Check Elasticsearch connection
    if not es.ping():
        return JsonResponse({'error': 'Search service unavailable'}, status=503)
    
    try:
        # Basic Elasticsearch query
        search_results = es.search(
            index=INDEX_NAME,
            query={
                "multi_match": {
                    "query": query,
                    "fields": ["text"],
                    "type": "best_fields"
                }
            },
            size=20,  # Number of results to return
            highlight={
                "fields": {
                    "text": {
                        "pre_tags": ["<strong>"],
                        "post_tags": ["</strong>"],
                        "fragment_size": 200,
                        "number_of_fragments": 3
                    }
                }
            }
        )
        
        # Process search results
        hits = search_results.get('hits', {}).get('hits', [])
        processed_results = []
        
        for hit in hits:
            source = hit.get('_source', {})
            highlights = hit.get('highlight', {}).get('text', [])
            
            processed_results.append({
                'doc_id': source.get('doc_id', ''),
                'text': source.get('text', ''),
                'highlights': highlights,
                'score': hit.get('_score', 0)
            })
        
        # Enhance results with LLM if results found
        if processed_results:
            try:
                enhanced_data = enhance_search_results(query, processed_results)
                return JsonResponse({
                    'query': query,
                    'results': processed_results,
                    'enhanced_response': enhanced_data.get('enhanced_response', '')
                })
            except Exception as e:
                # Fall back to regular results if LLM enhancement fails
                return JsonResponse({
                    'query': query,
                    'results': processed_results,
                    'error_llm': str(e)
                })
        else:
            return JsonResponse({
                'query': query,
                'results': [],
                'message': 'No results found'
            })
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def api_llm_only(request):
    """Endpoint that only uses the LLM for direct Q&A without search"""
    from search_engine.llm import generate_text
    
    query = request.GET.get('q', '')
    
    if not query:
        return JsonResponse({'error': 'Please provide a query'}, status=400)
    
    try:
        response = generate_text(query)
        return JsonResponse({
            'query': query,
            'response': response
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)