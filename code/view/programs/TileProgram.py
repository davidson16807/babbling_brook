# HUMAN VETTED

from pathlib import Path

from pyglm import glm
import moderngl as gl

from ViewState import ViewState


"""
`TileProgram` renders a swarm of textured 3D tiles represented through primitives

There is no game logic or entity lookup here. Each draw establishes its own
required depth/blend state. release() is explicit resource lifecycle management.
"""

class TileProgram:
    def __init__(self, gl, textures: Textures, shader_directory: Path):
        self.textures = textures
        self.gl = gl
        self.program = ctx.program(
            vertex_shader=(shader_directory / "tile.vert").read_text(),
            fragment_shader=(shader_directory / "tile.frag").read_text()
        )
        self.textures = textures

    def draw(self, 
        texture: str,
        positions: tuple[glm.vec3, ...],
        normals: tuple[glm.vec3, ...],
        uvs: tuple[glm.vec2, ...], 
        view: ViewState
    ) -> None:
        self.gl.enable_only(gl.DEPTH_TEST)
        self.gl.depth_mask = True
        self.gl.depth_func = "<="
        self.program["clip_from_world"].write(view.clip_from_world.to_bytes())
        self.program["image"].value = 0

        ...

    def release(self):
        for _, vao, buffers in self.meshes.values():
            vao.release()
            for buffer in buffers:
                buffer.release()
        self.meshes.clear()
        self.textures.release()
        self.program.release()
