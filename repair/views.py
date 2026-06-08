from django.shortcuts import render

def index(request):
    return render(request, 'repair/index.html', {'title': 'Ремонт и обустройство'})

def diy_list(request):
    return render(request, 'repair/diy_list.html', {'title': 'DIY-проекты'})

def diy_detail(request, slug):
    return render(request, 'repair/diy_detail.html', {'slug': slug, 'title': 'DIY-проект'})

def tools_list(request):
    return render(request, 'repair/tools_list.html', {'title': 'Инструменты'})

def organization(request):
    return render(request, 'repair/organization.html', {'title': 'Организация пространства'})