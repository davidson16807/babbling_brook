from itertools import groupby
from math import cos, sin
from pyglm import glm


class BillboardView:
    def __init__(self, program):
        self.program = program

    def draw(self, model, view):
        toward_camera = glm.vec2(cos(model.camera.look_azimuth), sin(model.camera.look_azimuth))
        objects = [(entity, model.instances.archetyped[entity], position) for entity, position in model.instances.positionables.items()]
        objects += [(entity, placement.archetype, placement.position) for entity, placement in model.map.static_objects.items()]
        objects.sort(key=lambda item: glm.dot(glm.vec2(item[2]), toward_camera))
        primitives = []
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
            primitives.append((
                texture,
                position,
                glm.vec2(definition.width, definition.height),
                glm.vec4(0, 0, 1, 1),
                mirrored,
            ))

        # Batch consecutive textures without disturbing back-to-front order.
        for texture, batch in groupby(primitives, key=lambda primitive: primitive[0]):
            batch = tuple(batch)
            origins = tuple(primitive[1] for primitive in batch)
            sizes = tuple(primitive[2] for primitive in batch)
            uv_rects = tuple(primitive[3] for primitive in batch)
            mirrored = tuple(primitive[4] for primitive in batch)
            self.program.draw(texture, origins, sizes, uv_rects, mirrored, view)

    def release(self):
        self.program.release()
