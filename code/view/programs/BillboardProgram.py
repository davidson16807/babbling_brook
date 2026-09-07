# HUMAN VETTED

from pathlib import Path
from struct import pack

from pyglm import glm
import moderngl as gl

from ..Textures import Textures
from .ViewState import ViewState

"""
`BillboardProgram` renders a swarm of textured cylindrical billboards represented through primitives
"""

class BillboardProgram:
    def __init__(self, gl, textures: Textures, shader_directory: Path):
        self.gl = gl
        self.program = gl.program(
            vertex_shader=(shader_directory / "billboard.vert").read_text(),
            fragment_shader=(shader_directory / "billboard.frag").read_text()
        )
        self.textures = textures
        self.quad = gl.buffer(b"".join(value.to_bytes() for value in [glm.vec2(0, 0), glm.vec2(1, 0), glm.vec2(1, 1),
            glm.vec2(0, 0), glm.vec2(1, 1), glm.vec2(0, 1)]))
        self.buffers = [gl.buffer(reserve=16) for _ in range(4)]
        self.vao = gl.vertex_array(self.program, [(self.quad, "2f", "in_corner"),
            (self.buffers[0], "3f /i", "in_origin"), (self.buffers[1], "2f /i", "in_size"),
            (self.buffers[2], "4f /i", "in_uv_rect"), (self.buffers[3], "1f /i", "in_mirror")])

        self.released = False

    def draw(self, 
        textures: tuple[str, ...],
        origin: tuple[glm.vec3, ...],
        size: tuple[glm.vec2, ...],
        uv_rect: tuple[glm.vec4, ...],
        mirrored: tuple[bool, ...],
        view: ViewState
    ) -> None:
        if self.released or not origin:
            return
        if len({len(values) for values in (textures, origin, size, uv_rect, mirrored)}) != 1:
            raise ValueError("Billboard attributes must have equal lengths")
        self.gl.enable_only(gl.DEPTH_TEST | gl.BLEND)
        self.gl.fbo.depth_mask = True
        self.gl.depth_func = "<="
        self.gl.blend_func = gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA
        self.program["clip_from_world"].write(view.clip_from_world.to_bytes())
        self.program["camera_right"].value = tuple(view.camera_right)
        self.program["image"].value = 0

        # The view supplies back-to-front instances. Keep that order when textures differ.
        for i, texture in enumerate(textures):
            self.textures.get(texture).use(0)
            values = (origin[i].to_bytes(), size[i].to_bytes(), uv_rect[i].to_bytes(),
                      pack("f", float(mirrored[i])))
            for buffer, data in zip(self.buffers, values):
                buffer.write(data)
            self.vao.render(gl.TRIANGLES, vertices=6, instances=1)

    def release(self):
        if self.released:
            return
        self.released = True
        self.vao.release()
        for buffer in self.buffers:
            buffer.release()
        self.quad.release()
        self.program.release()
