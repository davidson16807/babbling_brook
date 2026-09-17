# HUMAN VETTED

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import replace
from math import isfinite

from pyglm import glm

from ..GameState import GameState
from ..Map import Map
from .Plugin import Plugin
from ..component.archetypes import CharacterAnimation, CharacterArchetype, DirectionFrames
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

        animations = {}
        for (key, animation, direction, frame), (texture, seconds) in plugin.animation_frames.items():
            frames = animations.setdefault((key, animation), {})
            frames[direction, frame] = texture, seconds

        characters = {}
        for (key, name), frames in animations.items():
            if set(frames) != {(0, 0), (0, 1), (1, 0), (1, 1)}:
                raise ValueError(f"Animation {key!r}/{name!r} needs two frames in each direction")
            seconds = frames[0, 0][1]
            if not isfinite(seconds) or seconds <= 0 or any(value[1] != seconds for value in frames.values()):
                raise ValueError(f"Animation {key!r}/{name!r} needs one positive frame duration")
            characters.setdefault(key, {})[name] = CharacterAnimation(
                tuple(DirectionFrames(tuple(frames[direction, frame][0] for frame in (0, 1)))
                      for direction in (0, 1)),
                seconds,
            )
        characters = {key: CharacterArchetype(named) for key, named in characters.items()}

        archetypes = ArchetypeComponentStores(
            objects=dict(plugin.objects),
            characters=characters,
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
            map_,
            dict(plugin.globals),
            archetypes,
            instances,
            defaultdict(int, plugin.inventory),
        )

    def save(self, state: GameState) -> Plugin:
        frames = {}
        for key, character in state.archetypes.characters.items():
            for animation_name, animation in character.animations.items():
                for direction, direction_frames in enumerate(animation.directions):
                    for frame, texture in enumerate(direction_frames.textures):
                        frames[key, animation_name, direction, frame] = (
                            texture,
                            animation.seconds_per_frame,
                        )
        return Plugin(
            format={'version': 1},
            globals=dict(state.globals),
            inventory=dict(state.inventory),
            tiles=dict(state.archetypes.tiles),
            objects=dict(state.archetypes.objects),
            animation_frames=frames,
            placements=dict(state.instances.placements),
            physics=dict(state.instances.physics),
            characters=dict(state.instances.characters),
        )
