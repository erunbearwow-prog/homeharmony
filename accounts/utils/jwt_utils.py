# accounts/utils/jwt_utils.py

import jwt
from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()


def generate_jwt_tokens(user: User) -> dict:
    """Генерирует JWT токены"""
    access_token = jwt.encode(
        {
            'user_id': user.id,
            'email': user.email,
            'phone': user.phone_number,
            'exp': datetime.utcnow() + timedelta(days=7),
            'iat': datetime.utcnow(),
        },
        settings.SECRET_KEY,
        algorithm='HS256'
    )

    refresh_token = jwt.encode(
        {
            'user_id': user.id,
            'exp': datetime.utcnow() + timedelta(days=30),
            'iat': datetime.utcnow(),
        },
        settings.SECRET_KEY,
        algorithm='HS256'
    )

    return {
        'access': access_token,
        'refresh': refresh_token,
        'token_type': 'Bearer',
        'expires_in': 7 * 24 * 60 * 60,  # 7 дней в секундах
    }


def decode_jwt_token(token: str) -> dict:
    """Декодирует JWT токен"""
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        return {'error': 'Token expired'}
    except jwt.InvalidTokenError:
        return {'error': 'Invalid token'}