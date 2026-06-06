#!/bin/sh
set -e

flask db upgrade

exec gunicorn -b "0.0.0.0:${CAMPAIGN_SERVICE_PORT:-5002}" -w 2 services.campaign.app:app
