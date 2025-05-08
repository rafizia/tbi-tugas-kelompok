from django.shortcuts import render

# Create your views here.
def search_view(request):
    context = {}
    if request.method == 'POST':
        query = request.POST.get('query')
        context['query'] = query
        context['answer'] = f"Result: '{query}'"
    
    return render(request, 'search.html', context)
