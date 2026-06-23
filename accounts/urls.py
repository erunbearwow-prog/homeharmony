# accounts/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserViewSet,
    FamilyGroupViewSet,
    FamilyMembershipViewSet,
    UserProfileViewSet,
    AuthViewSet,
    login_page, profile_page, favorites_page, tasks_page, register_page, logout_view,
)

app_name = 'accounts'

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'family-groups', FamilyGroupViewSet, basename='family-group')
router.register(r'family-memberships', FamilyMembershipViewSet, basename='family-membership')
router.register(r'profiles', UserProfileViewSet, basename='profile')
router.register(r'auth', AuthViewSet, basename='auth')

urlpatterns = [
    path('api/', include(router.urls)),

    # HTML-страницы для пользователя
    path('profile/', profile_page, name='profile'),
    path('favorites/', favorites_page, name='favorites'),
    path('tasks/', tasks_page, name='user_tasks'),
    path('login/', login_page, name='auth-login-phone'),
    path('register/', register_page, name='auth-register'),
    path('logout/', logout_view, name='auth-logout'),
]