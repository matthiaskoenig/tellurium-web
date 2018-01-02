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
from .models import Job
from .tasks import sec3

from django.http import HttpResponse
from channels.handler import AsgiHandler
from channels import Group
from channels.sessions import channel_session
from urllib.parse import parse_qs
log = logging.getLogger(__name__)

from channels.sessions import channel_session
from channels.auth import channel_session_user, channel_session_user_from_http
from channels.security.websockets import allowed_hosts_only


@allowed_hosts_only
@channel_session_user_from_http
def ws_connect(message):
    """ Connection to websocket. """

    # Accept connection
    message.reply_channel.send({
        "text": json.dumps({
            "accept": True,
            "action": "reply_channel",
            "reply_channel": message.reply_channel.name,
        })
    })


@channel_session
def ws_connect(message):
    message.reply_channel.send({
        "text": json.dumps({
            "accept": True,
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


@channel_session_user
def ws_disconnect(message):
    pass
    # Group("chat-%s" % message.user.username[0]).discard(message.reply_channel)


def http_consumer(message):
    """ Example http consumer.

    :param message:
    :return:
    """
    # Make standard HTTP response - access ASGI path attribute directly
    response = HttpResponse("Hello world! You asked for %s" % message.content['path'])
    # Encode that response into message format (ASGI)
    for chunk in AsgiHandler.encode_response(response):
        message.reply_channel.send(chunk)




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
