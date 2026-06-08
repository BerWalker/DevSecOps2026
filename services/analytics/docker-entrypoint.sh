#!/bin/sh
set -e

flask db upgrade

exec gunicorn -b "0.0.0.0:${ANALYTICS_SERVICE_PORT:-5003}" -w 2 services.analytics.app:app
