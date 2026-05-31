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

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    path('kitchen/', include('kitchen.urls', namespace='kitchen')),

    # Временные маршруты для других разделов
    path('cleaning/', TemplateView.as_view(template_name='coming_soon.html'), name='cleaning'),
    path('budget/', TemplateView.as_view(template_name='coming_soon.html'), name='budget'),
    path('repair/', TemplateView.as_view(template_name='coming_soon.html'), name='repair'),
    path('health/', TemplateView.as_view(template_name='coming_soon.html'), name='health'),
    path('seasonal/', TemplateView.as_view(template_name='coming_soon.html'), name='seasonal'),
    path('community/', TemplateView.as_view(template_name='coming_soon.html'), name='community'),
    path('knowledge/', TemplateView.as_view(template_name='coming_soon.html'), name='knowledge'),

    path('about/', TemplateView.as_view(template_name='about.html'), name='about'),
    path('contacts/', TemplateView.as_view(template_name='contacts.html'), name='contacts'),
    path('faq/', TemplateView.as_view(template_name='faq.html'), name='faq'),
]