web: gunicorn config.wsgi --workers 2 --timeout 120 --bind 0.0.0.0:$PORT
release: python manage.py migrate --noinput && python manage.py collectstatic --noinput