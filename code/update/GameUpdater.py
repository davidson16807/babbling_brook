from dataclasses import replace
from math import ceil, isfinite

from ..messages import (KeyboardMessage, KeyboardAction, MouseButton, MouseMotionMessage,
    TickMessage, QuitMessage, WindowResizeMessage)
from ..model.components.instances import VerticalPhysics


class GameUpdater:
    def __init__(self, controls, camera, movement, gravity, animations, interactions, actions):
        self.controls, self.camera = controls, camera
        self.movement, self.gravity, self.animations = movement, gravity, animations
        self.interactions, self.actions = interactions, actions

    def update(self, model, message):
        model = replace(model, controls=self.controls.update(model.controls, message))
        if isinstance(message, QuitMessage):
            return replace(model, running=False)
        if isinstance(message, WindowResizeMessage):
            return replace(model, viewport=message.size)
        if isinstance(message, MouseMotionMessage) and MouseButton.MIDDLE in model.controls.pressed_mouse_buttons:
            return replace(model, camera=self.camera.update(model.camera, message))
        if isinstance(message, KeyboardMessage) and message.action == KeyboardAction.PRESS:
            if message.key == 'escape':
                return replace(model, running=False)
            if message.key == 'tab':
                return replace(model, show_inventory=not model.show_inventory)
            if message.key == 'space' and model.instances.physics['player'].is_grounded:
                physics = {**model.instances.physics, 'player': VerticalPhysics(6.0, False)}
                return replace(model, instances=replace(model.instances, physics=physics))
            if message.key == 'e':
                target = self.interactions.nearest(model.instances.positionables['player'], model.instances.characters['player'].facing,
                    model.instances.positionables, model.instances.archetyped, model.archetypes.objects, model.map.static_objects)
                if target is None:
                    return replace(model, message="Nothing to interact with nearby.")
                entity, key = target
                return self.actions.apply(model.archetypes.objects[key].action, model, entity)
        if isinstance(message, TickMessage):
            if not isfinite(message.seconds) or message.seconds < 0:
                raise ValueError("Tick duration must be finite and nonnegative")
            if message.seconds == 0:
                return model
            # Also bound externally supplied ticks; each step moves less than one tile.
            seconds = min(message.seconds, .25)
            steps = max(1, ceil(seconds * 120))
            for _ in range(steps):
                model = self.movement.update(model, TickMessage(seconds / steps))
                instances = model.instances
                positions, physics = self.gravity.step(instances.positionables, instances.physics, model.map, seconds / steps)
                characters = self.animations.step(instances.characters, seconds / steps)
                model = replace(model, instances=replace(instances, positionables=positions, physics=physics, characters=characters))
        return model


def default_updater():
    from .ControlUpdater import ControlUpdater
    from .HemisphereLookUpdater import HemisphereLookUpdater
    from .ClampedAzimuthUpdater import ClampedAzimuthUpdater
    from .actions import default_actions
    from ..model.systems.CollisionSystem import CollisionSystem
    from .MovementUpdater import MovementUpdater
    from ..model.systems.GravitySystem import GravitySystem
    from ..model.systems.CharacterAnimationSystem import CharacterAnimationSystem
    from ..model.systems.InteractionQuery import InteractionQuery
    return GameUpdater(ControlUpdater(), ClampedAzimuthUpdater(HemisphereLookUpdater()),
        MovementUpdater(CollisionSystem()), GravitySystem(), CharacterAnimationSystem(), InteractionQuery(), default_actions())
