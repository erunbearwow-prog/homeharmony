# Контекст разработки HomeHarmony — после Шага 10.3

**Дата:** 18.09.2026
**Точка возврата:** КБЖУ-движок работает, админка Части 10.1–10.4 частично готова.
**Следующий шаг:** чистка `AbstractIngredient`, потом возврат к `StepIngredient` и остальной админке.

---

## Что сделано за сессию

### 1. Модели (готовы, мигрированы)

| Модель | Что делает |
|---|---|
| **`UnitConversion`** | Правила пересчёта единиц (г, мл, шт, ст.л., ч.л., щеп., пучок, стакан 250, стакан 200) в граммы. |
| **`CutShape`** | Формы нарезки (целиком, соломка, кубики, пюре, фарш, …) с `factor` — множитель впитываемости масла. 18 записей. |
| **`StepIngredient`** | Связь «ингредиент ↔ шаг рецепта». Содержит `preparation`, `cooking_method`, `cooking_note`. |
| **`RecipeIngredientOption`** | Варианты ингредиентов из ТТК («говяжья или баранья»). |
| **`Recipe`** | Добавлены: `calories_per_100g`, `protein_per_100g`, `fat_per_100g`, `carbs_per_100g`, `total_weight`, `nutrition_calculated_at`, `rating`, `rating_count`. |
| **`RecipeFoodItem`** | Переделан: убраны `ingredient`/`product`; добавлены `abstract_ingredient`, `branded_ingredient`, `subrecipe`, `cut_shape`, `override_cooking_method`. |
| **`ProductLossNorm`** | Добавлен FK `ingredient` → `AbstractIngredient` (сейчас 31 привязано, 16 остались на `product_name` как fallback). |
| **`CookingMethod`** | Добавлен `default_oil` (FK на масло подсолнечное, id=2377). Удалён `cut_shape_factors`. |
| **`RecipeStep`** | Убраны `cooking_method`, `ingredient_preparation` (переехали в `StepIngredient`). `subrecipe_base_ingredient` → `RecipeFoodItem`. |
| **`IngredientSubstitution`** | Переделана: `food_item` (FK на `RecipeFoodItem`), `substitute_ingredient`, `substitute_branded`, `substitute_subrecipe`, `source`, `applied_rule`. |
| **`IngredientSubstitutionRule`** | Добавлены `usage_count`, `is_public`. |
| **`UnitConversion.category`** | FK на `IngredientCategory` — правила могут быть на категорию. |

### 2. Миграции (применены)

- `0066`–`0076` — 10+ миграций.
- Итог: 129 рецептов пересчитаны успешно (**129/129** без ошибок).
- `UnitConversion`: **78+ правил** (3 общих + 75 категорийных + ингредиентных).
- `CutShape`: 18 форм.
- `CookingMethod.default_oil` заполнен для 7 методов.
- 25 новых категорий, 12+ ингредиентов перенесены в правильные категории.

### 3. Расчётный движок (`kitchen/utils/nutrition.py`)

**Функции:**
- `convert_to_grams(quantity, unit, ingredient)` — с иерархией поиска (ингредиент → категория → родитель → общее).
- `resolve_nutrition_per_100g(item)` — КБЖУ источника (subrecipe > branded > abstract).
- `get_loss_norm(ingredient, cooking_method)` — потери.
- `get_oil_absorption(ingredient, cooking_method)` — впитываемость масла.
- `calculate_item_nutrition(item, cooking_method)` — расчёт одного ингредиента.
- `recalculate_recipe_nutrition(recipe)` — общий расчёт, разветвляется:
  - `_recalculate_home` — по `RecipeFoodItem` (сложный, с потерями и маслом).
  - `_recalculate_professional` — по `ProfessionalIngredient` (простой, брутто/нетто).

**Порядок применения:** граммы → потери → впитываемость масла → КБЖУ.

