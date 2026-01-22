web: bash -c "python manage.py migrate && python manage.py collectstatic --noinput && gunicorn ft_fashion_backend.wsgi --bind 0.0.0.0:$PORT"
