# create_palettes.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'homeharmony.settings')
django.setup()

from core.models import LogoColors

def create_palettes():
    # Деактивируем все существующие палитры
    LogoColors.objects.update(is_active=False)

    # Данные палитр (с прозрачностью)
    palettes = [
        {
            'name': 'Платиновый',
            'circle_fill': '#A8B5C0',
            'circle_stroke': '#6B7A8A',
            'circle_opacity': 0.90,
            'curved_top_fill': '#F5F7FA',
            'curved_top_opacity': 1.0,
            'bottom_triangle_fill': '#F5F7FA',
            'bottom_triangle_opacity': 1.0,
            'left_top_fill': '#D5DCE4',
            'left_top_opacity': 1.0,
            'right_top_fill': '#D0D4D8',
            'right_top_opacity': 1.0,
            'curved_left_fill': '#B8C0C8',
            'curved_left_opacity': 1.0,
            'curved_right_fill': '#A0AAB4',
            'curved_right_opacity': 1.0,
            'stroke_color': '#808A94',
            'stroke_width': 0.6,
            'stroke_opacity': 0.3,
            'is_active': False,
        },
        {
            'name': 'Бордовый',
            'circle_fill': '#8B1A1A',
            'circle_stroke': '#6B1010',
            'circle_opacity': 0.90,
            'curved_top_fill': '#F9F6F0',
            'curved_top_opacity': 1.0,
            'bottom_triangle_fill': '#F9F6F0',
            'bottom_triangle_opacity': 1.0,
            'left_top_fill': '#E8DCD0',
            'left_top_opacity': 1.0,
            'right_top_fill': '#DFD6CC',
            'right_top_opacity': 1.0,
            'curved_left_fill': '#D0C4B8',
            'curved_left_opacity': 1.0,
            'curved_right_fill': '#C8BDB0',
            'curved_right_opacity': 1.0,
            'stroke_color': '#6B5A4E',
            'stroke_width': 0.7,
            'stroke_opacity': 0.25,
            'is_active': False,
        },
        {
            'name': 'Оливковый',
            'circle_fill': '#7A8B5E',
            'circle_stroke': '#5C6B46',
            'circle_opacity': 0.92,
            'curved_top_fill': '#F5F4EE',
            'curved_top_opacity': 1.0,
            'bottom_triangle_fill': '#F5F4EE',
            'bottom_triangle_opacity': 1.0,
            'left_top_fill': '#E2DED0',
            'left_top_opacity': 1.0,
            'right_top_fill': '#D8D6CC',
            'right_top_opacity': 1.0,
            'curved_left_fill': '#C8C4B8',
            'curved_left_opacity': 1.0,
            'curved_right_fill': '#B8BAB0',
            'curved_right_opacity': 1.0,
            'stroke_color': '#6B7A5A',
            'stroke_width': 0.6,
            'stroke_opacity': 0.3,
            'is_active': False,
        },
    ]

    # Создаём палитры
    created = 0
    for palette_data in palettes:
        obj, is_new = LogoColors.objects.get_or_create(
            name=palette_data['name'],
            defaults=palette_data
        )
        if is_new:
            created += 1
            print(f"✅ Создана пали