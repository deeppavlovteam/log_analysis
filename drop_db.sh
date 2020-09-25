#!/bin/bash
rm db.sqlite3 stats/migrations/*.py
. venv/bin/activate
python manage.py makemigrations stats
python manage.py migrate
python manage.py createsuperuser
python manage.py shell
