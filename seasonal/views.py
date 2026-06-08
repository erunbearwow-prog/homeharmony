from django.shortcuts import render

def index(request):
    """Главная страница раздела 'Сезонное'"""
    return render(request, 'seasonal/index.html', {'title': 'Сезонное'})

def canning(request):
    """Заготовки"""
    return render(request, 'seasonal/canning.html', {'title': 'Заготовки'})

def garden(request):
    """Уход за садом"""
    return render(request, 'seasonal/garden.html', {'title': 'Уход за садом'})

def spring(request):
    """Весенние работы"""
    return render(request, 'seasonal/spring.html', {'title': 'Весна'})

def summer(request):
    """Летние работы"""
    return render(request, 'seasonal/summer.html', {'title': 'Лето'})

def autumn(request):
    """Осенние работы"""
    return render(request, 'seasonal/autumn.html', {'title': 'Осень'})

def winter(request):
    """Зимние работы"""
    return render(request, 'seasonal/winter.html', {'title': 'Зима'})