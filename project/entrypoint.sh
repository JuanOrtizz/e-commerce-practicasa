#!/bin/sh
set -e

python manage.py collectstatic --noinput

if [ -n "$DATABASE_URL_DIRECT" ]; then
    DATABASE_URL="$DATABASE_URL_DIRECT" python manage.py migrate --noinput
else
    python manage.py migrate --noinput
fi

if [ "$CREATE_SUPERUSER" = "true" ]; then
    python manage.py shell < project/create_superuser.py
fi

exec "$@"
