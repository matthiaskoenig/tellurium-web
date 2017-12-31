"""
Django channels.

In our ws_connect function, we will simply echo back to the client
what their reply channel address is. The reply channel is the unique address
that gets assigned to every browser client that connects to our
websockets server. This value which can be retrieved from
message.reply_channel.name can be saved or passed on to a different
function such as a Celery task so that they can also send a message back.
"""

import json
import logging
from channels import Channel
from channels.sessions import channel_session
from .models import Job
from .tasks import sec3

from channels.handler import AsgiHandler

log = logging.getLogger(__name__)

def http_consumer(message):
    # Make standard HTTP response - access ASGI path attribute directly
    response = HttpResponse("Hello world! You asked for %s" % message.content['path'])
    # Encode that response into message format (ASGI)
    for chunk in AsgiHandler.encode_response(response):
        message.reply_channel.send(chunk)

def my_consumer(message):
    """ Example function to consume a channel.
    For every message on the channel, Django will call the consumer function with
    a message object (message objects have a “content” attribute which is
    always a dict of data, and a “channel” attribute which is the channel
    it came from, as well as some others).

    :param message:
    :return:
    """

    pass


@channel_session
def ws_connect(message):
    message.reply_channel.send({
        "text": json.dumps({
            "action": "reply_channel",
            "reply_channel": message.reply_channel.name,
        })
    })


@channel_session
def ws_receive(message):
    try:
        data = json.loads(message['text'])
    except ValueError:
        log.debug("ws message isn't json text=%s", message['text'])
        return

    if data:
        reply_channel = message.reply_channel.name

        if data['action'] == "start_sec3":
            start_sec3(data, reply_channel)


def start_sec3(data, reply_channel):
    log.debug("job Name=%s", data['job_name'])
    # Save model to our database
    job = Job(
        name=data['job_name'],
        status="started",
    )
    job.save()

    # Start long running task here (using Celery)
    sec3_task = sec3.delay(job.id, reply_channel)

    # Store the celery task id into the database if we wanted to
    # do things like cancel the task in the future
    job.celery_id = sec3_task.id
    job.save()

    # Tell client task has been started
    Channel(reply_channel).send({
        "text": json.dumps({
            "action": "started",
            "job_id": job.id,
            "job_name": job.name,
            "job_status": job.status,
        })
    })