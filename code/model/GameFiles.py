# HUMAN VETTED

"""Load and save game state at the filesystem boundary."""
from dataclasses import replace
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
        map_, plugin = self.load_content(map_filename, game_filenames, save_filename)
        return self.plugin_ops.load(map_, plugin)

    def load_content(self, map_filename, game_filenames, save_filename=None):
        """Compose map and plugin data without constructing an application state."""
        if not game_filenames:
            raise ValueError("At least one game file is required")
        plugins = [self._plugin(filename) for filename in game_filenames]
        plugin = self.plugin_ops.update(*plugins)

        with open(map_filename, encoding='ascii') as file:
            image = PpmImageCodec().decode(file.read())
        map_ = MapCodec(plugin.tile_palette, plugin.tiles).decode(image)

        if save_filename is not None:
            saved = self._plugin(save_filename)
            plugin = self.plugin_ops.update(*plugins, saved)
            # A save is an instance snapshot: removed objects must not respawn.
            plugin = replace(plugin, placements=dict(saved.placements),
                             physics=dict(saved.physics), characters=dict(saved.characters))
        else:
            map_objects = Plugin(
                placements=ObjectPlacementCodec(plugin.object_palette, map_).decode(image)
            )
            plugin = self.plugin_ops.update(map_objects, *plugins)

        return map_, plugin

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
