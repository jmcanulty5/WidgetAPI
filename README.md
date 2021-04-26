# Widgets API

This is a CRUD REST API using Python for a single resource type. It is built using the flask Framework and is backed by a sqlite3 db.

The single resource type supported is "widget".

Currently, it only supports json representations of widgets.

A widget resource has the following properties:
  * Name (utf8 string, limited to 64 chars)
  * Number of parts (integer)
  * Created date (date, automatically set)
  * Updated date (date, automatically set)
  * potentially more proprties can optionally be defined, and they're structure is unspecified

## Src Control Repo

xxxxxxxxx

## Primary Shell Commands For Project Developers

to create your isolated env:
> python -m venv env

to enter your env:
> . env/bin/activate

to get the development dependencies via pip and requirements.txt (run this only while in your isolated env):
> pip install -r requirements.txt

to run the unit tests:
> PYTHONPATH=. python -m unittest tests/*

to run the linting:
> flake8

to run bandit static security scans:
> bandit -r . -x /env
\*remove "-x /env" if you wish to scan every included lib as well, although be mindful that this will scan many files and some of them will be dev dependencies only, so some false positive risks may occur.

to run the flask development server:
> export FLASK_APP=flaskapp
> export FLASK_ENV=development # run this if you want dev features (hot reloading and flask debugger)
> export CONNECT_STR=local.db # this app depends on sqlite. you must set this.
> python -m flask run

After starting the server, load up the postman collection in the project root into postman. From here, you'll be able to see sample requests and play around with the endpoints of this api.

to leave your env (run this when done working on this project for the day):
> deactivate
