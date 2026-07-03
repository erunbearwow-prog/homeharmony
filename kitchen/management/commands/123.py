# /Users/dmitry/Projects/django/homeharmony/kitchen/management/commands/123.py

import os
import sys
import django

# Устанавливаем переменную окружения для настроек Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'homeharmony.settings')  # замените на имя вашего проекта

# Инициализируем Django
django.setup()

# Теперь можно импортировать модели
from kitchen.models import AbstractIngredient, IngredientCategory

# kitchen/management/commands/add_waffles.py
# или вставьте в Django shell

from kitchen.models import AbstractIngredient, IngredientCategory

# Получаем или создаем категорию "Вафли"
waffle_category, _ = IngredientCategory.objects.get_or_create(
    name="Вафли",
    defaults={
        "parent": 'СЛАДОСТИ, ДЕСЕРТЫ, ВЫПЕЧКА ФАСОВАННАЯ',  # или укажите родителя "Сладости"
        "sort_order": 15  # после печенья
    }
)

# Данные для вафель (ГОСТ 14031-2014)
waffles_data = [
    {
        "name": "Вафли классические (неглазированные без начинки)",
        "name_normalized": "vafli_klassicheskie_neglazirovannye_bez_nachinki",
        "calories": 360.0,
        "protein": 8.0,
        "fat": 10.0,
        "carbohydrates": 65.0,
        "fiber": 2.0,
        "sugar": 15.0,
        "description": "Мучное кондитерское изделие выпеченное, с четким рисунком на поверхностях, толщиной не более 2 мм. Содержание муки не менее 90%, влаги не более 5%.",
        "description_ru": "Мучное кондитерское изделие выпеченное, с четким рисунком на поверхностях, толщиной не более 2 мм. Содержание муки не менее 90%, влаги не более 5%.",
        "data_source": "ГОСТ 14031-2014"
    },
    {
        "name": "Вафли с жировой начинкой",
        "name_normalized": "vafli_s_zhirovoy_nachinkoy",
        "calories": 480.0,
        "protein": 7.0,
        "fat": 22.0,
        "carbohydrates": 62.0,
        "fiber": 1.5,
        "sugar": 20.0,
        "description": "Вафли, прослоенные жировой начинкой (тонкоизмельченная масса на основе сахара, жира с добавлением злаковых культур). Массовая доля вафель не менее 20%, жира в начинке не менее 18%.",
        "description_ru": "Вафли, прослоенные жировой начинкой (тонкоизмельченная масса на основе сахара, жира с добавлением злаковых культур). Массовая доля вафель не менее 20%, жира в начинке не менее 18%.",
        "data_source": "ГОСТ 14031-2014"
    },
    {
        "name": "Вафли с пралине",
        "name_normalized": "vafli_s_praline",
        "calories": 520.0,
        "protein": 9.0,
        "fat": 28.0,
        "carbohydrates": 58.0,
        "fiber": 3.0,
        "sugar": 25.0,
        "description": "Вафли с начинкой пралине — тонкоизмельченная кондитерская масса из обжаренных орехов, сахара, масла какао. Массовая доля орехового жира не менее 10%.",
        "description_ru": "Вафли с начинкой пралине — тонкоизмельченная кондитерская масса из обжаренных орехов, сахара, масла какао. Массовая доля орехового жира не менее 10%.",
        "data_source": "ГОСТ 14031-2014"
    },
    {
        "name": "Вафли с фруктовой начинкой",
        "name_normalized": "vafli_s_fruktovoy_nachinkoy",
        "calories": 400.0,
        "protein": 6.0,
        "fat": 12.0,
        "carbohydrates": 70.0,
        "fiber": 4.0,
        "sugar": 35.0,
        "description": "Вафли с фруктовой начинкой — кондитерская масса на основе фруктового сырья с добавлением сахара и студнеобразователя. Массовая доля фруктового сырья не менее 25%.",
        "description_ru": "Вафли с фруктовой начинкой — кондитерская масса на основе фруктового сырья с добавлением сахара и студнеобразователя. Массовая доля фруктового сырья не менее 25%.",
        "data_source": "ГОСТ 14031-2014"
    },
    {
        "name": "Вафли с помадной начинкой",
        "name_normalized": "vafli_s_pomadnoy_nachinkoy",
        "calories": 440.0,
        "protein": 6.5,
        "fat": 16.0,
        "carbohydrates": 68.0,
        "fiber": 1.0,
        "sugar": 40.0,
        "description": "Вафли с помадной начинкой — однородная мелкокристаллическая кондитерская масса на основе сахара и патоки.",
        "description_ru": "Вафли с помадной начинкой — однородная мелкокристаллическая кондитерская масса на основе сахара и патоки.",
        "data_source": "ГОСТ 14031-2014"
    },
    {
        "name": "Вафли типа пралине",
        "name_normalized": "vafli_tipa_praline",
        "calories": 500.0,
        "protein": 8.0,
        "fat": 26.0,
        "carbohydrates": 60.0,
        "fiber": 2.5,
        "sugar": 22.0,
        "description": "Вафли с начинкой типа пралине — масса из обжаренных орехов, семян злаковых или арахиса, сахара, жира. Массовая доля орехового жира не менее 5%.",
        "description_ru": "Вафли с начинкой типа пралине — масса из обжаренных орехов, семян злаковых или арахиса, сахара, жира. Массовая доля орехового жира не менее 5%.",
        "data_source": "ГОСТ 14031-2014"
    },
    {
        "name": "Вафли глазированные шоколадной глазурью",
        "name_normalized": "vafli_glazirovannye_shokoladnoy_glazuryu",
        "calories": 530.0,
        "protein": 8.0,
        "fat": 30.0,
        "carbohydrates": 58.0,
        "fiber": 2.0,
        "sugar": 35.0,
        "description": "Вафли, покрытые шоколадной глазурью (полностью или частично).",
        "description_ru": "Вафли, покрытые шоколадной глазурью (полностью или частично).",
        "data_source": "ГОСТ 14031-2014"
    },
    {
        "name": "Вафли сдобные ('бисквитные')",
        "name_normalized": "vafli_sdobnye_biskvitnye",
        "calories": 420.0,
        "protein": 8.5,
        "fat": 18.0,
        "carbohydrates": 60.0,
        "fiber": 1.5,
        "sugar": 20.0,
        "description": "Сдобные вафли — изделие толщиной до 20 мм, на основе муки, сахара и жира. Содержание муки не менее 50%, влаги не более 20%, сахара не более 40%, жира не более 25%. Разновидность — мягкие 'бисквитные' вафли толщиной 25-30 мм.",
        "description_ru": "Сдобные вафли — изделие толщиной до 20 мм, на основе муки, сахара и жира. Содержание муки не менее 50%, влаги не более 20%, сахара не более 40%, жира не более 25%. Разновидность — мягкие 'бисквитные' вафли толщиной 25-30 мм.",
        "data_source": "ГОСТ 14031-2014"
    }
]

# Добавляем вафли
for data in waffles_data:
    obj, created = AbstractIngredient.objects.get_or_create(
        name=data["name"],
        defaults={
            "category": waffle_category,
            **{k: v for k, v in data.items() if k != "name"},
            "is_active": True
        }
    )
    if created:
        print(f"✅ Создан: {obj.name} (КБЖУ: {obj.calories} ккал)")
    else:
        print(f"⏭️  Пропущен: {obj.name} (уже существует)")
    print("\n✨ Готово!")