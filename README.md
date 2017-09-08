<h1><img title="tellurium logo" src="./teweb/combine/static/combine/images/logos/te-web.png" height="40" />&nbsp;&nbsp;Tellurium Web Tools</h1>

[![Build Status](https://travis-ci.org/matthiaskoenig/tellurium-web.svg?branch=develop)](https://travis-ci.org/matthiaskoenig/tellurium-web)
[![License (LGPL version 3)](https://img.shields.io/badge/license-LGPLv3.0-blue.svg?style=flat-square)](http://opensource.org/licenses/LGPL-3.0)
[![Coverage Status](https://coveralls.io/repos/github/matthiaskoenig/tellurium-web/badge.svg?branch=master)](https://coveralls.io/github/matthiaskoenig/tellurium-web?branch=master)

Online tools for running [CombineArchives](http://co.mbine.org/documents/archive) (*.omex) with [tellurium](http://tellurium.analogmachine.org/).   
Model descriptions in 
[SBML](http://sbml.org) and simulation descriptions in [SED-ML](http://sed-ml.org) are supported.



<img title="Screenshot Tellurium Web Tools" src="./docs/images/screenshot-0.1.png" width="600" />

Screenshot of the CombineArchive upload and list of Archives. 
Among others the [Combine Showcase Archive](https://github.com/SemsProject/CombineArchiveShowCase) is included.

## License
* Source Code: [LGPLv3](http://opensource.org/licenses/LGPL-3.0)
* Documentation: [CC BY-SA 4.0](http://creativecommons.org/licenses/by-sa/4.0/)

## Installation
`tellurium-web` requires 
- `python 3.5` or `python 3.6`.
- `redis` installation as message broker (for installation script see `linux-setup`) or `rabbitmq-server`
- `postgres`


### Setup
```
mkvirtualenv tellurium-web
(tellurium-web) pip install -r requirements.txt
```

The test server can be run via
```
(tellurium-web) cd teweb
(tellurium-web) python manage.py makemigrations
(tellurium-web) python manage.py makemigrations combine

(tellurium-web) python manage.py migrate
(tellurium-web) python manage.py runserver
(tellurium-web) python manage.py createsuperuser
```
Database can be filled via
```
(tellurium-web) ./scripts/fill_db.sh
```

# Celery
Start a test worker 
```
(tellurium-web) celery -A teweb worker -l info
```


## Changelog
*v0.1* [?]
- initial release


# Technology
This section gives an overview over the employed technology in `tellurium-web`

### Web framework 
* [django](https://www.djangoproject.com/)

### Database layer
* [sqlite](https://www.sqlite.org/) (develop) & [postgres](https://www.postgresql.org/) (deploy)

### Task queue
The execution of the CombineArchives and the simulations are performed
in a task queue. Task queues are used as a mechanism to distribute work across threads or machines.
* [celery](http://www.celeryproject.org/) Distributed task queue
* [redis](https://redis.io/) Redis is an open source (BSD licensed), 
in-memory data structure store, used as a database, cache and message broker.
* [jobtastic](https://github.com/PolicyStat/jobtastic)


### Interactive plots
python plot framework (interactive)
* [plotly](https://plot.ly/python/) with examples https://plot.ly/python/line-charts/
* [bokeh](https://bokeh.pydata.org/en/latest/) 
* [plotly.js](https://github.com/plotly/plotly.js) 

### Docker 
* development & deployment in container
* reproducible environments for testing
