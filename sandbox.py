import csv

with open('russian_products.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for i, row in enumerate(reader):
        print(f"{i+1}. {row.get('product_name', '')} | {row.get('brands', '')}")
        if i >= 10:
            break