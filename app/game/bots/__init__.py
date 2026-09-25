"""In-game bots: what runs on a game host when a person shares a round with them.

``nav``      the walkable graph of a map, flow fields and budgeted A*
``brain``    one bot's decisions, movement, aim and chatter
``runner``   the per-instance loop, level of detail, waking and sleeping

Bots only ever exist on a host in an instance a real player is in.  An
instance that only has bots in it is put to sleep and handed back to the web
server's director, which keeps it going in closed form until somebody joins
it again.
"""