**Порядок поиска UnitConversion:**
1. Ингредиент (`ingredient=FK`).
2. Категория ингредиента (`category=FK`).
3. Родительские категории вверх по дереву.
4. Общее правило (`ingredient=None, category=None`).

### 4. Управление

- **Management-команда:** `python manage.py recalculate_nutrition [--recipe-id N] [--only-empty] [--recipe-type home]`.
- **Action в админке:** «Пересчитать КБЖУ выбранных рецептов» в `RecipeAdmin`.
- **`RecipeAdmin`:** `get_inlines()` (разные наборы для home/ttk), `get_nutrition_summary` (зелёный блок), `get_calories_summary` (в списке).

### 5. Админка (частично)

| Admin | Статус |
|---|---|
| `UnitConversionAdmin` | ✅ |
| `CutShapeAdmin` | ✅ |
| `RecipeFoodItemAdmin` | ✅ + `FoodTypeFilter` |
| `RecipeAdmin` | ✅ (`get_inlines`, action, КБЖУ-блок) |
| `RecipeStepAdmin` | ✅ + `StepIngredientInline` |
| `StepIngredientInline` | ✅ |
| `RecipeFoodItemInline` | ✅ |
| `ProfessionalIngredientInline` | ✅ |
| `IngredientSubstitutionRuleAdmin` | ✅ (старый) |
| `HomeIngredientAdmin`, `IngredientSubstitutionAdmin` | ⚠️ закомментированы через `SKIP_BROKEN_ADMIN` |

### 6. Временные костыли

- `SKIP_BROKEN_ADMIN = True` в `admin.py` — оборачивает сломанные админки (не удалены).
- `RecipeAdmin.get_nutrition_summary` — исправлен баг с `format_html` и `{:.1f}` (числа форматируются заранее).

---

## Что НЕ сделано / требует внимания

### 1. **Главная проблема: у `AbstractIngredient` нет КБЖУ**

**2224 ингредиента, у большинства `calories = None`.**

Пример из Бешамеля:
- Сливочное масло: `None` (должно быть 748 ккал/100г)
- Мука: `None` (334)
- Сливки 33%: `None` (322)
- Мускатный орех: `None` (556)

**Результат:** Бешамель считается как **1 ккал/порция** вместо **~460 ккал**.

**Решение:** заполнить КБЖУ. Варианты:
- **A.** Вручную топ-100 ингредиентов (быстро покрывает 80%).
- **B.** Импорт из Приложения 1 Скурихина (полный).
- **C.** Гибрид: сначала A, потом B.

**Решение принято:** сначала **чистка `AbstractIngredient`** (ручная), потом заполнение КБЖУ.

### 2. **`StepIngredient.food_item = None` у всех шагов**

- Все `StepIngredient` созданы миграцией `0062` **без привязки** к `RecipeFoodItem`.
- Значит, потери (уварка/ужарка) и впитываемость масла **не учитываются** в расчёте.
- Чтобы учитывались — привязать вручную через `RecipeStepAdmin` (страница шага → inline `StepIngredient`).

**Проверка работы:** открыть `/admin/kitchen/recipe/130/change/` → шаг → проверить, что dropdown `food_item` показывает ингредиенты рецепта.

### 3. **Админка: незаконченные блоки**

- **`RecipeIngredientOptionInline`** — не создан (варианты из ТТК).
- **`IngredientSubstitutionInline`** — не переделан под новые поля.
- **`HomeIngredientInline`** — закомментирован (legacy).
- **`SKIP_BROKEN_ADMIN = True`** — надо убрать после правок.

### 4. **`HomeIngredient` — legacy**

- В базе 1 запись (перенесена в `RecipeFoodItem` миграцией `0061`).
- Модель можно **удалить** после чистки `AbstractIngredient`.

### 5. **`Product` (Open Food Facts)** — legacy

- В `RecipeFoodItem` больше не используется.
- Можно **удалить** модель или оставить для будущего импорта.

### 6. **`AbstractIngredient` — мусор**

