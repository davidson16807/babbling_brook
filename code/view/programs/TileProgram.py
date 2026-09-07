# HUMAN VETTED

from pathlib import Path

from pyglm import glm
import moderngl as gl

from .ViewState import ViewState
from ..Textures import Textures


"""
`TileProgram` renders a swarm of textured 3D tiles represented through primitives

There is no game logic or entity lookup here. Each draw establishes its own
required depth/blend state. release() is explicit resource lifecycle management.
"""

class TileProgram:
    def __init__(self, gl, textures: Textures, shader_directory: Path):
        self.textures = textures
        self.gl = gl
        self.program = gl.program(
            vertex_shader=(shader_directory / "tile.vert").read_text(),
            fragment_shader=(shader_directory / "tile.frag").read_text()
        )
        self.textures = textures
        self.buffers = [gl.buffer(reserve=16) for _ in range(3)]
        self.vao = gl.vertex_array(self.program, [
            (self.buffers[0], "3f", "in_position"),
            (self.buffers[1], "3f", "in_normal"),
            (self.buffers[2], "2f", "in_uv")])
        self.released = False

    def draw(self, 
        texture: str,
        positions: tuple[glm.vec3, ...],
        normals: tuple[glm.vec3, ...],
        uvs: tuple[glm.vec2, ...], 
        view: ViewState
    ) -> None:
        if self.released or not positions:
            return
        if not len(positions) == len(normals) == len(uvs) or len(positions) % 3:
            raise ValueError("Tile attributes must describe complete triangles")
        self.gl.enable_only(gl.DEPTH_TEST)
        self.gl.fbo.depth_mask = True
        self.gl.depth_func = "<="
        self.program["clip_from_world"].write(view.clip_from_world.to_bytes())
        self.program["image"].value = 0

        self.textures.get(texture).use(0)
        for buffer, values in zip(self.buffers, (positions, normals, uvs)):
            data = memoryview(b"".join(value.to_bytes() for value in values))
            if buffer.size < data.nbytes:
                buffer.orphan(data.nbytes)
            buffer.write(data)
        self.vao.render(gl.TRIANGLES, vertices=len(positions))

    def release(self):
        if self.released:
            return
        self.released = True
        self.vao.release()
        for buffer in self.buffers:
            buffer.release()
        self.program.release()
