### gunicorn
To test if gunicorn can serve the WSGI application use
```
(tellurium-web) cd teweb
(tellurium-web) gunicorn --bind 0.0.0.0:8000 teweb.wsgi:application
```
This will not serve the static files but check if the WSGI django works with gunicorn,
which is close to the actual deployment setup.

Gunicorn can be installed via
```
sudo apt-get install gunicorn
```
