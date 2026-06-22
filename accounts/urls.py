# accounts/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserViewSet,
    FamilyGroupViewSet,
    FamilyMembershipViewSet,
    UserProfileViewSet,
    AuthViewSet,
    profile_page
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
    path('profile/', profile_page, name='profile'),
]