web: python manage.py migrate --noinput && python manage.py collectstatic --noinput && gunicorn sgli_system.wsgi:application --log-file - --timeout 120 --bind 0.0.0.0:$PORT
worker: python manage.py qcluster
