"""
URLs customizadas para Dashboard
"""
from django.urls import path
from .admin_dashboard import admin_dashboard

urlpatterns = [
    path('', admin_dashboard, name='admin_dashboard'),
]
