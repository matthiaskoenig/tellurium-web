##############################################################################
# Dockerfile
##############################################################################
# Dockerfile for running the webapp in a container.
# The container can be build and run via:
#
#       docker build -t matthiaskoenig/teweb . && docker run -it -p 8000:8000 matthiaskoenig/teweb
#
##############################################################################
FROM python:3.5
MAINTAINER Matthias Koenig <konigmatt@googlemail.com>

WORKDIR /usr/src/app
COPY . .
RUN pip install -r requirements.txt

WORKDIR /usr/src/app/teweb
RUN python manage.py test

EXPOSE 8000
WORKDIR /usr/src/app/teweb
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

# TODO: run functionality tests