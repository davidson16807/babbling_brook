# HUMAN VETTED

"""Load and save game state at the filesystem boundary."""
from collections.abc import Iterable
import os
from pathlib import Path

from ..codec.map.MapCodec import MapCodec
from ..codec.map.ObjectPlacementCodec import ObjectPlacementCodec
from ..codec.map.PpmImageCodec import PpmImageCodec
from .GameState import GameState
from ..model.plugin.Plugin import Plugin
from ..model.plugin.PluginOps import PluginOps


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
        game_filenames: list[Path],
        save_filename: Path | None = None,
    ) -> GameState:
        plugins = [self._plugin(filename) for filename in game_filenames]
        plugin = self.plugin_ops.update(*plugins)

        # Each zone's map is relative to a loaded game file; later files take precedence.
        maps, placements = {}, {}
        for zone_id, zone in plugin.zones.items():
            candidates = [filename.parent / zone.map_filename for filename in reversed(game_filenames)]
            map_filename = next((candidate for candidate in candidates if candidate.is_file()), None)
            if map_filename is None:
                print(f"Warning: skipping zone {zone_id!r}; its map {zone.map_filename!r} was not found")
                continue
            with open(map_filename, encoding='ascii') as file:
                image = PpmImageCodec().decode(file.read())
            maps[zone_id] = MapCodec(plugin.tile_palette, plugin.tiles).decode(image)
            # Map-generated IDs are coordinates, so they are qualified by zone to stay unique.
            placements.update(
                (f'{zone_id}{entity}', placement) for entity, placement
                in ObjectPlacementCodec(plugin.object_palette, maps[zone_id], zone=zone_id).decode(image).items())

        if save_filename is not None:
            plugin = self.plugin_ops.update(plugin, self._plugin(save_filename))
        else:
            plugin = self.plugin_ops.update(Plugin(placements=placements), plugin)

        player = plugin.placements.get('player')
        if player is not None and player.zone not in maps:
            raise ValueError(f"The player's zone {player.zone!r} has no map")

        return self.plugin_ops.load(maps, plugin)

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
