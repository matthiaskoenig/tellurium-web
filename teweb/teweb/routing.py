"""
Routing information for django channels.
"""

from channels import route
from .combine import consumers

channel_routing = [
    # "some-channel": "combine.consumers.my_consumer",
    route("http.request", "combine.consumers.http_consumer"),

    # Wire up websocket channels to our consumers:
    route("websocket.connect", consumers.ws_connect),
    route("websocket.receive", consumers.ws_receive),
]