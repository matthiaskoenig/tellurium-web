# Deployment of django app on Apache
https://www.sitepoint.com/deploying-a-django-app-with-mod_wsgi-on-ubuntu-14-04/
https://www.stavros.io/posts/how-deploy-django-docker/

```
sudo apt-get install apache2
sudo apt-get install libapache2-mod-wsgi
```

Change the owner of the apache subfolder:
```
sudo chown www-data:www-data apache/
```
