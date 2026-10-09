# HUMAN REVIEWED

from dataclasses import replace

from pyglm import glm

from ..messages import (KeyboardMessage, KeyboardAction, MouseButton, MouseMotionMessage,
    QuitMessage, WindowResizeMessage)
from ..model.component.archetype import Waypoint
from ..model.component.instance import VerticalPhysics

class GameUpdater:
    def __init__(self, mouselook, keylook, interactions, actions, waypoint_query, jump_speed=6):

        self.mouselook = mouselook
        self.keylook = keylook
        self.interactions = interactions
        self.actions = actions
        self.waypoint_query = waypoint_query
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
                player = game.instances.placements['player']
                target = self.interactions.nearest(
                    player.position,
                    game.instances.characters['player'].facing,
                    # Only placements in the player's zone can be interacted with.
                    {entity: placement for entity, placement in game.instances.placements.items()
                     if placement.zone == player.zone},
                    # Doors are waypoints activated by interaction.
                    {**game.archetypes.actionables,
                     **{key: waypoint for key, waypoint in game.archetypes.waypoints.items() if waypoint.door}},
                )
                if target is None:
                    return replace(game, message="Nothing to interact with nearby.")
                entity, component = target
                if isinstance(component, Waypoint):
                    arrival = self.waypoint_query.destination(
                        entity, game.instances.placements, game.maps,
                        game.archetypes.waypoints, game.archetypes.cardinal_waypoints,
                        game.zone_adjacencies, game.zone_directions)
                    if arrival is None:
                        return game
                    placements = {**game.instances.placements, 'player': replace(
                        player, zone=arrival.zone, position=glm.vec3(arrival.position))}
                    return replace(game, instances=replace(game.instances, placements=placements))
                return self.actions.apply(component.action, game, entity)
            else:
                game = replace(
                    game,
                    camera=self.keylook.update(game.camera, message),
                )
        return game