- **Брендированные** ингредиенты в `AbstractIngredient`: «Марципан Ашан», «Томатная Паста Пятерочка», «Сосиски Детские Ашан» и т.д.
- **Обрывки названий:** «Марципановая», «Марципановое», «Марципановые», «Масляно-сахарная», «Сахарное».
- **Дубли:** «Крахмал кукурузный» (ID=1857) и «Кукурузный крахмал» (ID=1991 — уже удалён).
- **Незаполненные категории** у многих ингредиентов.

---

## Инструменты и команды

### Часто используемые

```bash
# Проверка
python manage.py check

# Миграции
python manage.py makemigrations kitchen
python manage.py migrate kitchen

# Пересчёт КБЖУ
python manage.py recalculate_nutrition
python manage.py recalculate_nutrition --recipe-id 124
python manage.py recalculate_nutrition --only-empty

# Дамп базы
python manage.py dumpdata > backup_YYYYMMDD.json

# Shell
python manage.py shell
```

### Полезные запросы в shell

```python
# Ингредиенты без КБЖУ, используемые в рецептах
from kitchen.models import AbstractIngredient
from django.db.models import Count

qs = AbstractIngredient.objects.filter(
    calories__isnull=True,
    used_in_recipes__isnull=False
).distinct().annotate(usage=Count('used_in_recipes')).order_by('-usage')

for ing in qs[:20]:
    print(f"ID={ing.id} | {ing.name} | used={ing.usage}")

# Правила UnitConversion
from kitchen.models import UnitConversion
for r in UnitConversion.objects.filter(from_unit='шт').select_related('ingredient', 'category'):
    print(r)

# Состав рецепта
from kitchen.models import Recipe
r = Recipe.objects.get(pk=130)
for item in r.food_items.select_related('abstract_ingredient', 'branded_ingredient', 'subrecipe'):
    print(f"{item.quantity} {item.unit} | {item.food_name}")
```

---

## Что делать дальше (план)

### Этап A. Чистка `AbstractIngredient` (текущая задача)

1. **Просмотреть все 2224 ингредиента.**
2. **Удалить мусор:**
   - «Марципановая», «Марципановое», «Сахарное», «Масляно-сахарная» (обрывки).
   - Дубли.
3. **Перенести брендированные в `BrandedIngredient`:**
   - «Марципан Ашан», «Томатная Паста Пятерочка», «Сосиски Детские Ашан» и т.д.
   - Или удалить, если это разовые упоминания.
4. **Привязать ингредиенты к категориям** (там, где пусто).
5. **Заполнить КБЖУ** — топ-100 вручную, потом полный импорт из Скурихина.

### Этап B. Возврат к админке (после чистки)

1. **Заполнить `StepIngredient.food_item`** через `RecipeStepAdmin`.
2. **Пересчитать рецепты** — увидеть, как потери и масло влияют на КБЖУ.
3. **`RecipeIngredientOptionInline`** — варианты из ТТК.
4. **`IngredientSubstitutionInline`** — переделка под новые поля.
5. **Убрать `SKIP_BROKEN_ADMIN`.**
6. **`HomeIngredient` и `Product` — удалить** (или заархивировать).

### Этап C. Приложения Скурихина (после B)

1. **Приложение 1** — химсостав и калорийность (полный импорт КБЖУ).
2. **Приложение 2** — уже импортировано (меры объёма).
3. **Приложение 3** — уже импортировано (масса 1 шт).

### Этап D. Бэкенд фронта

1. **Правки в `views.py`** — старые поля (`item.ingredient`, `item.product`) → новые.
2. **Правки в шаблонах** — то же.
3. **`save_recipe_variant`** — доработка под новые модели.

---

## Ключевые ID для справки

