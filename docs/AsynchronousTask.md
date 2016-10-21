### Asynchronous task queue


Required to run the tellurium integrations in a process outside of the request.

The absolute simplest way to do this (on a Unix-like operating system, at least) is to fork():

if os.fork() == 0:
    do_long_thing()
    sys.exit(0)
… continue with request …

This has some downsides, though (ex, if the server crashes, the “long thing” will be lost)… Which is where, ex, Celery can come in handy. It will keep track of the jobs that need to be done, the results of jobs (success/failure/whatever) and make it easy to run the jobs on other machines.

Using Celery with a Redis backend (see Kombu's Redis transport) is very simple, so I would recommend looking there first.


Celery is a powerful, production-ready asynchronous job queue, which allows 
you to run time-consuming Python functions in the background. A Celery powered 
application can respond to user requests quickly, while long-running tasks 
are passed onto the queue.
 
http://michal.karzynski.pl/blog/2014/05/18/setting-up-an-asynchronous-task-queue-for-django-using-celery-redis/

## Celery
Celery is a task queue with batteries included.
Celery uses “brokers” to pass messages between a Django Project and the Celery workers.

http://docs.celeryproject.org/en/latest/getting-started/first-steps-with-celery.html#first-steps
http://docs.celeryproject.org/en/latest/django/first-steps-with-django.html

```
pip install celery
```

# RabbitMQ - Message broker

# Redis - Key:value store
Redis, developed in 2009, is a flexible, open-source, key value data store. 
Following in the footsteps of other NoSQL databases, such as Cassandra, CouchDB, and MongoDB, 
Redis allows the user to store vast amounts of data without the limits of a relational database. 
Additionally, it has also been compared to memcache and can be used, 
with its basic elements as a cache with persistence.


Message broker
* RabbitMQ
```
sudo apt-get install rabbitmq-server
```
* Redis

* Database