web: gunicorn sgli_project.wsgi --log-file -
worker: python manage.py qcluster
release: python manage.py migrate --noinput && python manage.py collectstatic --noinput
