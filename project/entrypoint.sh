#!/bin/sh
set -e

python manage.py collectstatic --noinput
python manage.py migrate
python manage.py shell < project/create_superuser.py

exec "$@"
