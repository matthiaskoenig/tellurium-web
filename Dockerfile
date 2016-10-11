# docker build -t matthiaskoenig/teweb . && docker run -it -p 8000:8000 matthiaskoenig/teweb
# http://localhost:8000
FROM python:2.7
MAINTAINER Matthias Koenig <konigmatt@googlemail.com>

WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install -r requirements.txt
COPY . .

EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]