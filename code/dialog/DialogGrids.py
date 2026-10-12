"""Transitions of the dialog's inflection grid, the one place inflections are generated.

A grid offers every inflection of one placed constituent's lexeme. Inflections that read the
same share a cell, and the cells are shuffled in an
order fixed per lexeme and dialog session. The options are generated when the grid opens and
kept in the state, so drawing never generates them.
"""
import random
from dataclasses import replace

from .DialogState import Constituent, Grid


class DialogGrids:
    def __init__(self, addresses, address_operations, text, lexeme, inflections):
        """`text(rule)` reads a `Rule`, `lexeme(rule)` is the lexeme it inflects, and
        `inflections(lexeme)` generates its every `Rule`."""
        self.addresses = addresses
        self.address_operations = address_operations
        self.text = text
        self.lexeme = lexeme
        self.inflections = inflections

    def options(self, seed, lexeme) -> tuple:
        """Seeding with a string keeps the order identical across processes; `hash()` would not."""
        readings = {}
        for rule in self.inflections(lexeme):
            readings.setdefault(self.text(rule), rule)
        options = list(readings.values())
        random.Random(f'{seed}/{lexeme}').shuffle(options)
        return tuple(options)

    def open(self, state, address):
        """Open the grid of the constituent at this address, scrolled to show its inflection.
        A child a phrase was generated with, such as its article, opens its phrase's grid."""
        if not isinstance(self.addresses.resolve(state.statement, address), Constituent):
            address = self.addresses.parent(address)
        lexeme = self.lexeme(self.addresses.resolve(state.statement, address).inflection)
        return replace(state, grid=Grid(address, self.options(state.seed, lexeme)), grid_scroll=None)

    def toggle(self, state, address):
        """Close the grid if it is this constituent's, else open this constituent's."""
        if not isinstance(self.addresses.resolve(state.statement, address), Constituent):
            address = self.addresses.parent(address)
        if state.grid is not None and state.grid.address == address:
            return self.close(state)
        return self.open(state, address)

    def choose(self, state, index):
        """Give the grid's constituent the inflection in this cell; the grid stays open."""
        if state.grid is None or not 0 <= index < len(state.grid.options):
            return state
        statement = self.address_operations.reinflect(state.statement, state.grid.address,
                                                      state.grid.options[index])
        return replace(state, statement=statement)

    def follow(self, state, source, address, renamed):
        """Keep the grid on its constituent after what was at `source` was dropped at `address`, or
        removed if that is None, and its old siblings were `renamed`. If the grid's constituent was
        what was dropped, or within it, the grid goes with it, or closes if it was removed."""
        if state.grid is None:
            return state
        followed = self.address_operations.readdress(state.grid.address, source, renamed)
        if followed is None and address is not None:
            followed = (*address, *state.grid.address[len(source):])
        return replace(state, grid=None if followed is None else replace(state.grid, address=followed))

    def close(self, state):
        """Collapsing the grid keeps whatever inflection is selected."""
        return replace(state, grid=None)
