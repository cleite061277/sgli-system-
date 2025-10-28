web: python manage.py migrate --noinput && python manage.py collectstatic --noinput --clear && python create_superuser.py && python populate_initial_data.py && gunicorn sgli_project.wsgi --log-file - --timeout 120 --bind 0.0.0.0:$PORT
worker: python manage.py qcluster
