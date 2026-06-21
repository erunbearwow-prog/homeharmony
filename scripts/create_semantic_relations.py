#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Создание семантических связей между категориями
Запуск: python scripts/create_semantic_relations.py
"""

import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'homeharmony.settings')
import django

django.setup()

from kitchen.models import IngredientCategory, RelationType, SemanticRelation


# ===== ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ =====
def get_category(name):
    """Находит категорию по названию"""
    try:
        return IngredientCategory.objects.get(name=name)
    except IngredientCategory.DoesNotExist:
        print(f"⚠️ Категория не найдена: {name}")
        return None


def get_relation(slug):
    """Находит тип связи по slug"""
    try:
        return RelationType.objects.get(slug=slug)
    except RelationType.DoesNotExist:
        print(f"⚠️ Тип связи не найден: {slug}")
        return None


def add_relation(from_name, to_name, relation_slug, weight=1.0, notes=""):
    """Добавляет семантическую связь между двумя категориями"""
    from_cat = get_category(from_name)
    to_cat = get_category(to_name)
    rel_type = get_relation(relation_slug)

    if not all([from_cat, to_cat, rel_type]):
        return False

    try:
        relation, created = SemanticRelation.objects.get_or_create(
            from_category=from_cat,
            to_category=to_cat,
            relation_type=rel_type,
            defaults={
                'weight': weight,
                'notes': notes,
            }
        )
        if created:
            print(f"✅ {from_name} {rel_type.name} {to_name}")
        else:
            print(f"⏭️ Уже существует: {from_name} {rel_type.name} {to_name}")
        return True
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False


# ===== СВЯЗИ =====

def create_relations():
    """Создает все семантические связи"""
    print("=" * 70)
    print("🔗 СОЗДАНИЕ СЕМАНТИЧЕСКИХ СВЯЗЕЙ")
    print("=" * 70)

    stats = {'created': 0, 'errors': 0}

    # ============================================================
    # 1. ИЕРАРХИЧЕСКИЕ СВЯЗИ (is_a, part_of)
    # ============================================================

    print("\n📂 ИЕРАРХИЧЕСКИЕ СВЯЗИ:")

    hierarchy = [
        # Овощи
        ('Картофель', 'Овощи', 'is_a'),
        ('Морковь', 'Овощи', 'is_a'),
        ('Лук репчатый', 'Овощи', 'is_a'),
        ('Капуста белокочанная', 'Овощи', 'is_a'),
        ('Томаты красные', 'Овощи', 'is_a'),
        ('Огурцы грунтовые', 'Овощи', 'is_a'),
        ('Перец сладкий болгарский', 'Овощи', 'is_a'),
        ('Чеснок', 'Овощи', 'is_a'),

        # Фрукты
        ('Яблоки', 'Фрукты', 'is_a'),
        ('Груши', 'Фрукты', 'is_a'),
        ('Бананы', 'Фрукты', 'is_a'),
        ('Апельсины', 'Фрукты', 'is_a'),
        ('Лимоны', 'Фрукты', 'is_a'),
        ('Виноград', 'Фрукты', 'is_a'),

        # Мясо
        ('Говядина', 'Мясо', 'is_a'),
        ('Свинина', 'Мясо', 'is_a'),
        ('Курица', 'Мясо', 'is_a'),
        ('Баранина', 'Мясо', 'is_a'),
        ('Индейка', 'Мясо', 'is_a'),

        # Рыба
        ('Семга', 'Рыба', 'is_a'),
        ('Треска', 'Рыба', 'is_a'),
        ('Минтай', 'Рыба', 'is_a'),
        ('Скумбрия', 'Рыба', 'is_a'),

        # Молочка
        ('Молоко коровье', 'Молочные продукты', 'is_a'),
        ('Сливки', 'Молочные продукты', 'is_a'),
        ('Сметана', 'Молочные продукты', 'is_a'),
        ('Творог', 'Молочные продукты', 'is_a'),
        ('Сыры', 'Молочные продукты', 'is_a'),
    ]

    for from_name, to_name, rel_slug in hierarchy:
        if add_relation(from_name, to_name, rel_slug):
            stats['created'] += 1
        else:
            stats['errors'] += 1

    # ============================================================
    # 2. ПРОИЗВОДСТВЕННЫЕ СВЯЗИ (made_from, processed_into)
    # ============================================================

    print("\n🔨 ПРОИЗВОДСТВЕННЫЕ СВЯЗИ:")

    production = [
        # Сырье → перерабатывается в → Продукт
        ('Абрикосы', 'Курага', 'processed_into'),
        ('Абрикосы', 'Урюк', 'processed_into'),
        ('Молоко коровье', 'Творог', 'processed_into'),
        ('Молоко коровье', 'Сыр', 'processed_into'),
        ('Сливки', 'Сметана', 'processed_into'),
        ('Сливки', 'Масло сливочное', 'processed_into'),
        ('Пшеница', 'Мука пшеничная', 'processed_into'),
        ('Мука пшеничная', 'Макароны', 'processed_into'),
    ]

    for from_name, to_name, rel_slug in production:
        if add_relation(from_name, to_name, rel_slug):
            stats['created'] += 1
        else:
            stats['errors'] += 1

    # ============================================================
    # 3. КУЛИНАРНЫЕ СВЯЗИ (used_in, goes_with, replaces, enhances)
    # ============================================================

    print("\n🍳 КУЛИНАРНЫЕ СВЯЗИ:")

    culinary = [
        # Используется в
        ('Курица', 'Основные блюда', 'used_in'),
        ('Курица', 'Салаты', 'used_in'),
        ('Курица', 'Бульоны', 'used_in'),
        ('Картофель', 'Гарниры', 'used_in'),
        ('Картофель', 'Супы', 'used_in'),
        ('Лук', 'Супы', 'used_in'),
        ('Лук', 'Соусы', 'used_in'),
        ('Чеснок', 'Соусы', 'used_in'),
        ('Чеснок', 'Маринады', 'used_in'),
        ('Томаты', 'Соусы', 'used_in'),
        ('Томаты', 'Салаты', 'used_in'),
        ('Сливки', 'Соусы', 'used_in'),
        ('Сливки', 'Десерты', 'used_in'),
        ('Сыр', 'Запеканки', 'used_in'),
        ('Сыр', 'Паста', 'used_in'),
        ('Яйца', 'Выпечка', 'used_in'),
        ('Яйца', 'Завтраки', 'used_in'),
        ('Мука', 'Выпечка', 'used_in'),
        ('Мука', 'Паста', 'used_in'),

        # Сочетается с
        ('Курица', 'Грибы', 'goes_with'),
        ('Курица', 'Сливки', 'goes_with'),
        ('Курица', 'Картофель', 'goes_with'),
        ('Говядина', 'Лук', 'goes_with'),
        ('Говядина', 'Картофель', 'goes_with'),
        ('Рыба', 'Лимон', 'goes_with'),
        ('Рыба', 'Зелень', 'goes_with'),
        ('Томаты', 'Базилик', 'goes_with'),
        ('Томаты', 'Чеснок', 'goes_with'),
        ('Сыр', 'Томаты', 'goes_with'),
        ('Сыр', 'Базилик', 'goes_with'),
        ('Яйца', 'Бекон', 'goes_with'),
        ('Яйца', 'Сыр', 'goes_with'),
        ('Картофель', 'Сметана', 'goes_with'),
        ('Картофель', 'Зелень', 'goes_with'),
        ('Мясо', 'Овощи', 'goes_with'),

        # Заменяет
        ('Сметана', 'Йогурт', 'replaces'),
        ('Курага', 'Изюм', 'replaces'),
        ('Миндаль', 'Грецкий орех', 'replaces'),
        ('Оливковое масло', 'Подсолнечное масло', 'replaces'),
        ('Тофу', 'Курица', 'replaces'),

        # Улучшает
        ('Соль', 'Вкус', 'enhances'),
        ('Перец', 'Вкус', 'enhances'),
        ('Специи', 'Вкус', 'enhances'),
        ('Лимон', 'Вкус', 'enhances'),
        ('Чеснок', 'Вкус', 'enhances'),
    ]

    for from_name, to_name, rel_slug in culinary:
        if add_relation(from_name, to_name, rel_slug):
            stats['created'] += 1
        else:
            stats['errors'] += 1

    # ============================================================
    # 4. СРАВНИТЕЛЬНЫЕ СВЯЗИ (similar_to, alternative_to)
    # ============================================================

    print("\n🔍 СРАВНИТЕЛЬНЫЕ СВЯЗИ:")

    comparison = [
        ('Сметана', 'Йогурт', 'similar_to'),
        ('Сливки', 'Молоко', 'similar_to'),
        ('Творог', 'Рикотта', 'similar_to'),
        ('Курага', 'Изюм', 'similar_to'),
        ('Миндаль', 'Фундук', 'similar_to'),
        ('Грецкий орех', 'Пекан', 'similar_to'),
        ('Оливковое масло', 'Подсолнечное масло', 'similar_to'),
        ('Кефир', 'Йогурт', 'similar_to'),
        ('Рис', 'Булгур', 'similar_to'),
        ('Макароны', 'Спагетти', 'similar_to'),

        # Альтернативы
        ('Тофу', 'Курица', 'alternative_to'),
        ('Соевое молоко', 'Молоко коровье', 'alternative_to'),
        ('Овсяное молоко', 'Молоко коровье', 'alternative_to'),
        ('Миндальное молоко', 'Молоко коровье', 'alternative_to'),
        ('Вегетарианский фарш', 'Фарш говяжий', 'alternative_to'),
    ]

    for from_name, to_name, rel_slug in comparison:
        if add_relation(from_name, to_name, rel_slug):
            stats['created'] += 1
        else:
            stats['errors'] += 1

    # ============================================================
    # 5. ДИЕТИЧЕСКИЕ СВЯЗИ (suitable_for, rich_in, source_of)
    # ============================================================

    print("\n💪 ДИЕТИЧЕСКИЕ СВЯЗИ:")

    diet = [
        # Подходит для
        ('Гречка', 'Безглютеновая диета', 'suitable_for'),
        ('Рис', 'Безглютеновая диета', 'suitable_for'),
        ('Киноа', 'Безглютеновая диета', 'suitable_for'),
        ('Куриная грудка', 'Низкокалорийная диета', 'suitable_for'),
        ('Творог', 'Низкокалорийная диета', 'suitable_for'),
        ('Гречка', 'Диабетическая диета', 'suitable_for'),
        ('Овсянка', 'Диабетическая диета', 'suitable_for'),
        ('Тофу', 'Вегетарианская диета', 'suitable_for'),
        ('Соевое молоко', 'Вегетарианская диета', 'suitable_for'),

        # Богат
        ('Курица', 'Белок', 'rich_in'),
        ('Яйца', 'Белок', 'rich_in'),
        ('Рыба', 'Омега-3', 'rich_in'),
        ('Лосось', 'Омега-3', 'rich_in'),
        ('Семга', 'Омега-3', 'rich_in'),
        ('Орехи', 'Жиры', 'rich_in'),
        ('Оливковое масло', 'Жиры', 'rich_in'),
        ('Гречка', 'Клетчатка', 'rich_in'),
        ('Овсянка', 'Клетчатка', 'rich_in'),
        ('Молоко', 'Кальций', 'rich_in'),
        ('Сыр', 'Кальций', 'rich_in'),
        ('Творог', 'Кальций', 'rich_in'),
        ('Шпинат', 'Железо', 'rich_in'),
        ('Бананы', 'Калий', 'rich_in'),
        ('Апельсины', 'Витамин C', 'rich_in'),
        ('Лимоны', 'Витамин C', 'rich_in'),

        # Источник
        ('Кальций', 'Молоко', 'source_of'),
        ('Кальций', 'Сыр', 'source_of'),
        ('Кальций', 'Творог', 'source_of'),
        ('Железо', 'Говядина', 'source_of'),
        ('Железо', 'Шпинат', 'source_of'),
        ('Омега-3', 'Лосось', 'source_of'),
        ('Омега-3', 'Семга', 'source_of'),
        ('Витамин C', 'Апельсины', 'source_of'),
        ('Витамин C', 'Лимоны', 'source_of'),
        ('Клетчатка', 'Гречка', 'source_of'),
        ('Клетчатка', 'Овсянка', 'source_of'),
    ]

    for from_name, to_name, rel_slug in diet:
        if add_relation(from_name, to_name, rel_slug):
            stats['created'] += 1
        else:
            stats['errors'] += 1

    # ============================================================
    # 6. КУЛИНАРНЫЕ ТЕХНИКИ (cooking_method, best_for, requires_technique)
    # ============================================================

    print("\n🔥 КУЛИНАРНЫЕ ТЕХНИКИ:")

    techniques = [
        # Способы приготовления
        ('Картофель', 'Жарка', 'cooking_method'),
        ('Картофель', 'Варка', 'cooking_method'),
        ('Картофель', 'Запекание', 'cooking_method'),
        ('Картофель', 'Фритюр', 'cooking_method'),
        ('Курица', 'Жарка', 'cooking_method'),
        ('Курица', 'Запекание', 'cooking_method'),
        ('Курица', 'Варка', 'cooking_method'),
        ('Курица', 'Гриль', 'cooking_method'),
        ('Говядина', 'Жарка', 'cooking_method'),
        ('Говядина', 'Тушение', 'cooking_method'),
        ('Говядина', 'Гриль', 'cooking_method'),
        ('Рыба', 'Запекание', 'cooking_method'),
        ('Рыба', 'Жарка', 'cooking_method'),
        ('Рыба', 'Варка', 'cooking_method'),
        ('Яйца', 'Варка', 'cooking_method'),
        ('Яйца', 'Жарка', 'cooking_method'),
        ('Яйца', 'Запекание', 'cooking_method'),
        ('Овощи', 'Варка', 'cooking_method'),
        ('Овощи', 'Запекание', 'cooking_method'),
        ('Овощи', 'Тушение', 'cooking_method'),

        # Лучше всего для
        ('Гриль', 'Мясо', 'best_for'),
        ('Гриль', 'Рыба', 'best_for'),
        ('Гриль', 'Овощи', 'best_for'),
        ('Фритюр', 'Картофель', 'best_for'),
        ('Фритюр', 'Курица', 'best_for'),
        ('Запекание', 'Запеканки', 'best_for'),
        ('Запекание', 'Овощи', 'best_for'),
        ('Тушение', 'Говядина', 'best_for'),
        ('Тушение', 'Овощи', 'best_for'),

        # Требует техники
        ('Суфле', 'Взбивание белков', 'requires_technique'),
        ('Безе', 'Взбивание белков', 'requires_technique'),
        ('Крем', 'Взбивание сливок', 'requires_technique'),
        ('Тесто', 'Замешивание', 'requires_technique'),
        ('Паста', 'Замешивание', 'requires_technique'),
    ]

    for from_name, to_name, rel_slug in techniques:
        if add_relation(from_name, to_name, rel_slug):
            stats['created'] += 1
        else:
            stats['errors'] += 1

    # ============================================================
    # ИТОГ
    # ============================================================

    print("\n" + "=" * 70)
    print("📊 СТАТИСТИКА СОЗДАНИЯ СВЯЗЕЙ")
    print("=" * 70)
    print(f"  Создано связей: {stats['created']}")
    print(f"  Ошибок: {stats['errors']}")
    print("=" * 70)

    total_relations = SemanticRelation.objects.count()
    print(f"\n📊 Всего связей в БД: {total_relations}")


if __name__ == "__main__":
    create_relations()