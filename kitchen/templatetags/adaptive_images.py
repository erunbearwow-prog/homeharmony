from django import template
from django.template.loader import render_to_string

register = template.Library()


@register.simple_tag
def adaptive_image(recipe, css_class='w-full rounded-2xl shadow-lg object-cover'):
    """
    Генерирует адаптивное изображение для рецепта
    """
    if not recipe.image:
        return ''

    context = {
        'url_400w': recipe.image_400w.url,
        'url_800w': recipe.image_800w.url,
        'url_1200w': recipe.image_1200w.url,
        'url_fallback': recipe.image_fallback.url,
        'alt': recipe.title,
        'css_class': css_class,
    }

    return render_to_string('kitchen/tags/adaptive_image.html', context)