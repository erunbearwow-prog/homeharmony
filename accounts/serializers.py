
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import User, FamilyGroup, FamilyMembership, UserProfile

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для пользователя"""
    display_name = serializers.ReadOnlyField()
    has_phone = serializers.ReadOnlyField()
    has_email = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'phone_number',
            'first_name', 'last_name', 'display_name',
            'avatar', 'bio', 'birth_date',
            'language', 'user_timezone', 'notifications_enabled',
            'phone_verified', 'email_verified',
            'last_activity', 'date_joined',
            'has_phone', 'has_email',
        ]
        read_only_fields = ['id', 'date_joined', 'last_activity']


class FamilyGroupSerializer(serializers.ModelSerializer):
    """Сериализатор для семейной группы"""
    member_count = serializers.ReadOnlyField()
    owner_name = serializers.ReadOnlyField(source='owner.display_name')

    class Meta:
        model = FamilyGroup
        fields = [
            'id', 'name', 'description', 'avatar',
            'owner', 'owner_name',
            'is_active', 'created_at', 'updated_at',
            'member_count',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class FamilyMembershipSerializer(serializers.ModelSerializer):
    """Сериализатор для участия в группе"""
    user_name = serializers.ReadOnlyField(source='user.display_name')
    group_name = serializers.ReadOnlyField(source='family_group.name')
    invited_by_name = serializers.ReadOnlyField(source='invited_by.display_name')

    class Meta:
        model = FamilyMembership
        fields = [
            'id', 'user', 'user_name',
            'family_group', 'group_name',
            'role', 'joined_at',
            'invited_by', 'invited_by_name',
            'is_active',
        ]
        read_only_fields = ['id', 'joined_at']


class UserProfileSerializer(serializers.ModelSerializer):
    """Сериализатор для профиля пользователя"""
    user_name = serializers.ReadOnlyField(source='user.display_name')

    class Meta:
        model = UserProfile
        fields = '__all__'
        read_only_fields = ['id', 'user']


class AuthSerializer(serializers.Serializer):
    """Сериализатор для аутентификации"""
    
    email = serializers.EmailField(required=False)
    phone = serializers.CharField(required=False)
    password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        required=False
    )
    otp = serializers.CharField(
        max_length=6,
        required=False,
        help_text="Код подтверждения (для входа по телефону)"
    )
    
    def validate(self, data):
        """Проверяем, что указан хотя бы один способ входа"""
        if not data.get('email') and not data.get('phone'):
            raise serializers.ValidationError(
                "Укажите email или телефон"
            )
        
        # Для входа по телефону нужен OTP
        if data.get('phone') and not data.get('otp'):
            raise serializers.ValidationError(
                "Для входа по телефону укажите код подтверждения"
            )
        
        # Для входа по email нужен пароль
        if data.get('email') and not data.get('password'):
            raise serializers.ValidationError(
                "Для входа по email укажите пароль"
            )
        
        return data


class PhoneAuthSerializer(serializers.Serializer):
    """Сериализатор для аутентификации по телефону"""
    
    phone = serializers.CharField(
        required=True,
        help_text="Номер телефона"
    )
    otp = serializers.CharField(
        max_length=6,
        required=False,
        help_text="Код подтверждения"
    )
    
    def validate_phone(self, value):
        """Валидация номера телефона"""
        from .validators import validate_phone_number
        validate_phone_number(value)
        return value
