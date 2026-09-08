from collections import defaultdict
from math import cos, sin
from pyglm import glm


class BillboardView:
    def __init__(self, program):
        self.program = program

    def draw(self, model, view):
        toward_camera = glm.vec2(cos(model.camera.look_azimuth), sin(model.camera.look_azimuth))
        objects = [(entity, model.instances.archetyped[entity], position) for entity, position in model.instances.positionables.items()]
        objects += [(entity, placement.archetype, placement.position) for entity, placement in model.map.static_objects.items()]
        batches = defaultdict(lambda: ([], [], [], []))
        for entity, key, position in objects:
            definition = model.archetypes.objects[key]
            texture, mirrored = definition.texture, False
            if key in model.archetypes.characters:
                state = model.instances.characters[entity]
                archetype = model.archetypes.characters[key]
                animation = getattr(archetype, state.animation, None) or archetype.walking or archetype.standing
                direction = 0 if glm.dot(state.facing, toward_camera) >= 0 else 1
                frame = int(state.elapsed / animation.seconds_per_frame) % 2
                texture = animation.directions[direction].textures[frame]
                mirrored = glm.dot(glm.vec3(state.facing, 0), view.camera_right) > 0
            origins, sizes, uv_rects, mirrors = batches[texture]
            origins.append(position)
            sizes.append(glm.vec2(definition.width, definition.height))
            uv_rects.append(glm.vec4(0, 0, 1, 1))
            mirrors.append(mirrored)

        for texture, (origins, sizes, uv_rects, mirrors) in batches.items():
            self.program.draw(
                texture,
                tuple(origins),
                tuple(sizes),
                tuple(uv_rects),
                tuple(mirrors),
                view,
            )

    def release(self):
        self.program.release()
