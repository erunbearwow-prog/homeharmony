#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Поиск файлов, не соответствующих схеме.
Запуск: python find_invalid_files.py
"""

import os
import json
import glob
from jsonschema import validate, ValidationError

# ==================== СХЕМА ====================
SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["name", "short_description", "description", "semantic_data"],
    "properties": {
        "name": {"type": "string"},
        "name_normalized": {"type": "string"},
        "synonyms": {"type": "string", "maxLength": 500},
        "short_description": {"type": "string", "maxLength": 500},
        "description": {"type": "string"},
        "category": {"type": "string"},
        "semantic_data": {
            "type": "object",
            "properties": {
                "properties": {"type": "array", "items": {"type": "string"}},
                "preparations": {"type": "array", "items": {"type": "string"}},
                "cooking_methods": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "method": {"type": "string"},
                            "priority": {"type": "string", "enum": ["high", "medium", "low"]}
                        },
                        "required": ["method", "priority"]
                    }
                },
                "applications": {"type": "array", "items": {"type": "string"}},
                "pairings": {
                    "type": "object",
                    "properties": {
                        "protein": {"type": "array", "items": {"type": "string"}},
                        "vegetables": {"type": "array", "items": {"type": "string"}},
                        "sauces": {"type": "array", "items": {"type": "string"}},
                        "herbs": {"type": "array", "items": {"type": "string"}},
                        "spices": {"type": "array", "items": {"type": "string"}}
                        # Здесь НЕТ additionalProperties: False — значит любые поля разрешены!
                    }
                },
                "substitutes": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "similarity": {"type": "string", "enum": ["high", "medium", "low"]}
                        },
                        "required": ["name", "similarity"]
                    }
                }
            }
        },
        "tags": {"type": "array", "items": {"type": "string"}}
    }
}

FOLDER = "semantic_data/abstractIngredients"


def check_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        validate(instance=data, schema=SCHEMA)
        return True, None
    except ValidationError as e:
        path = '.'.join(str(p) for p in e.path) if e.path else 'корень'
        return False, f"{path}: {e.message}"
    except json.JSONDecodeError as e:
        return False, f"Ошибка парсинга JSON: {e}"
    except Exception as e:
        return False, str(e)


def main():
    if not os.path.exists(FOLDER):
        print(f"❌ Папка {FOLDER} не найдена!")
        return

    files = glob.glob(os.path.join(FOLDER, "*.json"))
    print(f"🔍 Проверка {len(files)} файлов...\n")

    valid = []
    invalid = []

    for f in files:
        ok, error = check_file(f)
        filename = os.path.basename(f)
        if ok:
            valid.append(filename)
        else:
            invalid.append((filename, error))

    print("=" * 80)
    print(f"✅ Валидных:  {len(valid)}")
    print(f"❌ Невалидных: {len(invalid)}")
    print("=" * 80)

    if invalid:
        print("\nСписок проблемных файлов:")
        for filename, error in invalid:
            print(f"  ❌ {filename}")
            print(f"     Ошибка: {error}\n")


if __name__ == "__main__":
    main()