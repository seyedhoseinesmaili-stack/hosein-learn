#!/usr/bin/env bash
set -e

python manage.py migrate --noinput
exec gunicorn learn.wsgi:application --timeout "${GUNICORN_TIMEOUT:-600}"
