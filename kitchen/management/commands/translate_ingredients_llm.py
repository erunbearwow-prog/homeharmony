#!/usr/bin/env python
import os
import sys
import django
import subprocess
import json
import time

# Настраиваем Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'homeharmony.settings')
django.setup()

from kitchen.models import Ingredient
from django_localekit.models import Translation


def translate_with_ollama(text):
    """Переводит текст через Ollama (qwen2.5:7b)"""
    prompt = f"""Ты — профессиональный переводчик кулинарных терминов. 
Переведи название ингредиента с английского на русский язык.
Название ингредиента: "{text}"
Требования:
- Используй только русские слова (кириллицу)
- Если есть устоявшийся кулинарный термин, используй его
- Не добавляй пояснений, артиклей, 'the' — только название
- Единицы измерения не переводи, если они есть (г, кг, мл)
- Верни ТОЛЬКО перевод, без кавычек и дополнительного текста

Перевод:"""

    try:
        # Запускаем Ollama
        result = subprocess.run(
            ['ollama', 'run', 'qwen2.5:7b', prompt],
            capture_output=True,
            text=True,
            timeout=30
        )

        translation = result.stdout.strip()

        # Очищаем от возможных кавычек и лишних символов
        translation = translation.strip('"\'')

        # Если перевод пустой или подозрительно длинный, возвращаем оригинал
        if not translation or len(translation) > len(text) * 2:
            return text

        return translation

    except subprocess.TimeoutExpired:
        print(f"⚠️ Таймаут для: {text}")
        return text
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return text


def main():
    print("🚀 Начинаем перевод ингредиентов через Qwen2.5:7b...")

    # Получаем все ингредиенты, у которых нет перевода
    ingredients = Ingredient.objects.all()
    total = ingredients.count()
    translated = 0
    skipped = 0

    print(f"📊 Всего ингредиентов: {total}")

    for idx, ingredient in enumerate(ingredients, 1):
        # Проверяем, есть ли уже перевод на русский
        existing_translation = Translation.objects.filter(
            master_id=ingredient.id,
            master_model='kitchen.ingredient',
            language_code='ru',
            field_name='name'
        ).first()

        if existing_translation:
            print(f"⏭️ [{idx}/{total}] Пропускаем: {ingredient.name} (уже есть перевод)")
            skipped += 1
            continue

        # Переводим
        print(f"🔄 [{idx}/{total}] Переводим: {ingredient.name}")
        ru_name = translate_with_ollama(ingredient.name)

        if ru_name and ru_name != ingredient.name:
            # Создаём перевод
            translation = Translation.objects.create(
                master_id=ingredient.id,
                master_model='kitchen.ingredient',
                language_code='ru',
                field_name='name',
                text=ru_name
            )
            translated += 1
            print(f"   ✅ {ingredient.name} → {ru_name}")
        else:
            print(f"   ⚠️ Не удалось перевести: {ingredient.name}")

        # Небольшая задержка, чтобы не перегружать Ollama
        time.sleep(0.5)

    print(f"\n✅ Готово! Переведено: {translated}, Пропущено: {skipped}, Всего: {total}")


if __name__ == '__main__':
    main()