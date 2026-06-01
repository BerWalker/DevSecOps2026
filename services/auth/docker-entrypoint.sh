#!/bin/sh
set -e

flask db upgrade

exec gunicorn -b "0.0.0.0:${AUTH_SERVICE_PORT:-5001}" -w 2 services.auth.app:app
