#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Наполнение типов семантических связей
Запуск: python scripts/populate_relation_types.py
"""

import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'homeharmony.settings')
import django
django.setup()

from kitchen.models import RelationType


RELATION_TYPES = [
    # ===== ГРУППА 1: ИЕРАРХИЧЕСКИЕ СВЯЗИ =====
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
        'name': 'часть',
        'slug': 'part_of',
        'reverse_name': 'состоит из',
        'description': 'Часть целого (крыло → курица)',
        'icon': '🧩',
        'color': '#2980b9',
        'is_symmetric': False,
        'order': 2,
    },

    # ===== ГРУППА 2: ПРОИЗВОДСТВЕННЫЕ СВЯЗИ =====
    {
        'name': 'сделан из',
        'slug': 'made_from',
        'reverse_name': 'используется в',
        'description': 'Продукт сделан из ингредиента',
        'icon': '🔨',
        'color': '#2ecc71',
        'is_symmetric': False,
        'order': 10,
    },
    {
        'name': 'перерабатывается в',
        'slug': 'processed_into',
        'reverse_name': 'производится из',
        'description': 'Сырье перерабатывается в продукт',
        'icon': '🏭',
        'color': '#27ae60',
        'is_symmetric': False,
        'order': 11,
    },

    # ===== ГРУППА 3: КУЛИНАРНЫЕ СВЯЗИ =====
    {
        'name': 'используется в',
        'slug': 'used_in',
        'reverse_name': 'требует',
        'description': 'Ингредиент используется в блюде/категории',
        'icon': '🍳',
        'color': '#e74c3c',
        'is_symmetric': False,
        'order': 20,
    },
    {
        'name': 'сочетается с',
        'slug': 'goes_with',
        'reverse_name': 'сочетается с',
        'description': 'Продукты, которые хорошо сочетаются',
        'icon': '🤝',
        'color': '#e67e22',
        'is_symmetric': True,
        'order': 21,
    },
    {
        'name': 'заменяет',
        'slug': 'replaces',
        'reverse_name': 'заменяется',
        'description': 'Может заменить другой продукт в рецепте',
        'icon': '🔄',
        'color': '#9b59b6',
        'is_symmetric': False,
        'order': 22,
    },
    {
        'name': 'улучшает',
        'slug': 'enhances',
        'reverse_name': 'улучшается',
        'description': 'Улучшает вкус или свойства другого продукта',
        'icon': '✨',
        'color': '#f1c40f',
        'is_symmetric': False,
        'order': 23,
    },

    # ===== ГРУППА 4: СРАВНИТЕЛЬНЫЕ СВЯЗИ =====
    {
        'name': 'похоже на',
        'slug': 'similar_to',
        'reverse_name': 'похоже на',
        'description': 'Похожие продукты для замены',
        'icon': '🔍',
        'color': '#f39c12',
        'is_symmetric': True,
        'order': 30,
    },
    {
        'name': 'альтернатива',
        'slug': 'alternative_to',
        'reverse_name': 'альтернатива для',
        'description': 'Диетическая/вегетарианская альтернатива',
        'icon': '🌱',
        'color': '#1abc9c',
        'is_symmetric': False,
        'order': 31,
    },

    # ===== ГРУППА 6: ДИЕТИЧЕСКИЕ СВЯЗИ =====
    {
        'name': 'подходит для',
        'slug': 'suitable_for',
        'reverse_name': 'подходит',
        'description': 'Подходит для определенной диеты',
        'icon': '✅',
        'color': '#2ecc71',
        'is_symmetric': False,
        'order': 50,
    },
    {
        'name': 'богат',
        'slug': 'rich_in',
        'reverse_name': 'источник',
        'description': 'Богат определенным нутриентом',
        'icon': '💪',
        'color': '#e74c3c',
        'is_symmetric': False,
        'order': 51,
    },
    {
        'name': 'источник',
        'slug': 'source_of',
        'reverse_name': 'содержится в',
        'description': 'Является источником нутриента',
        'icon': '🔋',
        'color': '#3498db',
        'is_symmetric': False,
        'order': 52,
    },

    # ===== ГРУППА 8: КУЛИНАРНЫЕ ТЕХНИКИ =====
    {
        'name': 'готовится',
        'slug': 'cooking_method',
        'reverse_name': 'способ приготовления',
        'description': 'Ингредиент готовится этим способом',
        'icon': '🔥',
        'color': '#e74c3c',
        'is_symmetric': False,
        'order': 70,
    },
    {
        'name': 'лучше всего для',
        'slug': 'best_for',
        'reverse_name': 'лучше всего с',
        'description': 'Техника лучше всего подходит для продукта',
        'icon': '⭐',
        'color': '#f1c40f',
        'is_symmetric': False,
        'order': 71,
    },
    {
        'name': 'требует техники',
        'slug': 'requires_technique',
        'reverse_name': 'используется для',
        'description': 'Блюдо требует определенной техники',
        'icon': '📖',
        'color': '#9b59b6',
        'is_symmetric': False,
        'order': 72,
    },
]


def populate():
    """Заполняет типы связей"""
    print("=" * 70)
    print("📝 НАПОЛНЕНИЕ ТИПОВ СЕМАНТИЧЕСКИХ СВЯЗЕЙ")
    print("=" * 70)

    stats = {
        'created': 0,
        'updated': 0,
        'errors': 0,
    }

    for data in RELATION_TYPES:
        try:
            obj, created = RelationType.objects.get_or_create(
                slug=data['slug'],
                defaults={
                    'name': data['name'],
                    'reverse_name': data['reverse_name'],
                    'description': data['description'],
                    'icon': data['icon'],
                    'color': data['color'],
                    'is_symmetric': data['is_symmetric'],
                    'order': data['order'],
                }
            )

            if created:
                stats['created'] += 1
                print(f"✅ Создан: {data['name']} ({data['slug']})")
            else:
                # Обновляем существующие
                changed = False
                for field in ['name', 'reverse_name', 'description', 'icon', 'color', 'is_symmetric', 'order']:
                    if getattr(obj, field) != data[field]:
                        setattr(obj, field, data[field])
                        changed = True
                if changed:
                    obj.save()
                    stats['updated'] += 1
                    print(f"🔄 Обновлен: {data['name']} ({data['slug']})")
                else:
                    print(f"⏭️ Без изменений: {data['name']} ({data['slug']})")

        except Exception as e:
            stats['errors'] += 1
            print(f"❌ Ошибка при создании {data['name']}: {e}")

    # Итог
    print("\n" + "=" * 70)
    print("📊 СТАТИСТИКА")
    print("=" * 70)
    print(f"  Создано: {stats['created']}")
    print(f"  Обновлено: {stats['updated']}")
    print(f"  Ошибок: {stats['errors']}")
    print("=" * 70)

    # Показываем все созданные типы
    print("\n📋 СПИСОК ТИПОВ СВЯЗЕЙ:")
    for rt in RelationType.objects.all().order_by('order'):
        print(f"  {rt.icon} {rt.name} → {rt.reverse_name} ({rt.slug})")


if __name__ == "__main__":
    populate()