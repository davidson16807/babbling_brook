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
            objects=dict(plugin.objects),
            characters={key: CharacterArchetype() for key in character_keys},
            tiles=dict(plugin.tiles),
        )

        physics, characters = {}, {}
        for entity, placement in plugin.placements.items():
            key, position = placement.archetype, placement.position
            definition = archetypes.objects[key]
            if definition.has_gravity:
                ground = map_.height(glm.vec2(position))
                physics[entity] = VerticalPhysics(0.0, abs(position.z - ground) < 1e-5)
            if key in archetypes.characters:
                characters[entity] = CharacterAnimationState()

        instances = InstanceComponentStores(dict(plugin.placements), physics, characters)
        instances = replace(
            instances,
            physics={**instances.physics, **plugin.physics},
            characters={**instances.characters, **plugin.characters},
        )

        return GameState(
            map=map_,
            globals=dict(plugin.globals),
            archetypes=archetypes,
            character_animation_frames=dict(plugin.animation_frames),
            instances=instances,
            inventory=defaultdict(int, plugin.inventory),
        )

    def save(self, state: GameState) -> Plugin:
        return Plugin(
            format={'version': 1},
            globals=dict(state.globals),
            inventory=dict(state.inventory),
            tiles=dict(state.archetypes.tiles),
            objects=dict(state.archetypes.objects),
            animation_frames=dict(state.character_animation_frames),
            placements=dict(state.instances.placements),
            physics=dict(state.instances.physics),
            characters=dict(state.instances.characters),
        )
