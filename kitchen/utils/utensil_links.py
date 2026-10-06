import re
from django.core.cache import cache
from kitchen.models import RecommendedUtensil

# {утварь:Блендер|блендером}
UTENSIL_MARKER_RE = re.compile(r'\{утварь:([^}|]+)\|([^}]+)\}')

def _get_utensil_map():
    data = cache.get('utensil_name_map')
    if data is None:
        data = dict(RecommendedUtensil.objects.values_list('name', 'id'))
        cache.set('utensil_name_map', data, 60 * 60)
    return data

def render_description(text, html=False):
    """Заменяет маркеры {утварь:Название|форма} на ссылки.
    html=True — <a href>, иначе просто текст формы."""
    utmap = _get_utensil_map()

    def replace(match):
        name, display = match.group(1).strip(), match.group(2)
        uid = utmap.get(name)
        if uid is None:
            return display  # нет такого названия — показываем просто текст
        if html:
            return f'<a href="/kitchen/utensils/{uid}/">{display}</a>'
        return display

    return UTENSIL_MARKER_RE.sub(replace, text)
