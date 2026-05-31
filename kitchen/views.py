from django.http import HttpResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import CookingMethod

# Create your views here.
def home(request):
    return render(request, 'kitchen/index.html')

def recipe(request):
    return render(request, 'kitchen/cooking_recipe.html')

@require_http_methods(['GET'])
def get_method_details(request, method_id):
    """API для получения деталей метода приготовления"""
    try:
        method = CookingMethod.objects.get(id=method_id)
        data = {
            'id': method.id,
            'name': method.name,
            'icon': method.icon,
            'short_description': method.short_description,
            'description': method.description,
            'scientific_background': method.scientific_background,
            'typical_temperature': method.typical_temperature,
            'typical_duration': method.typical_duration,
            'tips': method.tips,
            'common_mistakes': method.common_mistakes,
            'advanced_notes': method.advanced_notes,
        }
        return JsonResponse(data)
    except CookingMethod.DoesNotExist:
        return JsonResponse({'error': 'Method not found'}, status=404)