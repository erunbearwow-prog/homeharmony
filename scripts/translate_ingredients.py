#!/usr/bin/env python
import os
import sys
import subprocess
import time

# Добавляем текущую директорию в путь
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# Настраиваем Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'homeharmony.settings')

try:
    import django

    django.setup()
    print("✅ Django настроен успешно")
except Exception as e:
    print(f"❌ Ошибка настройки Django: {e}")
    sys.exit(1)

from kitchen.models import Ingredient
from django.contrib.contenttypes.models import ContentType
from django_localekit.models import Translation


def translate_with_ollama(text):
    """Переводит текст через Ollama"""
    if not text or len(text.strip()) < 2:
        return text

    prompt = f"""Ты — профессиональный переводчик кулинарных терминов. 
Переведи название ингредиента с английского на русский язык.
Название ингредиента: "{text}"
Требования:
- Используй только русские слова
- Если есть устоявшийся термин, используй его
- Не добавляй пояснений, артиклей, 'the'
- Верни ТОЛЬКО перевод, без кавычек

Перевод:"""

    try:
        result = subprocess.run(
            ['ollama', 'run', 'qwen2.5:7b', prompt],
            capture_output=True,
            text=True,
            timeout=30
        )
        translation = result.stdout.strip()
        translation = translation.strip('"\'').strip()

        if not translation or len(translation) > len(text) * 3:
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

    # Проверяем Ollama
    try:
        subprocess.run(['ollama', 'list'], capture_output=True, check=True)
        print("✅ Ollama доступен")
    except Exception as e:
        print(f"❌ Ollama не запущен. Запустите 'ollama serve'")
        return

    # Получаем ContentType для модели Ingredient
    ingredient_content_type = ContentType.objects.get_for_model(Ingredient)

    ingredients = Ingredient.objects.all()
    total = ingredients.count()
    translated = 0
    skipped = 0

    print(f"📊 Всего ингредиентов: {total}")

    for idx, ingredient in enumerate(ingredients, 1):
        # Проверяем, есть ли уже перевод
        existing_translation = Translation.objects.filter(
            content_type=ingredient_content_type,
            object_id=str(ingredient.id),
            language='ru',
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
            Translation.objects.create(
                content_type=ingredient_content_type,
                object_id=str(ingredient.id),
                language='ru',
                field_name='name',
                field_value=ru_name  # ← ИСПРАВЛЕНО: 'text' → 'field_value'
            )
            translated += 1
            print(f"   ✅ {ingredient.name} → {ru_name}")
        else:
            print(f"   ⚠️ Не удалось перевести: {ingredient.name}")

        time.sleep(0.3)

    print(f"\n✅ Готово!")
    print(f"   Переведено: {translated}")
    print(f"   Пропущено (уже есть): {skipped}")
    print(f"   Всего обработано: {total}")


if __name__ == '__main__':
    main()