"""The event worlds' maps: one package per world, one module per area.

Every package builds its areas with :mod:`.kit` -- an
:class:`~.kit.ArenaArea` is a Last Light area (app/game/maps/lastlight/kit.py)
with team spawns, spectator cameras, switchable solids and room for whatever
else the world's rules need to know about the place -- and lays them out
with :func:`.kit.build_world`, far enough apart that no area can ever be seen
from another.
"""
