from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # Основные разделы
    path('', include('pages.urls')),
    path('cooking/', include('kitchen.urls')),  # Кулинария (существующий)
    # path('cleaning/', include('cleaning.urls')),
    # path('budget/', include('budget.urls')),
    # path('repair/', include('repair.urls')),
    # path('health/', include('health.urls')),
    # path('seasonal/', include('seasonal.urls')),
    # path('community/', include('community.urls')),
    # path('knowledge/', include('knowledge.urls')),
    # path('accounts/', include('accounts.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)