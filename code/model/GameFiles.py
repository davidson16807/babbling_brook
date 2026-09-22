# HUMAN VETTED

"""Load and save game state at the filesystem boundary."""
from collections.abc import Iterable
import os
from pathlib import Path

from ..codec.map.MapCodec import MapCodec
from ..codec.map.ObjectPlacementCodec import ObjectPlacementCodec
from ..codec.map.PpmImageCodec import PpmImageCodec
from .GameState import GameState
from .plugin.Plugin import Plugin
from .plugin.PluginOps import PluginOps


class GameFiles:
    """Compose game plugins with a map and persist game state."""

    def __init__(self, plugin_ops: PluginOps, plugin_string_codec):
        self.plugin_ops = plugin_ops
        self.plugin_string_codec = plugin_string_codec

    def _plugin(self, filename: Path) -> Plugin:
        with open(filename, encoding='utf-8') as file:
            return self.plugin_string_codec.decode(file.read())

    def load(
        self,
        map_filename: Path,
        game_filenames: list[Path],
        save_filename: Path | None = None,
    ) -> GameState:
        plugins = [self._plugin(filename) for filename in game_filenames]
        plugin = self.plugin_ops.update(*plugins)

        with open(map_filename, encoding='ascii') as file:
            image = PpmImageCodec().decode(file.read())
        map_ = MapCodec(plugin.tile_palette, plugin.tiles).decode(image)

        if save_filename is not None:
            plugin = self.plugin_ops.update(*plugins, self._plugin(save_filename))
        else:
            map_objects = Plugin(
                placements=ObjectPlacementCodec(plugin.object_palette, map_).decode(image)
            )
            plugin = self.plugin_ops.update(map_objects, *plugins)

        return self.plugin_ops.load(map_, plugin)

    def save(self, filename: Path, state: GameState) -> None:
        plugin = self.plugin_ops.save(state)
        filename.parent.mkdir(parents=True, exist_ok=True)
        temporary = filename.with_name(filename.name + '.tmp')
        try:
            with open(temporary, 'w', encoding='utf-8', newline='\n') as file:
                file.write(self.plugin_string_codec.encode(plugin) + '\n')
                file.flush()
                os.fsync(file.fileno())
            os.replace(temporary, filename)
        finally:
            if temporary.exists():
                temporary.unlink()
