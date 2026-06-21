#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Создание обратных связей "источник" (source_of) на основе связей "богат" (rich_in)
Запуск: python scripts/create_source_relations.py
"""

import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'homeharmony.settings')
import django

django.setup()

from kitchen.models import RelationType, SemanticRelation


def create_source_relations():
    """Создает обратные связи 'источник' для всех связей 'богат'"""
    print("=" * 70)
    print("🔄 СОЗДАНИЕ ОБРАТНЫХ СВЯЗЕЙ 'ИСТОЧНИК'")
    print("=" * 70)

    # Получаем типы связей
    rich_in = RelationType.objects.get(slug='rich_in')
    source_of = RelationType.objects.get(slug='source_of')

    # Находим все связи "богат"
    rich_relations = SemanticRelation.objects.filter(relation_type=rich_in)

    print(f"\n📊 Найдено связей 'богат': {rich_relations.count()}")

    stats = {'created': 0, 'skipped': 0, 'errors': 0}

    for rel in rich_relations:
        from_cat = rel.from_category  # Продукт (например, Бананы)
        to_cat = rel.to_category  # Нутриент (например, Калий)

        # Проверяем, существует ли уже обратная связь
        exists = SemanticRelation.objects.filter(
            from_category=to_cat,  # Нутриент → источник → Продукт
            to_category=from_cat,
            relation_type=source_of
        ).exists()

        if exists:
            stats['skipped'] += 1
            continue

        try:
            # Создаем обратную связь
            relation = SemanticRelation.objects.create(
                from_category=to_cat,
                to_category=from_cat,
                relation_type=source_of,
                weight=rel.weight,
                notes=f"Источник {rel.from_category.name}"
            )
            stats['created'] += 1
            print(f"  ✅ {to_cat.name} → источник → {from_cat.name}")

        except Exception as e:
            stats['errors'] += 1
            print(f"  ❌ Ошибка: {e}")

    # Итог
    print("\n" + "=" * 70)
    print("📊 СТАТИСТИКА")
    print("=" * 70)
    print(f"  Создано связей 'источник': {stats['created']}")
    print(f"  Пропущено (уже есть): {stats['skipped']}")
    print(f"  Ошибок: {stats['errors']}")
    print("=" * 70)

    # Проверяем результат
    total_source = SemanticRelation.objects.filter(relation_type=source_of).count()
    print(f"\n📊 Всего связей 'источник' в БД: {total_source}")


if __name__ == "__main__":
    create_source_relations()