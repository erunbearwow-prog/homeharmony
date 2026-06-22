# accounts/backends/phone_backend.py

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()


class PhoneBackend(ModelBackend):
    """Аутентификация по номеру телефона"""

    def authenticate(self, request, username=None, password=None, **kwargs):
        phone_number = kwargs.get('phone_number') or username

        if not phone_number:
            return None

        try:
            user = User.objects.get(
                Q(phone_number=phone_number) | Q(username=phone_number)
            )
        except User.DoesNotExist:
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user

        return None


