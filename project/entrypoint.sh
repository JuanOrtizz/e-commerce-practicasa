#!/bin/sh
set -e

python manage.py collectstatic --noinput
python manage.py migrate

if [ "$CREATE_SUPERUSER" = "true" ]; then
    python manage.py shell < project/create_superuser.py
fi

exec "$@"
