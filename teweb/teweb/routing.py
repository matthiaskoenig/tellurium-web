"""
Routing information for django channels.
"""

from channels import route
from combine.consumers import ws_connect, ws_message, ws_disconnect

channel_routing = [
    # http requests (these are handled by normal django views)
    # route("http.request", "combine.consumers.http_consumer"),

    # wire up websocket channesl
    # route("websocket.connect", ws_connect, path=r"^/(?P<room_name>[a-zA-Z0-9_]+)/$"),
    # route("websocket.receive", ws_message, path=r"^/(?P<room_name>[a-zA-Z0-9_]+)/$"),
    # route("websocket.disconnect", ws_disconnect, path=r"^/(?P<room_name>[a-zA-Z0-9_]+)/$"),

    route("websocket.connect", ws_connect),
    route("websocket.receive", ws_message),
    route("websocket.disconnect", ws_disconnect),

    # Wire up websocket channels to our consumers:
    # route("websocket.connect", consumers.ws_connect),
    # route("websocket.receive", consumers.ws_receive),
]