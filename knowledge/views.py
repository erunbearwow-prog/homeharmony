from django.shortcuts import render

def index(request):
    return render(request, 'knowledge/index.html', {'title': 'База знаний'})

def encyclopedia(request):
    return render(request, 'knowledge/encyclopedia.html', {'title': 'Энциклопедия терминов'})

def term_detail(request, term):
    return render(request, 'knowledge/term_detail.html', {'term': term, 'title': term})

def instructions(request):
    return render(request, 'knowledge/instructions.html', {'title': 'Инструкции'})

def instruction_detail(request, slug):
    return render(request, 'knowledge/instruction_detail.html', {'slug': slug, 'title': 'Инструкция'})

def hacks_list(request):
    return render(request, 'knowledge/hacks_list.html', {'title': 'Лайфхаки'})

def search(request):
    query = request.GET.get('q', '')
    return render(request, 'knowledge/search.html', {'query': query, 'title': 'Поиск'})