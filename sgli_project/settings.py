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

SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost').split(',')

INSTALLED_APPS = [
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
    'core.apps.CoreConfig',
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
        'DIRS': [BASE_DIR / 'templates', BASE_DIR / 'core',
    'django_q',  'templates'],
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

if IS_PRODUCTION:
    # Configuração de LOGGING para Produção (Railway)
    # Redireciona tudo para o console (stdout), que o Railway captura.
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
                'level': 'INFO',  # Pode ser WARNING ou ERROR em produção
            },
        },
        'root': {
            'handlers': ['console'],
            'level': 'INFO',
        },
    }
else:
    # Configuração de LOGGING para Desenvolvimento (Local)
    # Aqui você pode manter o log em arquivo e no console.
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
                'level': 'DEBUG',
            },
            'file': {
                'class': 'logging.handlers.RotatingFileHandler', # Use RotatingFileHandler para segurança
                # Use BASE_DIR para o caminho, garantindo que 'logs' seja criado
                'filename': BASE_DIR / 'logs/sgli.log', 
                'formatter': 'verbose',
                'level': 'INFO',
                'maxBytes': 1024 * 1024 * 5,  # 5 MB
                'backupCount': 5,
            },
        },
        'root': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
    }

#LOGGING = {
#    'version': 1,
#    'disable_existing_loggers': False,
#    'formatters': {
#        'verbose': {
#            'format': '{levelname} {asctime} {module} {message}',
#            'style': '{',
#        },
#    },
#    'handlers': {
#        'file': {
#            'level': 'INFO',
#            'class': 'logging.FileHandler',
#            'filename': BASE_DIR / 'logs' / 'sgli.log',
#            'formatter': 'verbose',
#        },
#        'console': {
#            'level': 'DEBUG',
#            'class': 'logging.StreamHandler',
#            'formatter': 'verbose',
#        },
#    },
#    'root': {
#        'handlers': ['console', 'file'],
#        'level': 'INFO',
#    },
#}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'KEY_PREFIX': 'sgli',
    }
}


# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'

# Garantir que existe um lugar para arquivos estáticos

# WhiteNoise configuration
if IS_PRODUCTION:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'
    
    # WhiteNoise middleware (já deve estar, mas garantir)
    if 'whitenoise.middleware.WhiteNoiseMiddleware' not in MIDDLEWARE:
        # Adicionar após SecurityMiddleware
        middleware_list = list(MIDDLEWARE)
        security_index = middleware_list.index('django.middleware.security.SecurityMiddleware')
        middleware_list.insert(security_index + 1, 'whitenoise.middleware.WhiteNoiseMiddleware')
        MIDDLEWARE = middleware_list

# ════════════════════════════════════════════
# STATIC FILES - CONFIGURAÇÃO LIMPA
# ════════════════════════════════════════════
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Se estiver em produção, usar WhiteNoise
if IS_PRODUCTION:
    # WhiteNoise
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'
    
    # Garantir que WhiteNoise está no middleware
    if 'whitenoise.middleware.WhiteNoiseMiddleware' not in MIDDLEWARE:
        MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')


# ════════════════════════════════════════════
# CSRF TRUSTED ORIGINS - CORREÇÃO COMPLETA
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
