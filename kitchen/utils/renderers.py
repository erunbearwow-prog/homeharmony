# kitchen/utils/renderers.py
import re
from django.urls import reverse
from django.utils.html import escape

UTENSIL_MARKER_RE = re.compile(r'\{утварь:([^|}]+)(?:\|([^}]+))?\}')
METHOD_MARKER_RE = re.compile(r'\{метод:([^}]+)\}')


def _norm(s):
    return s.strip().casefold()


def build_utensil_url_map():
    from kitchen.models import RecommendedUtensil
    return {_norm(name): code for name, code in
            RecommendedUtensil.objects.values_list('name', 'code')}


def build_method_url_map():
    from kitchen.models import CookingMethod
    result = {}
    methods = CookingMethod.objects.filter(code__isnull=False).exclude(code='')
    for method in methods:
        try:
            result[_norm(method.code)] = reverse(
                'kitchen:cooking_method_detail', args=[method.id]
            )
        except Exception:
            continue
    return result


def render_utensil_links(text, url_map=None):
    """Заменяет {утварь:Название|склонение} на ссылки в произвольном тексте.

    Подходит для любых полей: alternative, description и т.д.
    Неизвестная утварь остаётся простым текстом.
    """
    if url_map is None:
        url_map = build_utensil_url_map()

    def _replace(m):
        name = m.group(1).strip()
        display = (m.group(2) or name).strip()
        code = url_map.get(_norm(name))
        if code:
            href = reverse('kitchen:utensil_detail', args=[code])
            return f'<a href="{escape(href)}">{escape(display)}</a>'
        return display

    return UTENSIL_MARKER_RE.sub(_replace, text or '')


def render_description(method, utensil_url_map=None, method_url_map=None):
    """Рендер описания метода: маркеры утвари + маркеры методов."""
    if utensil_url_map is None:
        utensil_url_map = build_utensil_url_map()

    def _replace_method(m):
        code = m.group(1).strip()
        href = (method_url_map or {}).get(_norm(code))
        if href:
            return f'<a href="{escape(href)}">{escape(code)}</a>'
        return code

    text = render_utensil_links(method.description or '', utensil_url_map)
    if method_url_map:
        text = METHOD_MARKER_RE.sub(_replace_method, text)
    return text
