# Este comando será executado UMA VEZ após o build, garantindo
# que a rede com o PostgreSQL está pronta antes de migrar.
release: python manage.py collectstatic --noinput --clear && python manage.py migrate --noinput

# Este comando inicia o servidor web (Gunicorn), removendo a dependência de migração.
# Ele assume que a coleta estática e a migração já ocorreram no 'release'.
web: gunicorn sgli_project.wsgi:application --bind 0.0.0.0:8080 --log-file - --timeout 120

# Este comando é para o Django-Q (qcluster), que deve continuar separado.
worker: python manage.py qcluster
