"""
URL configuration for homeharmony project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),  # используем свою функцию
    path('kitchen/', include('kitchen.urls', namespace='kitchen')),
    # path('cleaning/', include('cleaning.urls', namespace='cleaning')),
    # path('budget/', include('budget.urls', namespace='budget')),
    # path('repair/', include('repair.urls', namespace='repair')),
    # path('health/', include('health.urls', namespace='health')),
    # path('seasonal/', include('seasonal.urls', namespace='seasonal')),
    # path('community/', include('community.urls', namespace='community')),
    # path('knowledge/', include('knowledge.urls', namespace='knowledge')),

    # Статические страницы (пока заглушки)
    path('about/', TemplateView.as_view(template_name='about.html'), name='about'),
    path('contacts/', TemplateView.as_view(template_name='contacts.html'), name='contacts'),
    path('faq/', TemplateView.as_view(template_name='faq.html'), name='faq'),
]