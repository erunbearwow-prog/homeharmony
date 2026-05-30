from django.http import HttpResponse
from django.shortcuts import render
from django.template.loader import render_to_string

# Create your views here.
def home(request):
    t = render_to_string('kitchen/index.html')
    return HttpResponse(t)


def recipe(request):
    print(f'recipe view here!')
    t = render_to_string('kitchen/cooking_recipe.html')
    return HttpResponse(t)