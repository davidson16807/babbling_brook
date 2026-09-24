# HUMAN REVIEWED

from dataclasses import replace

from ..messages import (KeyboardMessage, KeyboardAction, MouseButton, MouseMotionMessage,
    QuitMessage, WindowResizeMessage)
from ..model.component.instances import VerticalPhysics

pi = 3.14159265358979

class GameUpdater:
    def __init__(self, mouselook, keylook, interactions, actions, jump_speed=6):

        self.mouselook = mouselook
        self.keylook = keylook
        self.interactions = interactions
        self.actions = actions
        self.jump_speed = jump_speed

    def update(self, game, message):
        if isinstance(message, QuitMessage):
            return replace(game, running=False)
        if isinstance(message, WindowResizeMessage):
            return replace(game, viewport=message.size)
        if isinstance(message, MouseMotionMessage) and MouseButton.MIDDLE in message.buttons:
            return replace(game, camera=self.mouselook.update(game.camera, message))
        if isinstance(message, KeyboardMessage) and message.action == KeyboardAction.PRESS:
            if message.key == 'escape':
                return replace(game, running=False)
            if message.key == 'tab':
                return replace(game, show_inventory=not game.show_inventory)
            if message.key == 'space' and game.instances.physics['player'].is_grounded:
                physics = {**game.instances.physics, 'player': VerticalPhysics(self.jump_speed, False)}
                return replace(game, instances=replace(game.instances, physics=physics))
            if message.key == 'e':
                target = self.interactions.nearest(
                    game.instances.placements['player'].position,
                    game.instances.characters['player'].facing,
                    game.instances.placements,
                    game.archetypes.objects,
                )
                if target is None:
                    return replace(game, message="Nothing to interact with nearby.")
                entity, archetype = target
                return self.actions.apply(archetype.action, game, entity)
            else:
                game = replace(game, 
                    camera = replace(game.camera,
                        raw_azimuth = game.camera.raw_azimuth + (self.keylook.update(message.key).x * pi/2) % (2*pi),
                        elevation = max(pi/6, min(pi/3, game.camera.elevation + self.keylook.update(message.key).y * pi/6))
                    )
                )
        return game
