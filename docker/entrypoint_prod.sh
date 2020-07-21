#!/bin/bash

/app/docker/wait_for.sh ce_db:5432 -t 2 -- echo "Database (ce_db) is up!"
/app/docker/wait_for.sh ce_mongo:27017 -t 2 -- echo "Database (ce_mongo) is up!"

python /app/manage.py migrate
python /app/manage.py loaddata initial_groups.json
/usr/local/bin/gunicorn collection_editor.wsgi -b 0.0.0.0:8000
