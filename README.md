# Tellurium Web Tools
<img title="tellurium logo" src="./teweb/combine/static/combine/images/logos/te.png" height="50" />

[![Build Status](https://travis-ci.org/matthiaskoenig/tellurium-web.svg?branch=master)](https://travis-ci.org/matthiaskoenig/tellurium-web)
[![License (LGPL version 3)](https://img.shields.io/badge/license-LGPLv3.0-blue.svg?style=flat-square)](http://opensource.org/licenses/LGPL-3.0)
[![Coverage Status](https://coveralls.io/repos/github/matthiaskoenig/tellurium-web/badge.svg?branch=master)](https://coveralls.io/github/matthiaskoenig/tellurium-web?branch=master)

Online tools for running [CombineArchives](http://co.mbine.org/documents/archive) (*.omex) with [tellurium](http://tellurium.analogmachine.org/).   
Model descriptions in 
[SBML](http://sbml.org) and simulation descriptions in [SED-ML](http://sed-ml.org) are supported.

As example archive the [Combine Showcase Archive](https://github.com/SemsProject/CombineArchiveShowCase) is provided.

<img title="Screenshot Tellurium Web Tools" src="./docs/images/screenshot.png" width="600" />

Screenshot of the CombineArchive upload and list of Archives.

## License
* Source Code: [LGPLv3](http://opensource.org/licenses/LGPL-3.0)
* Documentation: [CC BY-SA 4.0](http://creativecommons.org/licenses/by-sa/4.0/)

## Installation
```
mkvirtualenv tellurium-web
(tellurium-web) pip install -r requirements.txt
```

In addition tellurium must be installed in the environment. This can be done
by cloning the `tellurium repository` and installing the latest version via
```

```

The test server can be run via
```
cd teweb
python manage.py makemigrations
python manage.py makemigrations combine
python manage.py migrate
python manage.py runserver
```
Database can be filled via
```
./scripts/fill_db.sh
```
 

## Changelog
*v0.1* [?]
- initial release


## Technology
The following technology is used in `tellurium-web`

### Web framework 
* [django](https://www.djangoproject.com/)

### Database layer
* [sqlite](https://www.sqlite.org/) (develop) & [postgres](https://www.postgresql.org/) (deploy)

### Task queue
* celery, jobtastic
* rabbitmq

### Interactive plots
python plot framework (interactive)
* [plotly](https://plot.ly/python/) with examples https://plot.ly/python/line-charts/
* [bokeh] http://bokeh.pydata.org/en/latest/docs/gallery/legend.html
* [plotly.js] https://github.com/plotly/plotly.js

### Docker 
* development & deployment in container
* reproducible environments for testing
