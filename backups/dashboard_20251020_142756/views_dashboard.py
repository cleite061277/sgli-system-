"""
Django views for SGLI dashboard.
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.urls import reverse_lazy

class DashboardHomeView(LoginRequiredMixin, TemplateView):
    """Main dashboard view."""
    template_name = 'dashboard/home.html'
    login_url = reverse_lazy('admin:login')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Dashboard'
        return context

class DashboardFinanceiroView(LoginRequiredMixin, TemplateView):
    """Financial dashboard view."""
    template_name = 'dashboard/financeiro.html'
    login_url = reverse_lazy('admin:login')

class DashboardImoveisView(LoginRequiredMixin, TemplateView):
    """Properties dashboard view."""
    template_name = 'dashboard/imoveis.html'
    login_url = reverse_lazy('admin:login')

class DashboardRelatoriosView(LoginRequiredMixin, TemplateView):
    """Reports dashboard view."""
    template_name = 'dashboard/relatorios.html'
    login_url = reverse_lazy('admin:login')

