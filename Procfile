web: python manage.py collectstatic --noinput --clear && python manage.py migrate --noinput && gunicorn sgli_project.wsgi --log-file - --timeout 120
worker: python manage.py qcluster
