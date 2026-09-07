from collections import defaultdict
from pyglm import glm


class TileView:
    def __init__(self, program):
        self.program = program
        self.map = None
        self.batches = {}

    def _build(self, map_):
        batches = defaultdict(lambda: ([], [], []))
        def triangle(texture, a, b, c, uv):
            positions, normals, uvs = batches[texture]
            cross = glm.cross(b - a, c - a)
            if glm.length(cross) <= 1e-8: return
            normal = glm.normalize(cross)
            positions.extend((a, b, c))
            normals.extend((normal,) * 3)
            uvs.extend(uv)
        
        uv0, uv1, uv2, uv3 = glm.vec2(0, 0), glm.vec2(1, 0), glm.vec2(0, 1), glm.vec2(1, 1)
        for y in range(map_.dimensions.y):
            for x in range(map_.dimensions.x):
                coordinate = x, y
                tile = map_.archetype(coordinate)
                min_height = map_.min_height(coordinate)
                v00, v10, v01, v11 = tuple(
                    glm.vec3(xi, yi, map_.corner_height((xi, yi), min_height))
                    for yi in (y, y + 1) 
                    for xi in (x, x + 1)
                )
                triangle(tile.texture, v00, v10, v11, (uv0, uv1, uv3))
                triangle(tile.texture, v00, v11, v01, (uv0, uv3, uv2))
                if not tile.show_exposed_sides:
                    continue
                # Match edge endpoints against the neighboring tile's own capped corners.
                edges = (
                    (v00, v01, glm.ivec2(x-1, y), glm.ivec2(1,0), glm.ivec2(1,1)),
                    (v11, v10, glm.ivec2(x+1, y), glm.ivec2(0,1), glm.ivec2(0,0)),
                    (v10, v00, glm.ivec2(x, y-1), glm.ivec2(1,1), glm.ivec2(0,1)),
                    (v01, v11, glm.ivec2(x, y+1), glm.ivec2(0,0), glm.ivec2(1,0))
                )
                for p, q, neighbor, p_offset, q_offset in edges:
                    low_p = map_.corner_height(neighbor+p_offset, map_.min_height(neighbor)) if neighbor in map_ else 0.0
                    low_q = map_.corner_height(neighbor+q_offset, map_.min_height(neighbor)) if neighbor in map_ else 0.0
                    dp, dq = p.z - low_p, q.z - low_q
                    if dp <= 0 and dq <= 0:
                        continue
                    # When edges cross, only the exposed portion belongs to this tile.
                    if dp < 0 or dq < 0:
                        t = dp / (dp - dq)
                        crossing = glm.mix(p, q, t)
                        if dp < 0:
                            p, low_p = crossing, crossing.z
                        else:
                            q, low_q = crossing, crossing.z
                    bottom_p, bottom_q = glm.vec3(p.x, p.y, low_p), glm.vec3(q.x, q.y, low_q)
                    triangle(tile.texture, p, bottom_q, bottom_p, (uv2, uv1, uv0))
                    triangle(tile.texture, p, q, bottom_q, (uv2, uv3, uv1))
        return {texture: tuple(tuple(values) for values in arrays) for texture, arrays in batches.items()}

    def draw(self, model, view):
        # Object collection changes copy Map but share the immutable tile fields.
        key = (model.map._max_heights, model.map._tile_archetype_ids)
        if self.map != key:
            self.map, self.batches = key, self._build(model.map)
        for texture, arrays in self.batches.items():
            self.program.draw(texture, *arrays, view)

    def release(self):
        self.program.release()
