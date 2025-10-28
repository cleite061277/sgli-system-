web: python manage.py migrate --noinput && python manage.py collectstatic --noinput && python create_superuser.py && gunicorn sgli_project.wsgi --log-file - --timeout 120 --bind 0.0.0.0:$PORT
worker: python manage.py qcluster
