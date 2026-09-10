# HUMAN REVIEWED

from dataclasses import replace
from math import cos, sin
from pyglm import glm

from ..messages import TickMessage

class MovementUpdater:
    def __init__(self, collisions):
        self.collisions = collisions

    def update(self, game, message):
        if not isinstance(message, TickMessage): return game
        positions = game.instances.positionables
        archetyped = game.instances.archetyped
        characters = game.instances.characters
        objects = game.archetypes.objects
        map_ = game.map
        keys = game.controls.pressed_keys
        direction = (
            glm.normalize(game.camera.right().xy) * (int('d' in keys) - int('a' in keys)) + 
            glm.normalize(game.camera.forward().xy) * (int('w' in keys) - int('s' in keys))
        )
        if glm.length(direction) > 0:
            direction = glm.normalize(direction)
        tries_running = 'shift' in keys or 'right shift' in keys
        before = positions['player']
        after = self.collisions.move(
            'player', before, direction * (4.0 if tries_running else 2.5) * message.seconds,
            positions, archetyped, objects, map_) # TODO: fuck this slop, this needs to be handled with regular system updates
        is_moving = glm.distance(glm.vec2(before), glm.vec2(after)) > 1e-6
        player = characters['player']
        animation = 'standing' if not is_moving else 'running' if tries_running else 'walking'
        return replace(game, 
            instances=replace(game.instances, 
                positionables={**positions, 'player': after}, 
                characters={
                    **characters, 
                    'player': replace(player,
                            facing=direction if is_moving else player.facing, 
                            animation=animation,
                            elapsed=player.elapsed if player.animation == animation else 0.0
                        )
                }
            )
        )
