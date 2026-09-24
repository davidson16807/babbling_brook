"""Load palette definitions and save the editor's PPM at the filesystem boundary."""
from dataclasses import replace
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

from ..codec.GameStateCodec import PluginStringCodec
from ..codec.map.MapCodec import MapCodec
from ..codec.map.ObjectPlacementCodec import ObjectPlacementCodec
from ..codec.map.PpmImageCodec import PpmImageCodec
from .EditorState import EditorState
from .plugin.PluginOps import PluginOps


class EditorFiles:
    def __init__(self, data_directory: Path):
        self.data_directory = data_directory

    def load(self, filename: Path) -> EditorState:
        filename = filename.resolve()
        definitions = filename.parent / 'world.game'
        if not definitions.is_file():
            definitions = self.data_directory / 'world.game'
        codec = PluginStringCodec()
        plugin = codec.decode(definitions.read_text(encoding='utf-8'))
        companion = filename.with_suffix('.game')
        if companion.is_file() and companion.resolve() != definitions.resolve():
            plugin = PluginOps().update(plugin, codec.decode(companion.read_text(encoding='utf-8')))
        image = PpmImageCodec().decode(filename.read_text(encoding='ascii'))
        map_ = MapCodec(plugin.tile_palette, plugin.tiles).decode(image)
        placements = ObjectPlacementCodec(plugin.object_palette, map_).decode(image)
        # Only PPM objects belong in this editor; plugin placements include game-specific actors.
        return EditorState(
            filename, image, image, map_, placements,
            plugin.tile_palette, plugin.object_palette, plugin.tiles, plugin.objects,
            (image.width // 2, image.height // 2),
        )

    def save(self, state: EditorState) -> EditorState:
        text = PpmImageCodec().encode(state.image)
        temporary = None
        try:
            with NamedTemporaryFile(mode='w', encoding='ascii', newline='\n',
                                    dir=state.filename.parent, delete=False) as output:
                temporary = Path(output.name)
                output.write(text)
                output.flush()
                os.fsync(output.fileno())
            os.chmod(temporary, state.filename.stat().st_mode & 0o777)
            os.replace(temporary, state.filename)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
        return replace(state, saved_image=state.image, quit_pending=False,
                       message=f'Saved {state.filename.name}.')
