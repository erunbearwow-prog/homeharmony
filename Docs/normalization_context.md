# Контекст: нормализация карточек абстрактных ингредиентов

## 1. О проекте

**HomeHarmony** — портал для семейного быта. Репозиторий: `erunbearwow-prog/homeharmony`.

Ключевое для задачи:
- Django-проект, приложение `kitchen`.
- Есть модель `AbstractIngredient` — карточки абстрактных ингредиентов.
- Есть модель `IngredientCategory` — иерархия категорий (FK, `parent` self-reference).
- Есть JSON Schema для карточки (`AbstractIngredient Schema (Extended)`).
- Есть management-команда импорта: `python manage.py import_ingredient <путь>.json --force`.
- Файлы карточек лежат в `semantic_data/abstractIngredients/`.

## 2. Целевая схема карточки (AbstractIngredient)

Обязательные поля (`required`):
- `name` — название (без буквы Ё)
- `short_description` — до 500 символов
- `description` — HTML с блоками
- `semantic_data` — структурированные данные
- `data_source` — enum:
  - `skurikhin_tutelyan_2002`
  - `health-diet.ru`
  - `open_food_facts`
  - `user_added`

Опциональные поля:
- `name_normalized` — транслит латиницей
- `synonyms` — через запятую, с Ё-вариантами
- `category` — строка (путь по иерархии)
- `tags` — массив строк
- `fdc_id`, `source_table`, `source_page`, `portion`, `is_active`
- `data_source_reference` — библиографическая ссылка
- Нутриенты (все опциональны): `calories`, `protein`, `fat`, `carbohydrates`, `water`, `ash`, `fiber`, `sugar`, `starch`, `sodium`, `potassium`, `calcium`, `magnesium`, `phosphorus`, `iron`, `zinc`, `copper`, `manganese`, `selenium`, `vitamin_a`, `vitamin_b1`, `vitamin_b2`, `vitamin_b3`, `vitamin_b4`, `vitamin_b5`, `vitamin_b6`, `vitamin_b7`, `vitamin_b9_folate`, `vitamin_b12`, `vitamin_c`, `vitamin_d`, `vitamin_e`, `vitamin_k`, `retinol_equivalent`, `niacin_equivalent`, `saturated_fat`, `monounsaturated_fat`, `polyunsaturated_fat`, `trans_fat`, `cholesterol`, `omega_3`, `omega_6`, `organic_acids`, `alcohol`, `soluble_fiber`, `insoluble_fiber`

Структура `semantic_data` (строго по схеме):
```json
{
  "properties": ["строка", "..."],
  "preparations": ["строка", "..."],
  "cooking_methods": [
    {"method": "название", "priority": "high|medium|low"}
  ],
  "applications": ["строка", "..."],
  "pairings": {
    "protein": [],
    "vegetables": [],
    "sauces": [],
    "herbs": [],
    "spices": []
  },
  "substitutes": [
    {"name": "название", "similarity": "high|medium|low"}
  ]
}