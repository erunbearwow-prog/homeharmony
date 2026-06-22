# test_phone_auth.py

from accounts.services.phone_auth_service import PhoneAuthService
from django.contrib.auth import get_user_model
from django.core.cache import cache

User = get_user_model()

print("=" * 60)
print("🧪 ТЕСТИРОВАНИЕ PHONE AUTH SERVICE")
print("=" * 60)

# 1. Тест генерации OTP
print("\n1️⃣ Тест генерации OTP:")
otp = PhoneAuthService.generate_otp("+79991234567")
print(f"   ✅ OTP сгенерирован: {otp}")
print(f"   ✅ Длина: {len(otp)} (должно быть 6)")

# 2. Тест отправки OTP
print("\n2️⃣ Тест отправки OTP:")
result = PhoneAuthService.send_otp("+79991234567")
print(f"   Результат: {result}")
print(f"   ✅ success: {result['success']}")
print(f"   ✅ message: {result['message']}")
print(f"   ✅ otp: {result['otp']}")

# 3. Тест валидации телефона
print("\n3️⃣ Тест валидации телефона:")
from accounts.validators.phone_validator import validate_phone_number

test_phones = [
    ("+79991234567", True),
    ("79991234567", True),
    ("89123456789", True),
    ("12345", False),
    ("+7999", False),
]

for phone, expected in test_phones:
    try:
        validate_phone_number(phone)
        valid = True
    except:
        valid = False

    status = "✅" if valid == expected else "❌"
    print(f"   {status} {phone} → {valid} (ожидалось: {expected})")

# 4. Тест регистрации (если пользователь не существует)
print("\n4️⃣ Тест регистрации:")
phone = "+79991234567"

# Проверяем, существует ли пользователь
user_exists = User.objects.filter(phone_number=phone).exists()
print(f"   Пользователь с телефоном {phone} существует: {user_exists}")

if not user_exists:
    result = PhoneAuthService.register(phone)
    print(f"   Результат регистрации: {result}")
    print(f"   ✅ success: {result['success']}")
    print(f"   ✅ message: {result['message']}")
    print(f"   ✅ otp_sent: {result.get('otp_sent', False)}")
else:
    print(f"   ⚠️ Пользователь уже существует, пропускаем регистрацию")

# 5. Тест верификации OTP
print("\n5️⃣ Тест верификации OTP:")
otp = PhoneAuthService.generate_otp(phone)
print(f"   Сгенерирован OTP: {otp}")

# Правильный OTP
result = PhoneAuthService.verify_otp(phone, otp)
print(f"   ✅ Правильный OTP: {result} (должно быть True)")

# Неправильный OTP
result = PhoneAuthService.verify_otp(phone, "123456")
print(f"   ❌ Неправильный OTP: {result} (должно быть False)")

# 6. Тест входа
print("\n6️⃣ Тест входа:")

if not user_exists:
    # Создаем пользователя для теста
    user = User.objects.create_user(
        username="test_user",
        phone_number=phone,
        password="testpass123",
        first_name="Test",
        last_name="User"
    )
    user.phone_verified = False
    user.save()
    print(f"   ✅ Создан тестовый пользователь: {user}")

# Генерируем OTP для входа
otp = PhoneAuthService.generate_otp(phone)
print(f"   OTP для входа: {otp}")

# Вход с правильным OTP
user = PhoneAuthService.login(phone, otp)
if user:
    print(f"   ✅ Вход успешен! Пользователь: {user.display_name}")
    print(f"   ✅ phone_verified: {user.phone_verified}")
    print(f"   ✅ last_activity: {user.last_activity}")
else:
    print(f"   ❌ Вход не удался")

# Вход с неправильным OTP
user = PhoneAuthService.login(phone, "000000")
if user:
    print(f"   ❌ Вход с неправильным OTP не должен работать!")
else:
    print(f"   ✅ Вход с неправильным OTP отклонен (корректно)")

# 7. Тест повторной отправки OTP
print("\n7️⃣ Тест повторной отправки OTP:")
result = PhoneAuthService.resend_otp(phone)
print(f"   Результат: {result}")
print(f"   ✅ success: {result['success']}")
print(f"   ✅ message: {result['message']}")

print("\n" + "=" * 60)
print("✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
print("=" * 60)