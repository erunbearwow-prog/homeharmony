from django.shortcuts import render
from .models import CleaningTask, CleaningTip

def index(request):
    tasks = CleaningTask.objects.all()[:6]
    tips = CleaningTip.objects.all()[:3]
    return render(request, 'cleaning/index.html', {'tasks': tasks, 'tips': tips, 'title': 'Уборка'})

def task_list(request):
    tasks = CleaningTask.objects.all()
    return render(request, 'cleaning/task_list.html', {'tasks': tasks, 'title': 'Задачи по уборке'})

def task_detail(request, task_id):
    from django.shortcuts import get_object_or_404
    task = get_object_or_404(CleaningTask, id=task_id)
    return render(request, 'cleaning/task_detail.html', {'task': task, 'title': task.title})

def checklist(request):
    tasks = CleaningTask.objects.all()
    return render(request, 'cleaning/checklist.html', {'tasks': tasks, 'title': 'Чек-лист уборки'})

def tips_list(request):
    tips = CleaningTip.objects.all()
    category = request.GET.get('category')
    if category:
        tips = tips.filter(category=category)
    return render(request, 'cleaning/tips_list.html', {'tips': tips, 'title': 'Советы по уборке'})

def schedule(request):
    return render(request, 'cleaning/schedule.html', {'title': 'График уборки'})