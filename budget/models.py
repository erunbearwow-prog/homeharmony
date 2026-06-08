from django.db import models
from django.conf import settings


class ExpenseCategory(models.Model):
    """Категория расходов"""
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, default='fa-shopping-cart')
    color = models.CharField(max_length=20, default='#d97706')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    is_default = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = 'Категории расходов'
        ordering = ['name']


class Expense(models.Model):
    """Расход"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='expenses')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(ExpenseCategory, on_delete=models.SET_NULL, null=True)
    date = models.DateField()
    note = models.TextField(blank=True)
    is_recurring = models.BooleanField(default=False)
    recurring_period = models.CharField(max_length=20, blank=True, choices=[
        ('weekly', 'Еженедельно'), ('monthly', 'Ежемесячно'), ('yearly', 'Ежегодно')
    ])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']


class ShoppingItem(models.Model):
    """Позиция списка покупок"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='shopping_items')
    name = models.CharField(max_length=200)
    quantity = models.CharField(max_length=100, blank=True)
    category = models.CharField(max_length=50, blank=True)
    is_checked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['category', 'name']