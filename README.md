#tellurium-web

## Technology overview

docker 
* development & deployment in container

python web framework & python backend code
* Django
* [Flask](http://flask.pocoo.org/)
* Pyramid
https://www.airpair.com/python/posts/django-flask-pyramid

database backend
* simple file database (existing combine archives)

python plot framework (interactive)
* plotly (https://plot.ly/python/)
* https://plot.ly/python/line-charts/

javascript frontend
* navigation


Django includes an ORM out of the box, while Pyramid and Flask leave 
it to the developer to choose how (or if) they want their data stored. 
The most popular ORM for non-Django web applications is SQLAlchemy by 
far, but there are plenty of other options from DynamoDB and MongoDB 
to simple local persistence like LevelDB or plain SQLite. Pyramid is 
designed to use any persistence layer, even yet-to-be-invented ones.

