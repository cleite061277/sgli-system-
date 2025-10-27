release: python manage.py migrate --noinput && python manage.py collectstatic --noinput --clear && python create_superuser.py
web: gunicorn sgli_project.wsgi --log-file - --timeout 120
worker: python manage.py qcluster
