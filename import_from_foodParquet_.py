import duckdb
import os

file_path = './food.parquet'  # или где лежит файл

# Проверяем существование
if not os.path.exists(file_path):
    print(f"❌ Файл не найден: {file_path}")
    exit()

conn = duckdb.connect()

# Сначала посмотрим структуру product_name
sample = conn.execute(f"""
    SELECT product_name 
    FROM '{file_path}' 
    WHERE product_name IS NOT NULL 
    LIMIT 5
""").fetchall()

print("📋 Примеры структуры product_name:")
for row in sample:
    print(f"  {row[0]}")
    print()

# Экспортируем с правильным извлечением текста
conn.execute(f"""
    COPY (
        SELECT 
            code,
            product_name[1].text as product_name,
            brands,
            quantity,
            categories,
            ingredients_text,
            nutriscore_grade,
            nova_group,
            countries_tags
        FROM '{file_path}'
        WHERE array_contains(countries_tags, 'en:russia') 
           OR array_contains(countries_tags, 'en:russian-federation')
        LIMIT 5000
    ) TO 'russian_products.csv' (HEADER, DELIMITER ',')
""")

print("✅ Экспортировано в russian_products.csv")