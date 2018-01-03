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

from django.shortcuts import get_object_or_404

from .models import Job, Archive
from .tasks import execute_omex
from urllib.parse import parse_qs
from celery.result import AsyncResult

from django.http import HttpResponse

from channels import Channel, Group
from channels.handler import AsgiHandler
from channels.sessions import channel_session
from channels.auth import channel_session_user, channel_session_user_from_http
from channels.security.websockets import allowed_hosts_only

log = logging.getLogger(__name__)


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

        if data['action'] == "run_archive":
            run_archive(data, reply_channel)



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


def run_archive(data, reply_channel):
    log.debug("job Name=%s", data['archive_id'])

    create_task = False

    # get archive
    archive_id = data['archive_id']
    archive = get_object_or_404(Archive, pk=archive_id)

    if archive.task_id:
        result = AsyncResult(archive.task_id)
        # Create new task and run again.
        if result.status in ["FAILURE", "SUCCESS"]:
            create_task = True

    else:
        # no execution yet
        create_task = True

    if create_task:
        # task will send message when finished
        result = execute_omex.delay(archive_id=archive_id, reply_channel=reply_channel)
        archive.task_id = result.task_id
        archive.save()

    # Tell client task has been started
    Channel(reply_channel).send({
        "text": json.dumps({
            "task_id": archive.task_id,
            "task_status": result.status,
            "archive_id": archive_id,
        })
    })
