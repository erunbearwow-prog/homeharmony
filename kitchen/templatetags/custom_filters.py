# kitchen/templatetags/custom_filters.py
from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Возвращает значение из словаря по ключу.
    Использование: {{ dictionary|get_item:key }}
    """
    if dictionary is None:
        return 0
    return dictionary.get(key, 0)

@register.filter
def get_progress(dictionary, key):
    """
    Возвращает прогресс из словаря по ключу (специально для компонентов).
    Использование: {{ components_progress|get_progress:component.id }}
    """
    if dictionary is None:
        return 0
    return dictionary.get(str(key), 0) or dictionary.get(key, 0)