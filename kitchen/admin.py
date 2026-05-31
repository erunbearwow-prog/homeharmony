from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import CookingMethod

@admin.register(CookingMethod)
class CookingMethodAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'short_description']
    search_fields = ['name', 'description']
    list_filter = ['category']
    fieldsets = [
        ('Основная информация', {
            'fields': ['name', 'category', 'short_description', 'icon', 'color']
        }),
        ('Подробное описание', {
            'fields': ['description', 'scientific_background']
        }),
        ('Параметры', {
            'fields': ['typical_temperature', 'typical_duration']
        }),
        ('Советы и ошибки', {
            'fields': ['tips', 'common_mistakes', 'advanced_notes']
        }),
    ]