"""Pure layout and hit testing shared by updater and view."""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256

from .DialogLexicon import phrase_options
from .DialogState import DialogState, NounPhraseItem


Rect = tuple[int, int, int, int]


def contains(rect: Rect, point: tuple[int, int]) -> bool:
    x, y, width, height = rect
    return x <= point[0] < x + width and y <= point[1] < y + height


@dataclass(frozen=True, slots=True)
class Hit:
    kind: str
    value: object = None
    parent: int | None = None


@dataclass(frozen=True, slots=True)
class Placed:
    rect: Rect
    hit: Hit
    text: str = ''
    selected: bool = False


@dataclass(frozen=True, slots=True)
class Layout:
    inventory: Rect
    grid: Rect
    playmat: Rect
    close: Rect
    clear: Rect
    talk: Rect
    elements: tuple[Placed, ...]

    def hit(self, position):
        # Later elements are visually on top.
        return next((item.hit for item in reversed(self.elements)
                     if contains(item.rect, position)), Hit('background'))

    def phrase_at(self, position):
        hit = self.hit(position)
        if hit.kind in ('item', 'token') and hit.parent is not None:
            return hit.parent
        if hit.kind == 'item' and isinstance(hit.value, int):
            return hit.value
        return None


class DialogLayout:
    CHAR = 13
    CHIP_H = 40
    GAP = 10

    def _width(self, text):
        return max(58, 24 + self.CHAR * len(text))

    def _ordered_options(self, state, item):
        if isinstance(item, NounPhraseItem):
            options = phrase_options(item, state.lexemes)
        else:
            options = tuple((form.text, form) for form in state.lexeme(item.lexeme_id).inflections)
        def order(option):
            digest = sha256(f'{state.session_seed}:{item.lexeme_id if hasattr(item, "lexeme_id") else item.noun_lexeme_id}:{option[0]}'.encode()).digest()
            return digest
        return tuple(sorted(options, key=order))

    def build(self, state: DialogState) -> Layout:
        width, height = state.viewport
        margin, inventory_w = 16, min(270, max(190, width // 4))
        inventory = (margin, margin, inventory_w, max(100, height - margin * 2))
        left = inventory[0] + inventory[2] + 18
        content_w = max(220, width - left - margin)
        playmat_h = 82
        playmat = (left, height - margin - playmat_h, content_w, playmat_h)
        grid_h = min(210, max(125, height // 3))
        grid = (left, playmat[1] - 12 - grid_h, content_w, grid_h)
        close = (grid[0] + grid[2] - 42, grid[1] + 10, 30, 30)
        clear = (playmat[0] + playmat[2] - 188, playmat[1] + 20, 68, 42)
        talk = (playmat[0] + playmat[2] - 110, playmat[1] + 20, 96, 42)
        elements = [Placed(inventory, Hit('inventory-panel')),
                    Placed(grid, Hit('grid-panel')), Placed(playmat, Hit('playmat'))]
        if state.active_item_id is not None:
            elements.append(Placed(close, Hit('close'), '×'))
        elements.extend((Placed(clear, Hit('clear'), 'clear'),
                         Placed(talk, Hit('talk'), 'talk (E)')))

        y = inventory[1] + 18
        for lexeme in state.lexemes:
            rect = (inventory[0] + 14, y, min(inventory[2] - 28, self._width(lexeme.canonical)), self.CHIP_H)
            elements.append(Placed(rect, Hit('inventory', lexeme.id), lexeme.canonical))
            y += self.CHIP_H + 8

        x = playmat[0] + 14
        for item in state.playmat:
            if isinstance(item, NounPhraseItem):
                token_widths = [self._width(token.text) for token in item.tokens]
                item_w = sum(token_widths) + self.GAP * (len(token_widths) - 1) + 16
                item_rect = (x, playmat[1] + 16, item_w, 50)
                elements.append(Placed(item_rect, Hit('item', item.id, item.id), '', state.active_item_id == item.id))
                tx = x + 8
                for index, (token, token_w) in enumerate(zip(item.tokens, token_widths)):
                    rect = (tx, playmat[1] + 21, token_w, self.CHIP_H)
                    elements.append(Placed(rect, Hit('token', index, item.id), token.text))
                    tx += token_w + self.GAP
                x += item_w + self.GAP
            else:
                item_w = self._width(item.text)
                rect = (x, playmat[1] + 21, item_w, self.CHIP_H)
                elements.append(Placed(rect, Hit('item', item.id), item.text, state.active_item_id == item.id))
                x += item_w + self.GAP

        active = state.item(state.active_item_id) if state.active_item_id is not None else None
        if active is not None:
            gx, gy = grid[0] + 18, grid[1] + 18
            for index, (text, option) in enumerate(self._ordered_options(state, active)):
                cell_w = min(grid[2] - 72, max(170, self._width(text)))
                if gx + cell_w > grid[0] + grid[2] - 54:
                    gx, gy = grid[0] + 18, gy + self.CHIP_H + 10
                selected = text == ' '.join(token.text for token in active.tokens) if isinstance(active, NounPhraseItem) else text == active.text
                elements.append(Placed((gx, gy, cell_w, self.CHIP_H),
                                       Hit('option', index, active.id), text, selected))
                gx += cell_w + self.GAP

        return Layout(inventory, grid, playmat, close, clear, talk, tuple(elements))

    def option(self, state, item, index):
        return self._ordered_options(state, item)[index]

    def playmat_index(self, layout: Layout, state: DialogState, x: int) -> int:
        item_boxes = [placed for placed in layout.elements if placed.hit.kind == 'item']
        for index, placed in enumerate(item_boxes):
            if x < placed.rect[0] + placed.rect[2] // 2:
                return index
        return len(state.playmat)

    def token_index(self, layout: Layout, phrase_id: int, x: int) -> int:
        tokens = [placed for placed in layout.elements
                  if placed.hit.kind == 'token' and placed.hit.parent == phrase_id]
        for index, placed in enumerate(tokens):
            if x < placed.rect[0] + placed.rect[2] // 2:
                return index
        return len(tokens)