| Что | ID |
|---|---|
| Масло подсолнечное | 2377 |
| Сахар | 6502 |
| Яйцо куриное | 5345 |
| Мука (пшеничная) | ~3754 |
| Крахмал кукурузный | 1857 |
| Крахмал картофельный | 1856 |
| Утиная грудка с кожей | 11324 |
| Рецепт «Кисло-сладкий соус» | 124 |
| Рецепт «Утиная грудка с инжирным чатни» | 130 |
| Рецепт «Бешамель основной» | 121 |
| Рецепт «Суп Харчо» | 131 |

---

## Справочные данные для заполнения КБЖУ (топ-20)

| Ингредиент | Ккал/100г | Белки | Жиры | Углеводы |
|---|---|---|---|---|
| Сливочное масло 82.5% | 748 | 0.5 | 82.5 | 0.8 |
| Мука пшеничная в/с | 334 | 10.3 | 1.1 | 68.9 |
| Сливки 33% | 322 | 2.2 | 33.0 | 4.0 |
| Сливки 20% | 205 | 2.8 | 20.0 | 3.7 |
| Молоко 3.2% | 60 | 2.9 | 3.2 | 4.7 |
| Молоко 2.5% | 52 | 2.8 | 2.5 | 4.7 |
| Яйцо куриное | 157 | 12.7 | 11.5 | 0.7 |
| Сахар-песок | 399 | 0 | 0 | 99.8 |
| Соль поваренная | 0 | 0 | 0 | 0 |
| Масло подсолнечное | 899 | 0 | 99.9 | 0 |
| Сметана 20% | 206 | 2.8 | 20.0 | 3.2 |
| Сметана 30% | 294 | 2.4 | 30.0 | 3.1 |
| Творог 5% | 121 | 17.0 | 5.0 | 1.8 |
| Сыр твердый | 364 | 25.0 | 29.5 | 0 |
| Куриная грудка (филе) | 110 | 23.0 | 1.5 | 0 |
| Куриное бедро | 185 | 19.0 | 12.0 | 0 |
| Говядина (I кат.) | 218 | 18.6 | 16.0 | 0 |
| Свинина (мясная) | 357 | 14.3 | 33.0 | 0 |
| Картофель | 77 | 2.0 | 0.4 | 16.3 |
| Морковь | 35 | 1.3 | 0.1 | 6.9 |

*(Данные по Скурихину, 2008)*

---

## Что уже работает и что нет

### ✅ Работает
- Расчёт КБЖУ для 129 рецептов (129/129 без ошибок).
- Иерархия правил мер (ингредиент → категория → родитель → общее).
- Разветвление `home` / `ttk` расчётов.
- Action «Пересчитать КБЖУ» в `RecipeAdmin`.
- `get_nutrition_summary` — зелёный блок.
- `UnitConversionAdmin`, `CutShapeAdmin`, `RecipeFoodItemAdmin`, `RecipeStepAdmin`.
- `StepIngredientInline` — работает (можно добавлять/редактировать).

### ❌ Не работает / не заполнено
- **КБЖУ у ~90% ингредиентов = `None`** → КБЖУ рецептов занижены.
- **`StepIngredient.food_item = None`** → потери и масло не учитываются.
- **`SKIP_BROKEN_ADMIN = True`** — часть админок отключена.
- **`HomeIngredient`, `Product`** — legacy, не удалены.
- **`IngredientSubstitutionInline`** — старая версия.
- **`RecipeIngredientOptionInline`** — не создан.
- **Фронтенд** (`views.py`, шаблоны) — старые поля в `saved_recipe_variant` и др.

---

## Точка возврата

**При возврате к этой точке:**
1. Проверить `python manage.py check`.
2. Убедиться, что `SKIP_BROKEN_ADMIN = True`.
3. Открыть `admin.py` — все админки из раздела «✅ Работает» должны быть активны.
4. Продолжить с **Этапа A** (чистка `AbstractIngredient`).

**Дамп базы:** `backup_after_admin_step1.json` (сделан до текущей сессии).
**Дамп перед следующей большой правкой:** сделать.