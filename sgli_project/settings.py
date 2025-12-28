import os
from pathlib import Path
from decouple import config
import dj_database_url  # Certifique-se de que dj-database-url está instalado (pip install dj-database-url)
# --------------------------------------------------------------------------
# 🎯 CORREÇÃO DO DEPLOYMENT: DEFINIÇÃO DE IS_PRODUCTION
# --------------------------------------------------------------------------
# Definimos IS_PRODUCTION com base em uma variável de ambiente, 
# assumindo que qualquer valor diferente de 'True' para DEBUG significa PRODUÇÃO.
# (Em ambientes como Railway/Cloud, DEBUG deve ser False ou não existir)
IS_PRODUCTION = os.environ.get('DEBUG', 'False') == 'False'
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY', default='django-insecure-CHANGE-THIS-IN-PRODUCTION')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost').split(',')

INSTALLED_APPS = [
    'django_apscheduler',
    'core.apps.CoreConfig',  # ← DEVE VIR PRIMEIRO para templates customizados
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    'django_filters',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'sgli_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'sgli_project.wsgi.application'

DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL') or config('DATABASE_URL', default=None),
        conn_max_age=600
    )
}

AUTH_USER_MODEL = 'core.Usuario'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
}

LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Diretórios adicionais para collectstatic
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'
ADMIN_MEDIA_PREFIX = '/static/admin/'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

CORS_ALLOW_CREDENTIALS = True

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# -----------------------------------------------------------
# LOGGING
# -----------------------------------------------------------

    # Configuração de LOGGING para Produção (Railway)
    # Redireciona tudo para o console (stdout), que o Railway captura.
    


# ════════════════════════════════════════════
if IS_PRODUCTION:
    # Pegar domínio da variável ALLOWED_HOSTS
    allowed_hosts = config('ALLOWED_HOSTS', default='.railway.app,.up.railway.app').split(',')
    
    # Criar lista de CSRF_TRUSTED_ORIGINS com https://
    csrf_origins = []
    for host in allowed_hosts:
        host = host.strip()
        if host.startswith('.'):
            # Para wildcard domains como .railway.app
            csrf_origins.append(f'https://*{host}')
        elif host:
            # Para domínios específicos
            csrf_origins.append(f'https://{host}')
    
    # Adicionar origens manualmente também
    csrf_origins.extend([
        'https://romantic-liberation-production.up.railway.app',
        'https://*.railway.app',
        'https://*.up.railway.app',
    ])
    
    # Remover duplicatas e aplicar
    CSRF_TRUSTED_ORIGINS = list(set(csrf_origins))
    
    print(f"🔐 CSRF_TRUSTED_ORIGINS configurado: {CSRF_TRUSTED_ORIGINS}")


# ════════════════════════════════════════════
# MIDDLEWARE DE TRATAMENTO DE ERROS
# ════════════════════════════════════════════
if IS_PRODUCTION:
    MIDDLEWARE.append('core.middleware.error_handler.ProductionErrorMiddleware')

# ════════════════════════════════════════════
# LOGGING CONFIGURATION (Railway-compatible)
# ════════════════════════════════════════════
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'WARNING',  # Reduz log de SQL
            'propagate': False,
        },
    },
}


# ════════════════════════════════════════════
# DATABASE CONNECTION POOL (Railway)
# ════════════════════════════════════════════
if IS_PRODUCTION:
    DATABASES['default']['CONN_MAX_AGE'] = 600  # 10 minutos
    DATABASES['default']['OPTIONS'] = {
        'connect_timeout': 10,
        'options': '-c statement_timeout=30000',  # 30 segundos
    }
    # Prevenir erro de cursor
    DATABASES['default']['DISABLE_SERVER_SIDE_CURSORS'] = True


# ════════════════════════════════════════════
# LOGIN PERSONALIZADO
# ════════════════════════════════════════════
LOGIN_URL = '/admin/login/'
LOGIN_REDIRECT_URL = '/admin/'
LOGOUT_REDIRECT_URL = '/admin/login/'

# Fallback para SQLite em desenvolvimento (se DATABASE_URL não existir)
import os
_DATABASE_URL = os.environ.get('DATABASE_URL')

if not _DATABASE_URL:
    import warnings
    warnings.warn("DATABASE_URL não encontrada. Usando SQLite como fallback.")
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


# ════════════════════════════════════════════
# EMAIL CONFIGURATION
# ════════════════════════════════════════════
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='HABITAT PRO <noreply@habitatpro.com>')


# ════════════════════════════════════════════
# CELERY CONFIGURATION
# ════════════════════════════════════════════
CELERY_BROKER_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'America/Sao_Paulo'
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutos

# URL do site (ajuste em produção)
SITE_URL = config('SITE_URL', default='http://localhost:8000')

# ════════════════════════════════════════════════════════════
# SendGrid Email via AnyMail API
# ════════════════════════════════════════════════════════════

if 'anymail' not in INSTALLED_APPS:
    INSTALLED_APPS += ['anymail']

if os.environ.get('SENDGRID_API_KEY'):
    EMAIL_BACKEND = 'anymail.backends.sendgrid.EmailBackend'
    ANYMAIL = {
        'SENDGRID_API_KEY': os.environ.get('SENDGRID_API_KEY'),
    }

# ================================================================
# APSCHEDULER - NOTIFICAÇÕES AUTOMÁTICAS
# ================================================================
APSCHEDULER_DATETIME_FORMAT = "N j, Y, f:s a"
APSCHEDULER_RUN_NOW_TIMEOUT = 25

# ==========================================
# CONFIGURAÇÃO DE MEDIA FILES
# ==========================================

import os

# Detectar ambiente
IS_RAILWAY = os.environ.get('RAILWAY_ENVIRONMENT') is not None

if IS_RAILWAY:
    # PRODUÇÃO (Railway): Usar volume persistente
    MEDIA_ROOT = '/data/media'
    MEDIA_URL = '/media/'
    
    # Criar diretórios se não existirem
    import pathlib
    pathlib.Path(MEDIA_ROOT).mkdir(parents=True, exist_ok=True)
    pathlib.Path(os.path.join(MEDIA_ROOT, 'templates_contratos')).mkdir(parents=True, exist_ok=True)
    pathlib.Path(os.path.join(MEDIA_ROOT, 'contratos_gerados')).mkdir(parents=True, exist_ok=True)
else:
    # DESENVOLVIMENTO (Local): Usar pasta local
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
    MEDIA_URL = '/media/'

# Configurar uploads
FILE_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB


# ════════════════════════════════════════════════════════════════
# CONFIGURAÇÕES DE ALERTAS E VENCIMENTOS - DEV_21
# ════════════════════════════════════════════════════════════════

# Prazo padrão para alertas de vencimento de contratos (em dias)
PRAZO_ALERTA_VENCIMENTO_DIAS = 90

# Níveis de alerta baseados no tempo restante (OPÇÃO B - cores proporcionais)
ALERTA_CRITICO_DIAS = 60   # Vermelho: < 60 dias
ALERTA_MEDIO_DIAS = 90      # Amarelo: 60-90 dias
# Verde: > 90 dias
