# HUMAN VETTED

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import replace
from math import isfinite

from pyglm import glm

from ...game.GameState import GameState
from ..Map import Map
from .Plugin import Plugin
from ..component.archetypes import CharacterArchetype
from ..component.instances import CharacterAnimationState, VerticalPhysics
from ..store import ArchetypeComponentStores, InstanceComponentStores

class PluginOps:
    """Operations for composing plugins and converting game state."""

    def update(self, *plugins: Iterable[Plugin]) -> Plugin:
        combined = Plugin()
        for plugin in plugins:
            combined = Plugin(**{
                name: {**getattr(combined, name), **getattr(plugin, name)}
                for name in Plugin.table_fields
            })
        return combined

    def load(self, map_: Map, plugin: Plugin) -> GameState:

        if any(box.archetype not in plugin.box_archetypes for box in plugin.boxes.values()):
            raise ValueError("Box refers to an unknown box archetype")

        animation_ids = {(key, name) for key, name, _, _ in plugin.animation_frames}
        for key, name in animation_ids:
            frames = {
                (direction, frame): value
                for (archetype, animation, direction, frame), value
                in plugin.animation_frames.items()
                if (archetype, animation) == (key, name)
            }
            seconds = frames[0, 0][1]
            if not isfinite(seconds) or seconds <= 0 or any(value[1] != seconds for value in frames.values()):
                raise ValueError(f"Animation {key!r}/{name!r} needs one positive frame duration")
        character_keys = {key for key, _ in animation_ids}
        for key in character_keys:
            if (key, 'standing') not in animation_ids:
                raise ValueError(f"Character {key!r} requires a standing animation")

        archetypes = ArchetypeComponentStores(
            billboards=dict(plugin.billboard_archetypes),
            boxes=dict(plugin.box_archetypes),
            characters={**{key: CharacterArchetype() for key in character_keys},
                        **plugin.character_archetypes},
            creatures=dict(plugin.creatures),
            liquids=dict(plugin.liquids),
            waypoints=dict(plugin.waypoints),
            tiles=dict(plugin.tiles),
            seasonal_tiles=dict(plugin.seasonal_tiles),
            seasonal_billboards=dict(plugin.seasonal_billboards),
        )

        physics, characters = {}, {}
        for entity, placement in plugin.billboards.items():
            key, position = placement.archetype, placement.position
            definition = archetypes.billboards[key]
            if definition.has_gravity:
                ground = map_.height(glm.vec2(position))
                physics[entity] = VerticalPhysics(0.0, abs(position.z - ground) < 1e-5)
            if key in character_keys:
                characters[entity] = CharacterAnimationState()

        instances = InstanceComponentStores(dict(plugin.billboards), physics, characters)
        instances = replace(
            instances,
            physics={**instances.physics, **plugin.physics},
            characters={**instances.characters, **plugin.characters},
            cycles=dict(plugin.cycles),
            landmarks=dict(plugin.landmarks),
            waterlevels=dict(plugin.waterlevels),
            boxes=dict(plugin.boxes),
        )

        return GameState(
            map=map_,
            globals=dict(plugin.globals),
            archetypes=archetypes,
            character_animation_frames=dict(plugin.animation_frames),
            instances=instances,
            inventory=defaultdict(int, plugin.inventory),
            biomes=dict(plugin.biomes),
            biome_spawns=dict(plugin.biome_spawns),
            zones=dict(plugin.zones),
            zone_directions=dict(plugin.zone_directions),
            zone_adjacencies=dict(plugin.zone_adjacencies),
            cardinal_waypoints=dict(plugin.cardinal_waypoints),
            colorcodes=dict(plugin.colorcodes),
        )

    def save(self, state: GameState) -> Plugin:
        return Plugin(
            format={'version': 1},
            globals=dict(state.globals),
            inventory=dict(state.inventory),
            tiles=dict(state.archetypes.tiles),
            seasonal_tiles=dict(state.archetypes.seasonal_tiles),
            seasonal_billboards=dict(state.archetypes.seasonal_billboards),
            billboard_archetypes=dict(state.archetypes.billboards),
            box_archetypes=dict(state.archetypes.boxes),
            character_archetypes=dict(state.archetypes.characters),
            creatures=dict(state.archetypes.creatures),
            liquids=dict(state.archetypes.liquids),
            waypoints=dict(state.archetypes.waypoints),
            biomes=dict(state.biomes),
            biome_spawns=dict(state.biome_spawns),
            zones=dict(state.zones),
            zone_directions=dict(state.zone_directions),
            zone_adjacencies=dict(state.zone_adjacencies),
            cardinal_waypoints=dict(state.cardinal_waypoints),
            colorcodes=dict(state.colorcodes),
            cycles=dict(state.instances.cycles),
            landmarks=dict(state.instances.landmarks),
            waterlevels=dict(state.instances.waterlevels),
            animation_frames=dict(state.character_animation_frames),
            billboards=dict(state.instances.billboards),
            boxes=dict(state.instances.boxes),
            physics=dict(state.instances.physics),
            characters=dict(state.instances.characters),
        )
