#!/usr/bin/env bash
########################################################
# Setup the database
#
# Deletes old database and recreates all data.
# TODO: same necessary for postgres
########################################################
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

# delete old database files & uploads
cd $DIR
cd ../teweb/
rm combine.sqlite3
rm -rf combine/migrations/*

# clean setup
python manage.py makemigrations
python manage.py makemigrations combine
python manage.py migrate


# clean everything
echo "* Remove upload files *"
rm media/archives/*
rm combine/migrations/*

echo "* Upload archives *"
cd $DIR
python fill_database.py

# create super user
cd ../teweb/
python manage.py createsuperuser