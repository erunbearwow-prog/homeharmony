# update_times.py
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'homeharmony.settings')
django.setup()

from kitchen.models import Recipe

print("🚀 Начинаем пересчёт времени для всех рецептов...\n")

updated = 0
for recipe in Recipe.objects.all():
    old_time = recipe.total_time
    new_time = recipe.calculate_total_time()
    if old_time != new_time:
        recipe.total_time = new_time
        recipe.save(update_fields=['total_time'])
        updated += 1
        print(f"✅ {recipe.title}: {old_time} → {new_time} мин")

print(f"\n📊 Готово! Обновлено рецептов: {updated}")