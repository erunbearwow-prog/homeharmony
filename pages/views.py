# pages/views.py
from django.shortcuts import render

def home(request):
    """Главная страница"""
    return render(request, 'pages/home.html', {'title': 'Главная'})

def about(request):
    """О проекте"""
    return render(request, 'pages/about.html', {'title': 'О проекте'})

def contacts(request):
    """Контакты"""
    return render(request, 'pages/contacts.html', {'title': 'Контакты'})

def blog_list(request):
    """Список статей блога"""
    return render(request, 'pages/blog_list.html', {'title': 'Блог'})

def blog_detail(request, slug):
    """Детальная страница статьи"""
    return render(request, 'pages/blog_detail.html', {'title': 'Статья', 'slug': slug})

def advertising(request):
    """Реклама"""
    return render(request, 'pages/advertising.html', {'title': 'Реклама'})

def terms(request):
    """Пользовательское соглашение"""
    return render(request, 'pages/terms.html', {'title': 'Пользовательское соглашение'})

def privacy(request):
    """Политика конфиденциальности"""
    return render(request, 'pages/privacy.html', {'title': 'Политика конфиденциальности'})

def offer(request):
    """Оферта для профессионалов"""
    return render(request, 'pages/offer.html', {'title': 'Оферта'})