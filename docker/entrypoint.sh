#!/bin/bash

/app/docker/wait_for.sh harvester_db:5432 -t 15 -- echo "Database (harvester_db) is up!"
/app/docker/wait_for.sh harvester_mongo:27017 -t 15 -- echo "Database (harvester_mongo) is up!"

cp /app/example.env /app/harvester/.env
cp /app/example.env /app/.env

python /app/manage.py migrate
python /app/manage.py runserver 0.0.0.0:8000
