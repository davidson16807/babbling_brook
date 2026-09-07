# HUMAN VETTED

from pathlib import Path
from struct import pack

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
        self.coordinate_buffer = gl.buffer(reserve=16)
        self.southwest_buffer = gl.buffer(reserve=16)
        self.southeast_buffer = gl.buffer(reserve=16)
        self.northwest_buffer = gl.buffer(reserve=16)
        self.northeast_buffer = gl.buffer(reserve=16)
        self.west_lower_buffer = gl.buffer(reserve=16)
        self.east_lower_buffer = gl.buffer(reserve=16)
        self.south_lower_buffer = gl.buffer(reserve=16)
        self.north_lower_buffer = gl.buffer(reserve=16)
        self.exposed_sides_buffer = gl.buffer(reserve=16)
        self.vao = gl.vertex_array(self.program, [
            (self.coordinate_buffer, "2f /i", "in_coordinate"),
            (self.southwest_buffer, "1f /i", "in_southwest"),
            (self.southeast_buffer, "1f /i", "in_southeast"),
            (self.northwest_buffer, "1f /i", "in_northwest"),
            (self.northeast_buffer, "1f /i", "in_northeast"),
            (self.west_lower_buffer, "2f /i", "in_west_lower"),
            (self.east_lower_buffer, "2f /i", "in_east_lower"),
            (self.south_lower_buffer, "2f /i", "in_south_lower"),
            (self.north_lower_buffer, "2f /i", "in_north_lower"),
            (self.exposed_sides_buffer, "1f /i", "in_exposed_sides")])
        self.released = False

    def draw(self,
        texture: str,
        coordinates: tuple[tuple[int, int], ...],
        southwest: tuple[float, ...],
        southeast: tuple[float, ...],
        northwest: tuple[float, ...],
        northeast: tuple[float, ...],
        west_lower: tuple[tuple[float, float], ...],
        east_lower: tuple[tuple[float, float], ...],
        south_lower: tuple[tuple[float, float], ...],
        north_lower: tuple[tuple[float, float], ...],
        exposed_sides: tuple[bool, ...],
        view: ViewState
    ) -> None:
        """Draw unit tiles from parallel per-tile collections.

        Each named corner supplies one height per tile; north is +y.
        Each side supplies two lower endpoint heights: west/east run south
        to north; south/north run west to east. The caller chooses boundary
        heights (for example, two zeros).
        Top triangles share the southwest–northeast diagonal. Texture names are resolved
        through Textures, as for the other programs.
        """
        if self.released: return
        attributes = (coordinates, southwest, southeast, northwest, northeast,
                      west_lower, east_lower, south_lower, north_lower, exposed_sides)
        self.gl.enable_only(gl.DEPTH_TEST)
        self.gl.fbo.depth_mask = True
        self.gl.depth_func = "<="
        self.program["clip_from_world"].write(view.clip_from_world.to_bytes())
        self.program["image"].value = 0

        self.textures.get(texture).use(0)
        # Upload per-tile properties; gl_VertexID supplies the fixed topology.
        coordinate_data = pack(f"{2 * len(coordinates)}f", *(value for pair in coordinates for value in pair))
        if self.coordinate_buffer.size < len(coordinate_data):
            self.coordinate_buffer.orphan(len(coordinate_data))
        self.coordinate_buffer.write(coordinate_data)

        southwest_data = pack(f"{len(southwest)}f", *southwest)
        if self.southwest_buffer.size < len(southwest_data):
            self.southwest_buffer.orphan(len(southwest_data))
        self.southwest_buffer.write(southwest_data)

        southeast_data = pack(f"{len(southeast)}f", *southeast)
        if self.southeast_buffer.size < len(southeast_data):
            self.southeast_buffer.orphan(len(southeast_data))
        self.southeast_buffer.write(southeast_data)

        northwest_data = pack(f"{len(northwest)}f", *northwest)
        if self.northwest_buffer.size < len(northwest_data):
            self.northwest_buffer.orphan(len(northwest_data))
        self.northwest_buffer.write(northwest_data)

        northeast_data = pack(f"{len(northeast)}f", *northeast)
        if self.northeast_buffer.size < len(northeast_data):
            self.northeast_buffer.orphan(len(northeast_data))
        self.northeast_buffer.write(northeast_data)

        west_lower_data = pack(f"{2 * len(west_lower)}f", *(value for pair in west_lower for value in pair))
        if self.west_lower_buffer.size < len(west_lower_data):
            self.west_lower_buffer.orphan(len(west_lower_data))
        self.west_lower_buffer.write(west_lower_data)

        east_lower_data = pack(f"{2 * len(east_lower)}f", *(value for pair in east_lower for value in pair))
        if self.east_lower_buffer.size < len(east_lower_data):
            self.east_lower_buffer.orphan(len(east_lower_data))
        self.east_lower_buffer.write(east_lower_data)

        south_lower_data = pack(f"{2 * len(south_lower)}f", *(value for pair in south_lower for value in pair))
        if self.south_lower_buffer.size < len(south_lower_data):
            self.south_lower_buffer.orphan(len(south_lower_data))
        self.south_lower_buffer.write(south_lower_data)

        north_lower_data = pack(f"{2 * len(north_lower)}f", *(value for pair in north_lower for value in pair))
        if self.north_lower_buffer.size < len(north_lower_data):
            self.north_lower_buffer.orphan(len(north_lower_data))
        self.north_lower_buffer.write(north_lower_data)

        exposed_sides_data = pack(f"{len(exposed_sides)}f", *exposed_sides)
        if self.exposed_sides_buffer.size < len(exposed_sides_data):
            self.exposed_sides_buffer.orphan(len(exposed_sides_data))
        self.exposed_sides_buffer.write(exposed_sides_data)
        # Two top triangles and two for each side. Hidden sides degenerate.
        self.vao.render(gl.TRIANGLES, vertices=30, instances=len(coordinates))

    def release(self):
        if self.released: return
        self.released = True
        self.vao.release()
        self.coordinate_buffer.release()
        self.southwest_buffer.release()
        self.southeast_buffer.release()
        self.northwest_buffer.release()
        self.northeast_buffer.release()
        self.west_lower_buffer.release()
        self.east_lower_buffer.release()
        self.south_lower_buffer.release()
        self.north_lower_buffer.release()
        self.exposed_sides_buffer.release()
        self.program.release()
