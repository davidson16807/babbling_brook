# HUMAN REVIEWED

from dataclasses import replace

from ..messages import (KeyboardMessage, KeyboardAction, MouseButton, MouseMotionMessage,
    QuitMessage, WindowResizeMessage)
from ..model.components.instances import VerticalPhysics


class GameUpdater:
    def __init__(self, controls, camera, interactions, actions):

        self.controls = controls
        self.camera = camera
        self.interactions = interactions

        self.actions = actions

    def update(self, game, message):
        game = replace(game, controls=self.controls.update(game.controls, message))
        if isinstance(message, QuitMessage):
            return replace(game, running=False)
        if isinstance(message, WindowResizeMessage):
            return replace(game, viewport=message.size)
        if isinstance(message, MouseMotionMessage) and MouseButton.MIDDLE in game.controls.pressed_mouse_buttons:
            return replace(game, camera=self.camera.update(game.camera, message))
        if isinstance(message, KeyboardMessage) and message.action == KeyboardAction.PRESS:
            if message.key == 'escape':
                return replace(game, running=False)
            if message.key == 'tab':
                return replace(game, show_inventory=not game.show_inventory)
            if message.key == 'space' and game.instances.physics['player'].is_grounded:
                physics = {**game.instances.physics, 'player': VerticalPhysics(6.0, False)}
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
        return game
