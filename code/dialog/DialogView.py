"""Pure projection from ``DialogState`` to backend-neutral drawing values."""
from __future__ import annotations

from dataclasses import dataclass

from .DialogLayout import DialogLayout
from .DialogState import NounPhraseItem


Color = tuple[int, int, int]


@dataclass(frozen=True, slots=True)
class DrawBox:
    rect: tuple[int, int, int, int]
    fill: Color
    border: Color
    border_width: int = 2
    radius: int = 4
    text: str = ''
    text_color: Color = (31, 39, 45)
    font_size: int = 23


@dataclass(frozen=True, slots=True)
class DrawText:
    position: tuple[int, int]
    text: str
    color: Color
    font_size: int


@dataclass(frozen=True, slots=True)
class DialogScene:
    viewport: tuple[int, int]
    boxes: tuple[DrawBox, ...]
    texts: tuple[DrawText, ...]


class DialogView:
    COLORS = {
        'ink': (37, 45, 50), 'paper': (244, 241, 228), 'panel': (227, 226, 211),
        'playmat': (238, 235, 217), 'chip': (253, 250, 236), 'selected': (255, 222, 119),
        'talk': (130, 199, 104), 'clear': (211, 102, 97), 'muted': (92, 101, 103),
    }

    def __init__(self, layout=None):
        self.layout = layout or DialogLayout()

    def scene(self, state):
        c, layout = self.COLORS, self.layout.build(state)
        boxes = [DrawBox(layout.inventory, c['panel'], c['ink'], 3, 5),
                 DrawBox(layout.grid, c['panel'], c['ink'], 3, 5),
                 DrawBox(layout.playmat, c['playmat'], c['ink'], 3, 5)]
        texts = [DrawText((layout.inventory[0] + 14, 4), 'LEXEMES', c['muted'], 17),
                 DrawText((layout.grid[0] + 12, layout.grid[1] - 22),
                          'INFLECTIONS', c['muted'], 17),
                 DrawText((layout.playmat[0] + 12, layout.playmat[1] - 22),
                          'PLAYMAT', c['muted'], 17),
                 DrawText((layout.grid[0], 24), 'Build a sentence by dragging words.', c['ink'], 29),
                 DrawText((layout.grid[0], 61),
                          'Click a placed word to choose its form. Drag red into a noun phrase.',
                          c['muted'], 19),
                 DrawText((layout.grid[0], 91), state.feedback, c['ink'], 21)]
        for placed in layout.elements:
            kind = placed.hit.kind
            if kind in ('inventory-panel', 'grid-panel', 'playmat'):
                continue
            if kind == 'close' and state.active_item_id is None:
                continue
            if kind == 'item' and not placed.text:
                if placed.selected:
                    boxes.append(DrawBox(placed.rect, c['selected'], c['ink'], 4, 6))
                else:
                    boxes.append(DrawBox(placed.rect, c['playmat'], c['ink'], 2, 6))
                continue
            fill = c['chip']
            if kind == 'option' and placed.selected:
                fill = c['selected']
            elif kind == 'talk':
                fill = c['talk']
            elif kind in ('clear', 'close'):
                fill = c['clear']
            boxes.append(DrawBox(placed.rect, fill, c['ink'], 3 if placed.selected else 2,
                                 4, placed.text))

        if state.active_item_id is None:
            texts.append(DrawText((layout.grid[0] + 18, layout.grid[1] + 24),
                                  'Drag a lexeme to the playmat or click a placed word.',
                                  c['muted'], 21))
        if state.drag is not None:
            drag = state.drag
            if drag.kind == 'inventory':
                text = state.lexeme(str(drag.source_id)).canonical
            elif drag.kind == 'item':
                item = state.item(int(drag.source_id))
                text = (' '.join(token.text for token in item.tokens)
                        if isinstance(item, NounPhraseItem) else item.text)
            else:
                phrase = state.item(drag.phrase_id)
                text = phrase.tokens[int(drag.source_id)].text
            width = max(58, 24 + self.layout.CHAR * len(text))
            boxes.append(DrawBox((drag.position[0] - width // 2, drag.position[1] - 20,
                                  width, self.layout.CHIP_H), c['selected'], c['ink'], 2, 4, text))
        return DialogScene(state.viewport, tuple(boxes), tuple(texts))
