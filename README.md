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

## Changelog
*v0.1* [?]
- initial release

## Technology
In the following section an overview over the used and planned technology is 
given.
### Docker 
* development & deployment in container
* reproducible environments for testing

### Web framework 
* django
* python web framework & python backend code



### Datastorage layer
sqlite & postgresql
* database backend
* simple file database (sqlite)
* switch to postgres when necessary

### Interactive plots
python plot framework (interactive)
* [plotly](https://plot.ly/python/) with examples https://plot.ly/python/line-charts/
* [bokeh] http://bokeh.pydata.org/en/latest/docs/gallery/legend.html
* [plotly.js] https://github.com/plotly/plotly.js

# Installation
```
mkvirtualenv tellurium-web
(tellurium-web) pip install -r requirements.txt
```

In addition tellurium must be installed in the environment.
