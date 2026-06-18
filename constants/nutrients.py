# Словарь всех питательных веществ
NUTRIENTS_MAP = {
    # Энергетическая ценность
    'calories': {
        'name': 'Калорийность',
        'unit': 'ккал',
        'category': 'energy',
        'icon': '🔥'
    },

    # Макронутриенты (БЖУ)
    'protein': {
        'name': 'Белки',
        'unit': 'г',
        'category': 'macros',
        'icon': '🥩'
    },
    'fat': {
        'name': 'Жиры',
        'unit': 'г',
        'category': 'macros',
        'icon': '🧈'
    },
    'carbohydrates': {
        'name': 'Углеводы',
        'unit': 'г',
        'category': 'macros',
        'icon': '🍞'
    },
    'fiber': {
        'name': 'Клетчатка',
        'unit': 'г',
        'category': 'macros',
        'icon': '🌾'
    },
    'sugar': {
        'name': 'Сахар',
        'unit': 'г',
        'category': 'macros',
        'icon': '🍬'
    },

    # Жиры (подробно)
    'saturated_fat': {
        'name': 'Насыщенные жиры',
        'unit': 'г',
        'category': 'fats_detail',
        'icon': '🥓'
    },
    'trans_fat': {
        'name': 'Трансжиры',
        'unit': 'г',
        'category': 'fats_detail',
        'icon': '⚠️'
    },
    'cholesterol': {
        'name': 'Холестерин',
        'unit': 'мг',
        'category': 'fats_detail',
        'icon': '🫀'
    },

    # Витамины
    'vitamin_a': {
        'name': 'Витамин A',
        'unit': 'мкг',
        'category': 'vitamins',
        'icon': '👁️'
    },
    'vitamin_b1': {
        'name': 'Витамин B1 (Тиамин)',
        'unit': 'мг',
        'category': 'vitamins',
        'icon': '🧠'
    },
    'vitamin_b2': {
        'name': 'Витамин B2 (Рибофлавин)',
        'unit': 'мг',
        'category': 'vitamins',
        'icon': '⚡'
    },
    'vitamin_b3': {
        'name': 'Витамин B3 (Ниацин)',
        'unit': 'мг',
        'category': 'vitamins',
        'icon': '💪'
    },
    'vitamin_b6': {
        'name': 'Витамин B6',
        'unit': 'мг',
        'category': 'vitamins',
        'icon': '🧬'
    },
    'vitamin_b9': {
        'name': 'Витамин B9 (Фолиевая кислота)',
        'unit': 'мкг',
        'category': 'vitamins',
        'icon': '🤰'
    },
    'vitamin_b12': {
        'name': 'Витамин B12',
        'unit': 'мкг',
        'category': 'vitamins',
        'icon': '🩸'
    },
    'vitamin_c': {
        'name': 'Витамин C',
        'unit': 'мг',
        'category': 'vitamins',
        'icon': '🍊'
    },
    'vitamin_d': {
        'name': 'Витамин D',
        'unit': 'мкг',
        'category': 'vitamins',
        'icon': '☀️'
    },
    'vitamin_e': {
        'name': 'Витамин E',
        'unit': 'мг',
        'category': 'vitamins',
        'icon': '🌿'
    },
    'vitamin_k': {
        'name': 'Витамин K',
        'unit': 'мкг',
        'category': 'vitamins',
        'icon': '🩹'
    },

    # Минералы
    'calcium': {
        'name': 'Кальций (Ca)',
        'unit': 'мг',
        'category': 'minerals',
        'icon': '🦴'
    },
    'iron': {
        'name': 'Железо (Fe)',
        'unit': 'мг',
        'category': 'minerals',
        'icon': '🩸'
    },
    'magnesium': {
        'name': 'Магний (Mg)',
        'unit': 'мг',
        'category': 'minerals',
        'icon': '💪'
    },
    'phosphorus': {
        'name': 'Фосфор (P)',
        'unit': 'мг',
        'category': 'minerals',
        'icon': '🦷'
    },
    'potassium': {
        'name': 'Калий (K)',
        'unit': 'мг',
        'category': 'minerals',
        'icon': '❤️'
    },
    'sodium': {
        'name': 'Натрий (Na)',
        'unit': 'мг',
        'category': 'minerals',
        'icon': '🧂'
    },
    'zinc': {
        'name': 'Цинк (Zn)',
        'unit': 'мг',
        'category': 'minerals',
        'icon': '🔬'
    },
    'copper': {
        'name': 'Медь (Cu)',
        'unit': 'мкг',
        'category': 'minerals',
        'icon': '🪙'
    },
    'manganese': {
        'name': 'Марганец (Mg)',
        'unit': 'мкг',
        'category': 'minerals',
        'icon': '⚙️'
    },
    'selenium': {
        'name': 'Селен (Se)',
        'unit': 'мкг',
        'category': 'minerals',
        'icon': '🛡️'
    },

    # Дополнительно
    'water': {
        'name': 'Вода',
        'unit': 'г',
        'category': 'other',
        'icon': '💧'
    },
    'ash': {
        'name': 'Зола',
        'unit': 'г',
        'category': 'other',
        'icon': '🧪'
    },
}

# Названия категорий для отображения
CATEGORY_NAMES = {
    'energy': 'Энергетическая ценность',
    'macros': 'Основные нутриенты',
    'fats_detail': 'Детализация жиров',
    'vitamins': 'Витамины',
    'minerals': 'Минералы',
    'other': 'Дополнительно',
}

# Порядок категорий (для сортировки)
CATEGORY_ORDER = ['energy', 'macros', 'fats_detail', 'vitamins', 'minerals', 'other']