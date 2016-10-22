#!/usr/bin/env bash

# delete old database files & uploads

# clean setup
#   python manage.py makemigrations
#   python manage.py migrate
#   python manage.py createsuperuser

# clean everything

echo "* Flush database *"
cd ../teweb
python manage.py flush --noinput

echo "* Remove upload files *"
rm archives/upload/*

echo "* Upload archives *"
cd ../scripts
python db_setup.py

