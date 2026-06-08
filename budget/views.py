from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def dashboard(request):
    return render(request, 'budget/dashboard.html', {'title': 'Бюджет'})

@login_required
def expense_list(request):
    return render(request, 'budget/expense_list.html', {'title': 'Расходы'})

@login_required
def add_expense(request):
    return render(request, 'budget/add_expense.html', {'title': 'Добавить расход'})

@login_required
def shopping_list(request):
    return render(request, 'budget/shopping_list.html', {'title': 'Список покупок'})

def export_csv(request):
    from django.http import HttpResponse
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="expenses.csv"'
    return response