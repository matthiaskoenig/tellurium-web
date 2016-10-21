"""
Celery example

run the server via:
celery -A tasks worker --loglevel=info


To call our task you can use the delay() method.
This is a handy shortcut to the apply_async() method which gives greater control of the task execution (see Calling Tasks)

Calling a task returns an AsyncResult instance,
which can be used to check the state of the task,
wait for the task to finish or get its return value
(or if the task failed, the exception and traceback).

"""


from celery import Celery

# selecting the message broker
# for RabbitMQ you can use amqp://localhost
# or for Redis you can use redis://localhost.
#
# app = Celery('tasks', broker='amqp://guest@localhost')

# Or if you want to use Redis as the result backend, but still use RabbitMQ as the message broker (a popular combination):
app = Celery('tasks', backend='redis://localhost', broker='amqp://guest@localhost')

@app.task
def add(x, y):
    return x + y
