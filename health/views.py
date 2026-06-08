from django.shortcuts import render

def index(request):
    return render(request, 'health/index.html', {'title': 'Здоровье и уход'})

def first_aid(request):
    return render(request, 'health/first_aid.html', {'title': 'Первая помощь'})

def first_aid_detail(request, slug):
    return render(request, 'health/first_aid_detail.html', {'slug': slug, 'title': 'Инструкция'})

def care_tips(request):
    return render(request, 'health/care_tips.html', {'title': 'Советы по уходу'})

def video_tutorials(request):
    return render(request, 'health/video_tutorials.html', {'title': 'Видеоуроки'})