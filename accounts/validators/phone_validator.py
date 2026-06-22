# accounts/validators/phone_validator.py

import re
from django.core.exceptions import ValidationError

def validate_phone_number(value):
    """Валидатор номера телефона"""
    # Простая валидация для российских номеров
    pattern = r'^(\+7|7|8)?[\s\-]?\(?[489][0-9]{2}\)?[\s\-]?[0-9]{3}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}$'
    if not re.match(pattern, value):
        raise ValidationError(
            'Номер телефона должен быть в формате: +7 999 123 45 67'
        )
    return value