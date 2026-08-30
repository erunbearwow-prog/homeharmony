markdown
# 📘 Руководство по организации тем в Django + Tailwind проекте

## 🎯 Цель
Централизованное управление цветовой схемой проекта через CSS-переменные, чтобы менять тему можно было в одном месте без правки всех шаблонов.

---

## 📁 Структура проекта (рекомендуемая)
project/
├── static/
│ └── css/
│ ├── style.css # Основной файл стилей с переменными
│ ├── theme.css # (опционально) отдельный файл для тем
│ └── components/ # (опционально) компонентные стили
├── templates/
│ ├── base.html # Базовый шаблон
│ └── includes/ # Включаемые части
│ ├── navigation.html
│ └── footer.html
└── theme_config/ # (опционально) для админки темы
├── models.py
└── context_processors.py

text

---

## 🎨 Шаг 1. CSS-переменные

Добавьте в начало вашего `static/css/style.css`:

```css
/* ==========================================================
   ТЕМА (ЦВЕТОВАЯ СХЕМА ПРОЕКТА)
   ========================================================== */
:root {
  /* ===== ОСНОВНОЙ ЦВЕТ (янтарный) ===== */
  --primary: #d97706;           /* основной цвет */
  --primary-dark: #b45309;      /* тёмный вариант */
  --primary-darker: #92400e;    /* ещё темнее */
  --primary-light: #fef3c7;     /* светлый фон */
  --primary-lighter: #fffbeb;   /* очень светлый */
  --primary-border: #fde68a;    /* граница */
  --primary-text: #b45309;      /* текст на основном цвете */
  --primary-text-light: #92400e; /* текст светлее */
  --primary-accent: #f59e0b;    /* акцент */
  --primary-rgb: 217, 119, 6;   /* RGB для прозрачности */

  /* ===== ВТОРИЧНЫЙ ЦВЕТ (для про-режима) ===== */
  --secondary: #2563eb;
  --secondary-dark: #1d4ed8;
  --secondary-light: #dbeafe;
  --secondary-bg: #eff6ff;
  --secondary-border: #bfdbfe;

  /* ===== ЦВЕТА ФОНА ===== */
  --bg-body: #ffffff;
  --bg-navbar: rgba(255, 255, 255, 0.9);
  --bg-footer: #111827;
  --bg-card: #ffffff;
  --bg-gray-50: #f9fafb;
  --bg-gray-100: #f3f4f6;
  --bg-gray-200: #e5e7eb;
  --bg-overlay: rgba(0, 0, 0, 0.4);
  --bg-overlay-dark: rgba(0, 0, 0, 0.5);

  /* ===== ЦВЕТА ТЕКСТА ===== */
  --text-primary: #1f2937;
  --text-secondary: #4b5563;
  --text-muted: #6b7280;
  --text-light: #9ca3af;
  --text-white: #ffffff;
  --text-footer: #d1d5db;

  /* ===== ЦВЕТА ГРАНИЦ ===== */
  --border-light: #f3f4f6;
  --border-medium: #e5e7eb;
  --border-dark: #d1d5db;
  --border-primary: #fde68a;

  /* ===== ЦВЕТА ТЕГОВ ===== */
  --tag-amber-bg: #fef3c7;
  --tag-amber-text: #92400e;
  --tag-green-bg: #dcfce7;
  --tag-green-text: #166534;
  --tag-blue-bg: #dbeafe;
  --tag-blue-text: #1e40af;
  --tag-purple-bg: #f3e8ff;
  --tag-purple-text: #6b21a5;
  --tag-indigo-bg: #e0e7ff;
  --tag-indigo-text: #3730a3;
  --tag-pink-bg: #fce7f3;
  --tag-pink-text: #9d174d;
  --tag-teal-bg: #ccfbf1;
  --tag-teal-text: #0f766e;

  /* ===== КНОПКИ ===== */
  --btn-primary-bg: var(--primary);
  --btn-primary-text: var(--text-white);
  --btn-primary-hover: var(--primary-darker);
  --btn-secondary-bg: var(--bg-body);
  --btn-secondary-text: var(--primary-darker);
  --btn-secondary-border: var(--primary-border);
  --btn-secondary-hover: var(--primary-lighter);

  /* ===== ГРАДИЕНТЫ ===== */
  --gradient-hero: linear-gradient(135deg, #fdf8f0 0%, #f0f4f0 100%);
  --gradient-primary: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);

  /* ===== ТЕНИ ===== */
  --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
  --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1);

  /* ===== ШРИФТЫ ===== */
  --font-sans: 'Inter', sans-serif;
  --font-serif: 'Georgia', serif;
  --font-mono: 'Courier New', monospace;

  /* ===== РАЗМЕРЫ ===== */
  --radius-sm: 0.375rem;
  --radius-md: 0.5rem;
  --radius-lg: 0.75rem;
  --radius-xl: 1rem;
  --radius-full: 9999px;
  --container-max: 1280px;
  --navbar-height: 64px;

  /* ===== ОТСТУПЫ ===== */
  --sp-1: 0.25rem;
  --sp-2: 0.5rem;
  --sp-3: 0.75rem;
  --sp-4: 1rem;
  --sp-6: 1.5rem;
  --sp-8: 2rem;
  --sp-12: 3rem;
  --sp-16: 4rem;

  /* ===== АНИМАЦИИ ===== */
  --transition-fast: 0.15s ease;
  --transition-normal: 0.3s ease;
  --transition-slow: 0.5s ease;
}
🔧 Шаг 2. Как переписать CSS на переменные
Пример 1: Кнопки
css
/* БЫЛО */
.btn-primary {
    background-color: #d97706;
    color: white;
    padding: 0.75rem 1.5rem;
}
.btn-primary:hover {
    background-color: #b45309;
}

/* СТАЛО */
.btn-primary {
    background-color: var(--primary);
    color: var(--text-white);
    padding: var(--sp-3) var(--sp-6);
    border-radius: var(--radius-md);
    font-weight: 600;
    transition: background-color var(--transition-fast);
    border: none;
    cursor: pointer;
}
.btn-primary:hover {
    background-color: var(--primary-dark);
}
Пример 2: Навигация
css
/* БЫЛО */
.navbar {
    background-color: rgba(255, 255, 255, 0.9);
    border-bottom: 1px solid #f3f4f6;
}
.logo-icon {
    color: #d97706;
}

/* СТАЛО */
.navbar {
    background-color: var(--bg-navbar);
    border-bottom: 1px solid var(--border-light);
}
.logo-icon {
    color: var(--primary);
}
Пример 3: Карточки
css
/* БЫЛО */
.card {
    background-color: white;
    border: 1px solid #f3f4f6;
    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
    transition: all 0.3s ease;
}
.card:hover {
    transform: translateY(-5px);
    box-shadow: 0 20px 25px -12px rgba(0, 0, 0, 0.1);
}

/* СТАЛО */
.card {
    background-color: var(--bg-card);
    border: 1px solid var(--border-light);
    box-shadow: var(--shadow-sm);
    transition: all var(--transition-normal);
}
.card:hover {
    transform: translateY(-5px);
    box-shadow: var(--shadow-lg);
}
Пример 4: Теги
css
/* БЫЛО */
.tag-amber {
    background-color: #fef3c7;
    color: #92400e;
}

/* СТАЛО */
.tag-amber {
    background-color: var(--tag-amber-bg);
    color: var(--tag-amber-text);
}
🌐 Шаг 3. Использование в шаблонах Django
В базовом шаблоне (base.html)
html
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}{% endblock %}</title>
    
    <!-- Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com"></script>
    
    <!-- Основные стили с переменными -->
    <link rel="stylesheet" href="{% static 'css/style.css' %}">
    
    <!-- Переменные темы из админки (опционально) -->
    {% if theme_css %}
    <style>{{ theme_css|safe }}</style>
    {% endif %}
    
    {% block extra_css %}{% endblock %}
</head>
<body class="bg-[var(--bg-body)] text-[var(--text-primary)]">
    <!-- Контент -->
</body>
</html>
Пример с Tailwind классами
html
<!-- БЫЛО -->
<button class="bg-amber-600 text-white px-6 py-3 rounded-lg hover:bg-amber-700 transition">
    Перейти к рецептам
</button>

<!-- СТАЛО (через CSS-переменные) -->
<button class="bg-[var(--primary)] text-[var(--text-white)] px-6 py-3 rounded-lg hover:bg-[var(--primary-dark)] transition">
    Перейти к рецептам
</button>

<!-- ИЛИ через кастомный класс -->
<button class="btn-primary">
    Перейти к рецептам
</button>
Пример с текстом
html
<!-- БЫЛО -->
<h1 class="text-gray-800">Заголовок</h1>
<p class="text-gray-500">Описание</p>

<!-- СТАЛО -->
<h1 class="text-[var(--text-primary)]">Заголовок</h1>
<p class="text-[var(--text-muted)]">Описание</p>
Пример с фоном
html
<!-- БЫЛО -->
<section class="bg-white p-6 rounded-xl border border-gray-100">

<!-- СТАЛО -->
<section class="bg-[var(--bg-card)] p-6 rounded-xl border border-[var(--border-light)]">
🚀 Шаг 4. Массовая замена в проекте
VS Code (Поиск и замена с Regular Expression)
Найти (Regex)	Заменить	Пояснение
bg-amber-600	bg-[var(--primary)]	Основной фон
bg-amber-700	bg-[var(--primary-dark)]	Тёмный фон
hover:bg-amber-700	hover:bg-[var(--primary-dark)]	Hover
hover:bg-amber-800	hover:bg-[var(--primary-darker)]	Более тёмный hover
text-amber-700	text-[var(--primary-text)]	Текст
text-amber-800	text-[var(--primary-text-light)]	Светлый текст
border-amber-200	border-[var(--primary-border)]	Граница
bg-amber-100	bg-[var(--primary-light)]	Светлый фон
bg-amber-50	bg-[var(--primary-lighter)]	Очень светлый фон
text-gray-800	text-[var(--text-primary)]	Основной текст
text-gray-600	text-[var(--text-secondary)]	Второстепенный текст
text-gray-500	text-[var(--text-muted)]	Серый текст
bg-white	bg-[var(--bg-card)]	Фон карточек
border-gray-100	border-[var(--border-light)]	Светлая граница
border-gray-200	border-[var(--border-medium)]	Средняя граница
Linux/macOS (замена во всех файлах)
bash
# Замена во всех HTML-шаблонах
find ./templates -name "*.html" -exec sed -i 's/bg-amber-600/bg-\[var\(--primary\)\]/g' {} \;
find ./templates -name "*.html" -exec sed -i 's/hover:bg-amber-700/hover:bg-\[var\(--primary-dark\)\]/g' {} \;
🎛️ Шаг 5. Переключение тем (JavaScript)
Базовое переключение
javascript
// theme.js
function setTheme(themeName) {
    // Сохраняем выбор
    localStorage.setItem('theme', themeName);
    
    // Применяем тему
    if (themeName === 'dark') {
        document.documentElement.style.setProperty('--bg-body', '#1a202c');
        document.documentElement.style.setProperty('--text-primary', '#f7fafc');
        document.documentElement.style.setProperty('--bg-card', '#2d3748');
        document.documentElement.style.setProperty('--border-light', '#4a5568');
        // ... остальные переменные
    } else {
        // Возвращаем светлую тему
        document.documentElement.style.setProperty('--bg-body', '#ffffff');
        document.documentElement.style.setProperty('--text-primary', '#1f2937');
        document.documentElement.style.setProperty('--bg-card', '#ffffff');
        document.documentElement.style.setProperty('--border-light', '#f3f4f6');
        // ... остальные переменные
    }
}

// Восстановление сохранённой темы
const savedTheme = localStorage.getItem('theme') || 'light';
setTheme(savedTheme);
Переключатель в шаблоне
html
<button onclick="toggleTheme()" class="p-2 rounded-full hover:bg-[var(--bg-gray-100)]">
    <i class="fas fa-moon" id="themeIcon"></i>
</button>

<script>
function toggleTheme() {
    const current = localStorage.getItem('theme') || 'light';
    const next = current === 'light' ? 'dark' : 'light';
    setTheme(next);
    
    // Меняем иконку
    const icon = document.getElementById('themeIcon');
    icon.className = next === 'light' ? 'fas fa-moon' : 'fas fa-sun';
}
</script>
🗄️ Шаг 6. Хранение тем в Django (Админка)
Модель для тем
python
# models.py
from django.db import models

class Theme(models.Model):
    name = models.CharField('Название', max_length=100)
    is_active = models.BooleanField('Активна', default=False)
    
    # Основные цвета
    primary = models.CharField(max_length=7, default='#d97706')
    primary_dark = models.CharField(max_length=7, default='#b45309')
    primary_darker = models.CharField(max_length=7, default='#92400e')
    primary_light = models.CharField(max_length=7, default='#fef3c7')
    
    # Текст
    text_primary = models.CharField(max_length=7, default='#1f2937')
    text_secondary = models.CharField(max_length=7, default='#4b5563')
    text_muted = models.CharField(max_length=7, default='#6b7280')
    
    # Фоны
    bg_body = models.CharField(max_length=7, default='#ffffff')
    bg_card = models.CharField(max_length=7, default='#ffffff')
    
    def css_variables(self):
        return f"""
        :root {{
            --primary: {self.primary};
            --primary-dark: {self.primary_dark};
            --primary-darker: {self.primary_darker};
            --primary-light: {self.primary_light};
            --text-primary: {self.text_primary};
            --text-secondary: {self.text_secondary};
            --text-muted: {self.text_muted};
            --bg-body: {self.bg_body};
            --bg-card: {self.bg_card};
        }}
        """
Context Processor для темы
python
# context_processors.py
from .models import Theme

def theme_variables(request):
    try:
        theme = Theme.objects.get(is_active=True)
        return {'theme_css': theme.css_variables()}
    except Theme.DoesNotExist:
        return {'theme_css': ''}
Добавление в настройки
python
# settings.py
TEMPLATES = [
    {
        # ...
        'OPTIONS': {
            'context_processors': [
                # ...
                'your_app.context_processors.theme_variables',
            ],
        },
    },
]
📝 Шаг 7. Чек-лист замены цветов
Пройдите по всем элементам и отметьте заменённые:

Элемент	Было	Стало	✅
Основные кнопки	bg-amber-600 → hover:bg-amber-700	var(--primary) → var(--primary-dark)	☐
Вторичные кнопки	border-amber-200 → hover:bg-amber-50	var(--primary-border) → var(--primary-lighter)	☐
Ссылки в навигации	text-gray-500 → hover:text-amber-600	var(--text-secondary) → var(--primary)	☐
Иконки	text-amber-700	var(--primary-text)	☐
Заголовки	text-gray-800	var(--text-primary)	☐
Текст	text-gray-600	var(--text-secondary)	☐
Карточки	bg-white, border-gray-100	var(--bg-card), var(--border-light)	☐
Теги	bg-amber-100, text-amber-800	var(--tag-amber-bg), var(--tag-amber-text)	☐
Прогресс-бар	bg-amber-600	var(--primary)	☐
Акцентные элементы	text-amber-500	var(--primary-accent)	☐
🎯 Итог: преимущества подхода
✅ Одно место для изменения — меняете цвет в :root и он обновляется везде
✅ Темы через админку — можно создать модель и дать редакторам менять цвета через админку Django
✅ Переключение светлой/тёмной темы — через JavaScript без перезагрузки страницы
✅ Удобная поддержка — новые разработчики сразу видят структуру цветов
✅ Совместимость с Tailwind — через синтаксис bg-[var(--primary)]
✅ Гибкость — можно быстро экспериментировать с новыми цветами

📚 Полезные ссылки
Tailwind CSS — Arbitrary Values

CSS Custom Properties (MDN)

Django — Context Processors

Сохраните этот файл как THEME_GUIDE.md и используйте как шпаргалку при работе над проектом! 🚀

text

---

Всё готово! Скопируйте весь этот текст и сохраните как `THEME_GUIDE.md` в корне вашего проекта. При необходимости просто открываете и используете как инструкцию. 😊