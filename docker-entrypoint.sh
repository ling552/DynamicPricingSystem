#!/bin/sh
set -e

python manage.py collectstatic --noinput
python manage.py migrate --noinput

if [ "${DPS_SEED_DEMO:-}" = "1" ]; then
  python manage.py seed_demo
fi

exec "$@"
