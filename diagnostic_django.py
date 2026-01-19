#!/usr/bin/env python
"""
HABITAT PRO - DIAGNÓSTICO DJANGO DETALHADO
Script para analisar configurações específicas do Django
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sgli_project.settings')
django.setup()

from django.conf import settings
from django.contrib import admin
from django.apps import apps

print("=" * 60)
print("🔍 HABITAT PRO - DIAGNÓSTICO DJANGO DETALHADO")
print("=" * 60)
print()

# ==========================================
# 1. CONFIGURAÇÕES DO PROJETO
# ==========================================
print("=" * 60)
print("1️⃣ CONFIGURAÇÕES DO PROJETO")
print("=" * 60)
print()

print("→ Nome do projeto:")
print(f"   {settings.SETTINGS_MODULE}")
print()

print("→ DEBUG mode:")
print(f"   {settings.DEBUG}")
print()

print("→ INSTALLED_APPS:")
for i, app in enumerate(settings.INSTALLED_APPS, 1):
    print(f"   {i:2d}. {app}")
print()

print("→ MIDDLEWARE:")
for i, mw in enumerate(settings.MIDDLEWARE, 1):
    print(f"   {i:2d}. {mw}")
print()

# ==========================================
# 2. CONFIGURAÇÕES DO ADMIN
# ==========================================
print("=" * 60)
print("2️⃣ CONFIGURAÇÕES DO ADMIN SITE")
print("=" * 60)
print()

print("→ Admin site class:")
print(f"   {admin.site.__class__.__module__}.{admin.site.__class__.__name__}")
print()

print("→ Admin site title:")
print(f"   site_title: {admin.site.site_title}")
print(f"   site_header: {admin.site.site_header}")
print(f"   index_title: {admin.site.index_title}")
print()

print("→ Templates customizados:")
if hasattr(admin.site, 'index_template') and admin.site.index_template:
    print(f"   index_template: {admin.site.index_template}")
else:
    print("   index_template: (padrão)")
    
if hasattr(admin.site, 'base_template') and admin.site.base_template:
    print(f"   base_template: {admin.site.base_template}")
else:
    print("   base_template: (padrão)")
print()

# ==========================================
# 3. MODELS REGISTRADOS
# ==========================================
print("=" * 60)
print("3️⃣ MODELS REGISTRADOS NO ADMIN")
print("=" * 60)
print()

registered_models = admin.site._registry
print(f"→ Total de models registrados: {len(registered_models)}")
print()

print("→ Lista de models:")
for i, (model, model_admin) in enumerate(sorted(registered_models.items(), key=lambda x: x[0]._meta.verbose_name_plural), 1):
    app_label = model._meta.app_label
    model_name = model._meta.model_name
    verbose_name = model._meta.verbose_name_plural
    admin_class = model_admin.__class__.__name__
    
    print(f"   {i:2d}. {app_label}.{model_name}")
    print(f"       Verbose: {verbose_name}")
    print(f"       Admin: {admin_class}")
    
    # Verificar customizações importantes
    customizations = []
    if hasattr(model_admin, 'list_display') and model_admin.list_display != ('__str__',):
        customizations.append(f"list_display ({len(model_admin.list_display)} cols)")
    if hasattr(model_admin, 'list_filter') and model_admin.list_filter:
        customizations.append(f"list_filter ({len(model_admin.list_filter)} filters)")
    if hasattr(model_admin, 'search_fields') and model_admin.search_fields:
        customizations.append(f"search_fields ({len(model_admin.search_fields)} fields)")
    if hasattr(model_admin, 'actions') and len(model_admin.actions) > 1:  # >1 porque delete é padrão
        customizations.append(f"actions ({len(model_admin.actions)-1} custom)")
    if hasattr(model_admin, 'inlines') and model_admin.inlines:
        customizations.append(f"inlines ({len(model_admin.inlines)})")
    
    if customizations:
        print(f"       Customizações: {', '.join(customizations)}")
    print()

# ==========================================
# 4. TEMPLATES
# ==========================================
print("=" * 60)
print("4️⃣ CONFIGURAÇÕES DE TEMPLATES")
print("=" * 60)
print()

print("→ Template engines:")
for i, engine in enumerate(settings.TEMPLATES, 1):
    print(f"   {i}. {engine['BACKEND']}")
    if 'DIRS' in engine and engine['DIRS']:
        print(f"      DIRS: {engine['DIRS']}")
    if 'APP_DIRS' in engine:
        print(f"      APP_DIRS: {engine['APP_DIRS']}")
print()

# Verificar se existem templates customizados do admin
import os
templates_dirs = settings.TEMPLATES[0].get('DIRS', [])
for template_dir in templates_dirs:
    admin_template_dir = os.path.join(template_dir, 'admin')
    if os.path.exists(admin_template_dir):
        print(f"→ Templates admin customizados encontrados em:")
        print(f"   {admin_template_dir}")
        
        # Listar arquivos
        for root, dirs, files in os.walk(admin_template_dir):
            for file in files:
                if file.endswith('.html'):
                    rel_path = os.path.relpath(os.path.join(root, file), template_dir)
                    print(f"   - {rel_path}")
        print()

# ==========================================
# 5. STATIC FILES
# ==========================================
print("=" * 60)
print("5️⃣ CONFIGURAÇÕES DE ARQUIVOS ESTÁTICOS")
print("=" * 60)
print()

print("→ STATIC_URL:")
print(f"   {settings.STATIC_URL}")
print()

if hasattr(settings, 'STATIC_ROOT'):
    print("→ STATIC_ROOT:")
    print(f"   {settings.STATIC_ROOT}")
    print()

if hasattr(settings, 'STATICFILES_DIRS'):
    print("→ STATICFILES_DIRS:")
    for i, static_dir in enumerate(settings.STATICFILES_DIRS, 1):
        print(f"   {i}. {static_dir}")
    print()

# ==========================================
# 6. APPS CUSTOMIZADOS
# ==========================================
print("=" * 60)
print("6️⃣ APPS CUSTOMIZADOS DO PROJETO")
print("=" * 60)
print()

project_apps = [app for app in settings.INSTALLED_APPS 
                if not app.startswith('django.') 
                and not app.startswith('rest_framework')
                and app != 'django_apscheduler']

print("→ Apps do projeto:")
for i, app in enumerate(project_apps, 1):
    try:
        app_config = apps.get_app_config(app.split('.')[-1])
        print(f"   {i}. {app}")
        print(f"      Path: {app_config.path}")
        
        # Contar models
        models = app_config.get_models()
        print(f"      Models: {len(models)}")
        
    except:
        print(f"   {i}. {app} (não carregado)")
    print()

# ==========================================
# 7. VERIFICAÇÕES DE COMPATIBILIDADE
# ==========================================
print("=" * 60)
print("7️⃣ VERIFICAÇÕES DE COMPATIBILIDADE")
print("=" * 60)
print()

print("→ Versão Django:")
print(f"   {django.get_version()}")
print()

print("→ Compatibilidade Unfold:")
django_version = tuple(map(int, django.get_version().split('.')[:2]))
if django_version >= (4, 2):
    print("   ✅ Django >= 4.2 (compatível com Unfold)")
else:
    print(f"   ⚠️ Django {django.get_version()} (Unfold requer >= 4.2)")
print()

print("→ Python version:")
print(f"   {sys.version.split()[0]}")
python_version = tuple(map(int, sys.version.split()[0].split('.')[:2]))
if python_version >= (3, 10):
    print("   ✅ Python >= 3.10 (compatível com Unfold)")
else:
    print(f"   ⚠️ Python {sys.version.split()[0]} (Unfold requer >= 3.10)")
print()

# ==========================================
# 8. RESUMO
# ==========================================
print("=" * 60)
print("📊 RESUMO DO DIAGNÓSTICO")
print("=" * 60)
print()

print("✅ Verificações concluídas:")
print(f"   • {len(settings.INSTALLED_APPS)} apps instalados")
print(f"   • {len(registered_models)} models no admin")
print(f"   • {len(project_apps)} apps customizados")
print(f"   • Django {django.get_version()}")
print(f"   • Python {sys.version.split()[0]}")
print()

# Verificar se há customizações críticas
critical_customizations = []
if hasattr(admin.site, 'index_template') and admin.site.index_template:
    critical_customizations.append("Template index customizado")
if hasattr(admin.site, 'base_template') and admin.site.base_template:
    critical_customizations.append("Template base customizado")

if critical_customizations:
    print("⚠️ Customizações críticas detectadas:")
    for custom in critical_customizations:
        print(f"   • {custom}")
    print()
    print("   → Estas customizações serão preservadas durante implementação")
    print()
else:
    print("✅ Nenhuma customização crítica detectada")
    print("   → Implementação será mais simples")
    print()

print("=" * 60)
print("✅ DIAGNÓSTICO DJANGO COMPLETO!")
print("=" * 60)
print()
print("Próximo passo: Envie esta saída junto com o diagnóstico Bash")
print()
