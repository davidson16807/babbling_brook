# HUMAN VETTED

from dataclasses import replace
from pyglm import glm

from ..messages import KeyboardAction, KeyboardMessage

class MovementUpdater:
    def __init__(self, collisions, vector_updater):
        self.collisions = collisions
        self.vector_updater = vector_updater

    def update(self, game, seconds, messages):
        placements = game.instances.placements
        characters = game.instances.characters
        objects = game.archetypes.objects
        map_ = game.map
        held = tuple(
            message for message in messages
            if isinstance(message, KeyboardMessage)
            and message.action == KeyboardAction.REPEAT
        )
        axes = glm.vec2(0)
        for message in held:
            axes = self.vector_updater.update(axes, message)
        direction = (
            glm.normalize(game.camera.right().xy) * axes.x +
            glm.normalize(game.camera.forward().xy) * axes.y
        )
        if glm.length(direction) > 0:
            direction = glm.normalize(direction)
        tries_running = any(message.key in ('shift', 'right shift') for message in held)
        before = placements['player'].position
        after = self.collisions.move(
            'player', before, direction * (4.0 if tries_running else 2.5) * seconds,
            placements, objects, map_)
        is_moving = glm.distance(glm.vec2(before), glm.vec2(after)) > 1e-6
        player = characters['player']
        animation = 'standing' if not is_moving else 'running' if tries_running else 'walking'
        return replace(game, 
            instances=replace(game.instances, 
                placements={
                    **placements,
                    'player': replace(placements['player'], position=after),
                },
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
