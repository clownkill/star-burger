#!/bin/bash

set -e

cd /opt/star-burger

git pull

COMMIT_HASH='git rev-parse --short HEAD'

pip install -r requirements.txt

npm install --only-dev

parcel build bundles-src/index.js -d bundles --no-minify --public-url="./"

venv/bin/python manage.py collectstatic --no-input

venv/bin/python manage.py migrate --no-input

systemctl restart star-burger.service
systmectl reload nginx.service

curl -H "X-Rollbar-Access-Token: 27ba3be4f2394b6f852c76bb1fbbfcf0" -H "Content-Type: application/json" -X POST 'https://api.rollbar.com/api/1/deploy' -d '{"environment": "prod", "revision": "'$COMMIT_HASH'"}'
