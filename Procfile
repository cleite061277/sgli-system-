# Removido o 'release:'
# O 'web' executa a migração antes de subir o Gunicorn.
web: python manage.py migrate --noinput && gunicorn sgli_project.wsgi:application --bind 0.0.0.0:8080 --log-file - --timeout 120

worker: python manage.py qcluster
