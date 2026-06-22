from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from kitchen.views import get_child_categories

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('pages.urls')),           # ← ВРЕМЕННО
    path('kitchen/', include('kitchen.urls')),   # ← ОСТАВЛЯЕМ
    path('accounts/', include('accounts.urls')), # ← ВРЕМЕННО
    path('cleaning/', include('cleaning.urls')), # ← ВРЕМЕННО
    path('budget/', include('budget.urls')),     # ← ВРЕМЕННО
    path('repair/', include('repair.urls')),     # ← ВРЕМЕННО
    path('health/', include('health.urls')),     # ← ВРЕМЕННО
    path('seasonal/', include('seasonal.urls')), # ← ВРЕМЕННО
    path('community/', include('community.urls')), # ← ВРЕМЕННО
    path('knowledge/', include('knowledge.urls')), # ← ВРЕМЕННО
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)