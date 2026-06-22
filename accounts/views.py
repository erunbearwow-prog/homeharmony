# accounts/views.py

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import render
from django.contrib.auth import get_user_model
from .models import FamilyGroup, FamilyMembership, UserProfile
from .serializers import (
    UserSerializer,
    FamilyGroupSerializer,
    FamilyMembershipSerializer,
    UserProfileSerializer,
    AuthSerializer,
    PhoneAuthSerializer
)
from .services.auth_service import AuthService

User = get_user_model()


def profile_page(request):
    return render(request, 'accounts/profile.html')


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления пользователями.

    Доступ:
    - Администратор: видит всех пользователей
    - Обычный пользователь: видит только себя
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Ограничиваем доступ к списку пользователей"""
        if self.request.user.is_superuser:
            return User.objects.all()
        return User.objects.filter(id=self.request.user.id)

    @action(detail=False, methods=['get'])
    def me(self, request):
        """Получить данные текущего пользователя"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['put', 'patch'])
    def update_me(self, request):
        """Обновить данные текущего пользователя"""
        user = request.user
        serializer = self.get_serializer(
            user,
            data=request.data,
            partial=request.method == 'PATCH'
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FamilyGroupViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления семейными группами.

    Пользователь может:
    - Создавать группы (становится владельцем)
    - Просматривать группы, в которых состоит
    - Управлять своими группами
    """

    queryset = FamilyGroup.objects.all()
    serializer_class = FamilyGroupSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Показываем только группы, где пользователь состоит"""
        return self.queryset.filter(members=self.request.user)

    def perform_create(self, serializer):
        """При создании группы пользователь становится владельцем"""
        group = serializer.save(owner=self.request.user)
        # Добавляем владельца в участники
        FamilyMembership.objects.get_or_create(
            user=self.request.user,
            family_group=group,
            defaults={'role': 'owner'}
        )

    @action(detail=True, methods=['post'])
    def add_member(self, request, pk=None):
        """Добавить участника в группу"""
        group = self.get_object()

        # Проверяем, что пользователь имеет право добавлять
        if group.owner != request.user and not request.user.is_superuser:
            return Response(
                {'error': 'Только владелец группы может добавлять участников'},
                status=status.HTTP_403_FORBIDDEN
            )

        user_id = request.data.get('user_id')
        role = request.data.get('role', 'member')

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'Пользователь не найден'},
                status=status.HTTP_404_NOT_FOUND
            )

        membership, created = FamilyMembership.objects.get_or_create(
            user=user,
            family_group=group,
            defaults={
                'role': role,
                'invited_by': request.user
            }
        )

        if not created:
            return Response(
                {'message': 'Пользователь уже состоит в группе'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = FamilyMembershipSerializer(membership)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def remove_member(self, request, pk=None):
        """Удалить участника из группы"""
        group = self.get_object()

        if group.owner != request.user and not request.user.is_superuser:
            return Response(
                {'error': 'Только владелец группы может удалять участников'},
                status=status.HTTP_403_FORBIDDEN
            )

        user_id = request.data.get('user_id')

        if user_id == str(request.user.id):
            return Response(
                {'error': 'Владелец не может удалить себя из группы'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            membership = FamilyMembership.objects.get(
                user_id=user_id,
                family_group=group
            )
            membership.delete()
            return Response({'message': 'Участник удален из группы'})
        except FamilyMembership.DoesNotExist:
            return Response(
                {'error': 'Участник не найден в группе'},
                status=status.HTTP_404_NOT_FOUND
            )


class FamilyMembershipViewSet(viewsets.ModelViewSet):
    """ViewSet для управления участием в группах"""

    queryset = FamilyMembership.objects.all()
    serializer_class = FamilyMembershipSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Показываем только свои участия"""
        return self.queryset.filter(user=self.request.user)

    @action(detail=False, methods=['get'])
    def my_groups(self, request):
        """Получить все группы пользователя"""
        memberships = self.get_queryset().select_related('family_group')
        serializer = self.get_serializer(memberships, many=True)
        return Response(serializer.data)


class UserProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления профилями пользователей.

    Каждый пользователь имеет один профиль с настройками:
    - Дневные нормы КБЖУ
    - Аллергии и ограничения
    - Предпочтения
    """

    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Показываем только свой профиль"""
        return self.queryset.filter(user=self.request.user)

    @action(detail=False, methods=['get'])
    def me(self, request):
        """Получить или создать профиль текущего пользователя"""
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        serializer = self.get_serializer(profile)
        return Response(serializer.data)

    @action(detail=False, methods=['put', 'patch'])
    def update_me(self, request):
        """Обновить профиль текущего пользователя"""
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        serializer = self.get_serializer(
            profile,
            data=request.data,
            partial=request.method == 'PATCH'
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AuthViewSet(viewsets.GenericViewSet):
    """
    ViewSet для аутентификации.

    Доступные методы:
    - register: Регистрация нового пользователя
    - login_email: Вход по email + пароль
    - login_phone: Вход по телефону + OTP
    - send_otp: Отправка OTP кода
    - logout: Выход (инвалидация токена)
    - refresh: Обновление токена
    """

    @action(detail=False, methods=['post'])
    def register(self, request):
        """
        Регистрация нового пользователя.

        Пример запроса:
        {
            "email": "user@example.com",
            "phone_number": "+79991234567",
            "password": "SecurePass123!",
            "first_name": "Иван",
            "last_name": "Иванов"
        }
        """
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            tokens = AuthService.generate_tokens(user)
            return Response({
                'tokens': tokens,
                'user': serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def login_email(self, request):
        """
        Вход по email и паролю.

        Пример запроса:
        {
            "email": "user@example.com",
            "password": "SecurePass123!"
        }
        """
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response(
                {'error': 'Укажите email и пароль'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = AuthService.login_by_email(email, password)
        if not user:
            return Response(
                {'error': 'Неверный email или пароль'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        tokens = AuthService.generate_tokens(user)
        return Response({
            'tokens': tokens,
            'user': UserSerializer(user).data
        })

    @action(detail=False, methods=['post'])
    def login_phone(self, request):
        """
        Вход по телефону с OTP кодом.

        Пример запроса:
        {
            "phone": "+79991234567",
            "otp": "123456"
        }
        """
        phone = request.data.get('phone')
        otp = request.data.get('otp')

        if not phone or not otp:
            return Response(
                {'error': 'Укажите телефон и код подтверждения'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = AuthService.login_by_phone(phone, otp)
        if not user:
            return Response(
                {'error': 'Неверный код подтверждения'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        tokens = AuthService.generate_tokens(user)
        return Response({
            'tokens': tokens,
            'user': UserSerializer(user).data
        })

    @action(detail=False, methods=['post'])
    def send_otp(self, request):
        """
        Отправка OTP кода на телефон или email.

        Пример запроса:
        {
            "phone": "+79991234567"
        }
        или
        {
            "email": "user@example.com"
        }
        """
        phone = request.data.get('phone')
        email = request.data.get('email')

        if not phone and not email:
            return Response(
                {'error': 'Укажите телефон или email'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if phone:
            otp = AuthService.generate_otp(phone)
            AuthService.send_otp_phone(phone, otp)
            return Response({
                'message': 'Код подтверждения отправлен на телефон',
                'phone': phone
            })

        if email:
            otp = AuthService.generate_otp(email)
            AuthService.send_otp_email(email, otp)
            return Response({
                'message': 'Код подтверждения отправлен на email',
                'email': email
            })

    @action(detail=False, methods=['post'])
    def logout(self, request):
        """
        Выход из системы (клиент должен удалить токен).

        Пример запроса:
        {
            "refresh": "refresh_token_here"
        }
        """
        # Здесь можно добавить логику черного списка токенов
        # В базовой реализации клиент просто удаляет токен на своей стороне
        return Response({
            'message': 'Выход выполнен успешно'
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def refresh(self, request):
        """
        Обновление access токена.

        Пример запроса:
        {
            "refresh": "refresh_token_here"
        }
        """
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response(
                {'error': 'Укажите refresh токен'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Здесь логика обновления токена
        # В базовой реализации можно использовать библиотеку djangorestframework-simplejwt
        return Response(
            {'error': 'Функция обновления токена требует настройки JWT'},
            status=status.HTTP_501_NOT_IMPLEMENTED
        )