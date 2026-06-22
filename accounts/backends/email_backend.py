# accounts/backends/emil_backend.py

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()

class EmailBackend(ModelBackend):
    """Аутентификация по email"""

    def authenticate(self, request, username=None, password=None, **kwargs):
        email = kwargs.get('email') or username

        if not email:
            return None

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user

        return None


class MultiAuthBackend(ModelBackend):
    """Комбинированная аутентификация (phone OR email)"""

    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username:
            return None

        # Пробуем найти по телефону или email
        user = None
        try:
            user = User.objects.get(
                Q(phone_number=username) | Q(email=username)
            )
        except User.DoesNotExist:
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user

        return None