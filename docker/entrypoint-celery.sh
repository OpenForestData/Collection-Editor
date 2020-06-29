#!/bin/bash

/app/docker/wait_for.sh harvester_db:5432 -t 15 -- echo "Database (harvester_db) is up!"
/app/docker/wait_for.sh harvester_mongo:27017 -t 15 -- echo "Database (harvester_mongo) is up!"
/app/docker/wait_for.sh harvester_redis:6379 -t 15 -- echo "Redis (harvester_redis) is up!"

cp /app/example.env /app/harvester/.env
cp /app/example.env /app/.env

cd /app/
celery flower -A harvester worker -l=INFO --address=0.0.0.0