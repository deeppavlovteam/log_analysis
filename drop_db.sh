#!/bin/bash
rm -r stats/migrations
. venv/bin/activate
python manage.py makemigrations stats
python manage.py migrate
python manage.py createsuperuser
