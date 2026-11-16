#!/bin/sh
# one container, two processes: the scheduler (autonomous discovery, monitoring, reviews) and the web server
python manage.py scheduler &
exec gunicorn -w 1 --threads 8 -b 0.0.0.0:${PORT:-5000} "msanii:create_app()"
