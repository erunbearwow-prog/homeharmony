import duckdb
import os

# Путь к файлу
file_path = 'food.parquet'
if not os.path.exists(file_path):
    downloads = '/Users/dmitry/Downloads/food.parquet'
    if os.path.exists(downloads):
        file_path = downloads
        print(f"✅ Файл найден: {file_path}")
    else:
        print("❌ Файл не найден")

conn = duckdb.connect()

# Посмотрим, какие колонки реально существуют
print("Доступные колонки:")
columns = conn.execute(f"SELECT * FROM '{file_path}' LIMIT 0").fetchdf().columns.tolist()
for col in columns[:20]:
    print(f"  - {col}")

# Экспорт русских продуктов (используем countries_tags)
conn.execute(f"""
    COPY (
        SELECT 
            product_name,
            brands,
            categories,
            ingredients_text,
            countries_tags,
            quantity,
            nutriscore_grade,
            nova_group
        FROM '{file_path}'
        WHERE list_contains(countries_tags, 'en:russia') OR list_contains(countries_tags, 'en:russian-federation')
        LIMIT 10000
    ) TO 'russian_products.csv' (HEADER, DELIMITER ',')
""")

print("✅ Экспортировано в russian_products.csv")

# Проверим результат
result = conn.execute("SELECT COUNT(*) FROM 'russian_products.csv'").fetchone()[0]
print(f"📊 Экспортировано строк: {result}")