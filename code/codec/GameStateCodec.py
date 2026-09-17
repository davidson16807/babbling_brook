"""Compatibility imports; schemas now live in BabblingBrookFileCodec."""
from .BabblingBrookFileCodec import BabblingBrookFileCodec, PluginStringCodec
from .GameTablesCodec import GameRowCodec, GameTableCodec
from ..model.plugin.Plugin import Plugin


class PluginListCodec:
    item_count = 1

    def encode(self, plugin):
        return plugin.to_tables()

    def decode(self, tables):
        return Plugin.from_tables(tables)
