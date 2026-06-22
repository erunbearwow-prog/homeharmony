# accounts/models.py

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone
from .managers import UserManager
from .validators import validate_phone_number


class User(AbstractUser):
    """Расширенная модель пользователя"""

    # ===== ОСНОВНЫЕ ПОЛЯ =====
    phone_number = models.CharField(
        max_length=20,
        unique=True,
        validators=[validate_phone_number],
        blank=True,
        null=True,
        verbose_name="Номер телефона"
    )
    email = models.EmailField(
        unique=True,
        blank=True,
        null=True,
        verbose_name="Email"
    )
    username = models.CharField(
        max_length=150,
        unique=True,
        blank=True,
        null=True,
        verbose_name="Имя пользователя"
    )

    # ===== ПРОФИЛЬ =====
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
        verbose_name="Аватар"
    )
    bio = models.TextField(
        blank=True,
        verbose_name="О себе"
    )
    birth_date = models.DateField(
        blank=True,
        null=True,
        verbose_name="Дата рождения"
    )

    # ===== НАСТРОЙКИ =====
    language = models.CharField(
        max_length=2,
        choices=[('ru', 'Русский'), ('en', 'English')],
        default='ru',
        verbose_name="Язык"
    )
    user_timezone = models.CharField(
        max_length=50,
        default='Europe/Moscow',
        verbose_name="Часовой пояс"
    )
    notifications_enabled = models.BooleanField(
        default=True,
        verbose_name="Уведомления включены"
    )

    # ===== ВЕРИФИКАЦИЯ =====
    phone_verified = models.BooleanField(
        default=False,
        verbose_name="Телефон подтвержден"
    )
    email_verified = models.BooleanField(
        default=False,
        verbose_name="Email подтвержден"
    )

    # ===== ДАТЫ =====
    last_activity = models.DateTimeField(
        default=timezone.now,
        verbose_name="Последняя активность"
    )

    # ===== ПЕРЕОПРЕДЕЛЯЕМ ПОЛЯ ДЛЯ ИЗБЕЖАНИЯ КОНФЛИКТА =====
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='accounts_user_set',
        blank=True,
        verbose_name='groups',
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        related_query_name='accounts_user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='accounts_user_set',
        blank=True,
        verbose_name='user permissions',
        help_text='Specific permissions for this user.',
        related_query_name='accounts_user',
    )

    # ===== МЕНЕДЖЕР =====
    objects = UserManager()

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ['-date_joined']
        indexes = [
            models.Index(fields=['phone_number']),
            models.Index(fields=['email']),
            models.Index(fields=['username']),
        ]

    def __str__(self):
        if self.phone_number:
            return self.phone_number
        if self.email:
            return self.email
        return self.username or f"User #{self.id}"

    @property
    def display_name(self):
        """Имя для отображения"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        if self.first_name:
            return self.first_name
        if self.username:
            return self.username
        if self.phone_number:
            return self.phone_number
        if self.email:
            return self.email
        return f"User #{self.id}"

    @property
    def has_phone(self):
        return bool(self.phone_number and self.phone_verified)

    @property
    def has_email(self):
        return bool(self.email and self.email_verified)


class FamilyGroup(models.Model):
    """Семейная группа"""

    # ===== ОСНОВНЫЕ ПОЛЯ =====
    name = models.CharField(
        max_length=100,
        verbose_name="Название группы"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Описание"
    )
    avatar = models.ImageField(
        upload_to='family_groups/',
        blank=True,
        null=True,
        verbose_name="Аватар"
    )

    # ===== ВЛАДЕЛЕЦ =====
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='owned_family_groups',
        verbose_name="Владелец"
    )

    # ===== УЧАСТНИКИ =====
    members = models.ManyToManyField(
        User,
        through='FamilyMembership',
        through_fields=('family_group', 'user'),
        verbose_name="Участники"
    )

    # ===== НАСТРОЙКИ =====
    is_active = models.BooleanField(
        default=True,
        verbose_name="Активна"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата обновления"
    )

    class Meta:
        verbose_name = "Семейная группа"
        verbose_name_plural = "Семейные группы"
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def get_member_count(self):
        return self.members.count()


class FamilyMembership(models.Model):
    """Участие пользователя в семейной группе"""

    ROLE_CHOICES = [
        ('owner', 'Владелец'),
        ('admin', 'Администратор'),
        ('member', 'Участник'),
        ('viewer', 'Наблюдатель'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='memberships',
        verbose_name="Пользователь"
    )
    family_group = models.ForeignKey(
        FamilyGroup,
        on_delete=models.CASCADE,
        related_name='memberships',
        verbose_name="Семейная группа"
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='member',
        verbose_name="Роль"
    )
    joined_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата присоединения"
    )
    invited_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invited_members',
        verbose_name="Пригласил"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Активен"
    )

    class Meta:
        verbose_name = "Участие в группе"
        verbose_name_plural = "Участия в группах"
        unique_together = ['user', 'family_group']
        ordering = ['-joined_at']

    def __str__(self):
        return f"{self.user.display_name} in {self.family_group.name}"


class UserProfile(models.Model):
    """Дополнительный профиль пользователя"""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name="Пользователь"
    )

    # ===== ПИТАНИЕ =====
    daily_calories = models.PositiveIntegerField(
        default=2000,
        verbose_name="Дневная норма калорий"
    )
    daily_protein = models.PositiveIntegerField(
        default=75,
        verbose_name="Дневная норма белка"
    )
    daily_fat = models.PositiveIntegerField(
        default=70,
        verbose_name="Дневная норма жиров"
    )
    daily_carbohydrates = models.PositiveIntegerField(
        default=250,
        verbose_name="Дневная норма углеводов"
    )

    # ===== АЛЛЕРГИИ И ОГРАНИЧЕНИЯ =====
    allergies = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Аллергии"
    )
    dietary_restrictions = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Диетические ограничения"
    )
    favorite_cuisines = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Любимые кухни"
    )
    disliked_ingredients = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Нелюбимые ингредиенты"
    )

    # ===== СЕМЬЯ =====
    family_members = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Члены семьи"
    )

    # ===== НАСТРОЙКИ =====
    preferred_unit_system = models.CharField(
        max_length=10,
        choices=[('metric', 'Метрическая'), ('imperial', 'Имперская')],
        default='metric',
        verbose_name="Система единиц"
    )
    preferred_serving_size = models.PositiveIntegerField(
        default=1,
        verbose_name="Размер порции"
    )

    class Meta:
        verbose_name = "Профиль пользователя"
        verbose_name_plural = "Профили пользователей"

    def __str__(self):
        return f"Profile for {self.user.display_name}"