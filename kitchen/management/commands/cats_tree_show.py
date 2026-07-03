from kitchen.models import IngredientCategory


def print_tree(category, prefix="", is_last=True, max_depth=3):
    connector = "└── " if is_last else "├── "
    print(f"{prefix}{connector}📁 {category.name} (ID: {category.id})")

    if max_depth <= 0:
        return

    children = category.children.all().order_by('name')
    child_list = list(children)
    for idx, child in enumerate(child_list):
        new_prefix = prefix + ("    " if is_last else "│   ")
        is_last_child = (idx == len(child_list) - 1)
        print_tree(child, new_prefix, is_last_child, max_depth - 1)


# Выводим все корневые категории
roots = IngredientCategory.objects.filter(parent__isnull=True).order_by('name')
print("📊 ТЕКУЩАЯ ИЕРАРХИЯ КАТЕГОРИЙ:")
print("=" * 50)
for root in roots:
    print_tree(root, max_depth=3)
    print()