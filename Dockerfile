##############################################################################
# Dockerfile
##############################################################################
# Dockerfile for running the webapp in a container.
# The container can be build and run via:
#
#       docker build -t matthiaskoenig/teweb . && docker run -it -p 8000:8000 matthiaskoenig/teweb
#
##############################################################################
FROM python:latest
MAINTAINER Matthias Koenig <konigmatt@googlemail.com>

WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install -r requirements.txt
COPY . .

# Install latest tellurium
# WORKDIR $HOME
# RUN git clone https://github.com/sys-bio/tellurium
# WORKDIR $HOME/tellurium
# RUN git checkout mkoenig
# RUN python setup.py install

RUN pip install git+https://github.com/sys-bio/tellurium.git@mkoenig

# Run tests
WORKDIR /usr/src/app/teweb
RUN python manage.py test

EXPOSE 8000
WORKDIR /usr/src/app/teweb
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]