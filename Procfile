# Removido o 'release:'
# CRIAÇÃO TEMPORÁRIA DO SUPERUSUÁRIO ANTES DA MIGRAÇÃO
web: python manage.py createsuperuser --noinput --username $DJANGO_SUPERUSER_USERNAME --email $DJANGO_SUPERUSER_EMAIL || true && \
python manage.py migrate --noinput && \
gunicorn sgli_project.wsgi:application --bind 0.0.0.0:8080 --log-file - --timeout 120

worker: python manage.py qcluster
