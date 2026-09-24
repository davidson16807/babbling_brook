# HUMAN VETTED

from dataclasses import replace
from pyglm import glm

class MovementUpdater:
    def __init__(self, collisions, directional_keys):
        self.collisions = collisions
        self.directional_keys = directional_keys

    def update(self, game, seconds):
        placements = game.instances.placements
        characters = game.instances.characters
        objects = game.archetypes.objects
        map_ = game.map
        keys = game.controls.pressed_keys
        axes = self.directional_keys.update(keys)
        direction = (
            glm.normalize(game.camera.right().xy) * axes.x +
            glm.normalize(game.camera.forward().xy) * axes.y
        )
        if glm.length(direction) > 0:
            direction = glm.normalize(direction)
        tries_running = 'shift' in keys or 'right shift' in keys
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
