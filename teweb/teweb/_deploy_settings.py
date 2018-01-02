"""
Django settings for tellurium_webapp deployment
"""
DEBUG = True
SECRET_KEY = 'oizoizasdfhjoizhebraskdfijzalasdkf698hljk23'
INTERNAL_IPS = ['141.20.66.64']
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '141.20.66.64']


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'teweb',
        'USER': 'testuser',
        'HOST': 'localhost',
        'PASSWORD': 'Xac53abc7X',
        'PORT': 5432,
    }
}
