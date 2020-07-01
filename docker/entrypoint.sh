#!/bin/bash

/app/docker/wait_for.sh ce_db:5432 -t 2 -- echo "Database (ce_db) is up!"
/app/docker/wait_for.sh ce_mongo:27017 -t 2 -- echo "Database (ce_mongo) is up!"

cp /app/example.env /app/collection_editor/.env
cp /app/example.env /app/.env

python /app/manage.py migrate
python /app/manage.py runserver 0.0.0.0:8000
