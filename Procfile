web: python manage.py migrate --noinput && python manage.py recalcular_valor_pago && python manage.py diagnostico_dashboard && python manage.py collectstatic --noinput && gunicorn sgli_project.wsgi:application --log-file - --timeout 120 --bind 0.0.0.0:$PORT
worker: python manage.py qcluster
