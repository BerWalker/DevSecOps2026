#!/bin/sh
set -e

exec gunicorn -b "0.0.0.0:${EMAIL_SERVICE_PORT:-5010}" -w 2 services.email.app:app
