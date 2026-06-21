# scripts/create_relation_types.py

from kitchen.models import RelationType

RELATION_TYPES = [
    {
        'name': 'является',
        'slug': 'is_a',
        'reverse_name': 'включает',
        'description': 'Иерархическая связь (категория-подкатегория)',
        'icon': '📂',
        'color': '#3498db',
        'is_symmetric': False,
        'order': 1,
    },
    {
        'name': 'сделано из',
        'slug': 'made_from',
        'reverse_name': 'используется в',
        'description': 'Продукт сделан из ингредиента',
        'icon': '🔨',
        'color': '#2ecc71',
        'is_symmetric': False,
        'order': 2,
    },
    {
        'name': 'похоже на',
        'slug': 'similar_to',
        'reverse_name': 'похоже на',
        'description': 'Похожие продукты для замены',
        'icon': '🔍',
        'color': '#f39c12',
        'is_symmetric': True,
        'order': 3,
    },
    {
        'name': 'заменяет',
        'slug': 'substitutes',
        'reverse_name': 'заменяется',
        'description': 'Может заменить в рецепте',
        'icon': '🔄',
        'color': '#9b59b6',
        'is_symmetric': False,
        'order': 4,
    },
    {
        'name': 'используется в',
        'slug': 'used_in',
        'reverse_name': 'использует',
        'description': 'Используется в кулинарных целях',
        'icon': '🍳',
        'color': '#e74c3c',
        'is_symmetric': False,
        'order': 5,
    },
    {
        'name': 'связано с',
        'slug': 'related_to',
        'reverse_name': 'связано с',
        'description': 'Общая смысловая связь',
        'icon': '🔗',
        'color': '#95a5a6',
        'is_symmetric': True,
        'order': 6,
    },
    {
        'name': 'альтернатива',
        'slug': 'alternative_to',
        'reverse_name': 'альтернатива для',
        'description': 'Вегетарианская/диетическая альтернатива',
        'icon': '🌱',
        'color': '#27ae60',
        'is_symmetric': False,
        'order': 7,
    },
    {
        'name': 'сезон',
        'slug': 'season',
        'reverse_name': 'сезон для',
        'description': 'Сезонность продукта',
        'icon': '🌿',
        'color': '#2ecc71',
        'is_symmetric': False,
        'order': 8,
    },
]

for data in RELATION_TYPES:
    RelationType.objects.get_or_create(
        slug=data['slug'],
        defaults=data
    )
    print(f"✅ {data['name']}")