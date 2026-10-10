"""Pure geometry for the dialog: where every box goes, and what the pointer is over.

`DialogUpdater` hit-tests against the same layout that `DialogView` draws, so the
GUI keeps no positions of its own between frames. Boxes carry style names, not
colors; `DialogView` maps names to appearances.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from math import ceil

from pyglm import glm

from .DialogState import Slot, Word
from .playmat import arrange, find, phrase_items, texts as slot_texts, without, without_slot

Rect = tuple[int, int, int, int]  # left, top, width, height in viewport pixels


# What a press refers to.
@dataclass(frozen=True)
class InventoryTarget:
    lexeme: str

@dataclass(frozen=True)
class WordTarget:
    id: int          # a placed word; pressing a phrase's noun refers to the phrase

@dataclass(frozen=True)
class SlotTarget:
    id: int          # the noun phrase
    slot: Slot       # its article, adposition, or other word that came with its inflection

@dataclass(frozen=True)
class CellTarget:
    id: int          # the word whose grid this is
    inflection: str

@dataclass(frozen=True)
class ButtonTarget:
    name: str        # 'talk' or 'close'

@dataclass(frozen=True)
class PanelTarget:
    name: str        # 'inventory', 'grid', or 'playmat'


# Where a drag would land if released now.
@dataclass(frozen=True)
class PlaymatDrop:
    index: int       # among the playmat's words, not counting the dragged one

@dataclass(frozen=True)
class PhraseDrop:
    id: int          # the noun phrase
    index: int       # in its arrangement, not counting the dragged item

@dataclass(frozen=True)
class RemoveDrop:
    pass


@dataclass(frozen=True)
class LaidBox:
    rect: Rect
    style: str
    text: str = ''
    target: object = None


@dataclass(frozen=True)
class Layout:
    boxes: tuple[LaidBox, ...]                 # in draw order
    anchors: dict[object, Rect] = field(default_factory=dict)  # rect of each draggable thing
    drop: object = None
    limits: dict[str, int] = field(default_factory=dict)      # greatest scroll of each panel
    scroll: dict[str, int] = field(default_factory=dict)      # first visible row of each panel

    def hit(self, point: glm.vec2):
        """The topmost target under `point`, else None."""
        for box in reversed(self.boxes):
            if box.target is not None and contains(box.rect, point):
                return box.target
        return None

    def panel(self, point: glm.vec2):
        """Name of the panel under `point`, else None."""
        for box in reversed(self.boxes):
            if isinstance(box.target, PanelTarget) and contains(box.rect, point):
                return box.target.name
        return None


def contains(rect: Rect, point, margin=0) -> bool:
    x, y, w, h = rect
    return x - margin <= point.x < x + w + margin and y - margin <= point.y < y + h + margin


@dataclass(frozen=True)
class DialogMetrics:
    text: object          # see view/TextMetrics.py
    font_size: int = 22
    margin: int = 16      # around panels
    padding: int = 10     # inside panels
    gap: int = 8          # between chips
    chip_padding: tuple[int, int] = (8, 4)
    phrase_padding: int = 5
    scrollbar: int = 10
    grid_rows: int = 4    # visible rows before the grid scrolls


@dataclass
class _Placed:
    word: Word
    rect: Rect
    children: list  # display-sequence rects, for noun phrases


class DialogLayout:
    TALK = 'talk (E)'
    CLOSE = 'X'

    def __init__(self, lexicon, metrics: DialogMetrics):
        self.lexicon = lexicon
        self.metrics = metrics
        self.inventory = lexicon.sorted()

    def options(self, seed: int, lexeme) -> list[str]:
        """Inflection texts in grid order: shuffled per lexeme and dialog session.

        Seeding with a string keeps the order identical across processes;
        `hash()` would not.
        """
        texts = [inflection.text for inflection in lexeme.inflections]
        random.Random(f'{seed}/{lexeme.id}').shuffle(texts)
        return texts

    def chip_size(self, text: str) -> tuple[int, int]:
        m = self.metrics
        return (m.text.width(text, m.font_size) + 2 * m.chip_padding[0],
                m.text.height(m.font_size) + 2 * m.chip_padding[1])

    @property
    def chip_height(self) -> int:
        return self.chip_size('')[1]

    def phrase_texts(self, word: Word, inflection_text: str) -> list[str]:
        """The phrase's words as they would read with `inflection_text`, in the player's order."""
        inflection = self.lexicon.lexemes[word.lexeme].inflection(inflection_text)
        rearranged = Word(word.id, word.lexeme, inflection_text, arrange(word.arrangement, inflection))
        return [text for _, text in phrase_items(rearranged, inflection)]

    def word(self, word: Word, x: int, y: int, grid, interactive=True, suffix=''):
        """Lay out one placed word with its top-left at (x, y): (rect, boxes, child rects)."""
        m = self.metrics
        lexeme = self.lexicon.lexemes[word.lexeme]
        selected = '-selected' if grid == word.id else ''
        target = WordTarget(word.id) if interactive else None
        if not lexeme.is_noun_phrase:
            w, h = self.chip_size(word.inflection)
            rect = (x, y + m.phrase_padding, w, h)
            return rect, [LaidBox(rect, 'chip' + (suffix or selected), word.inflection, target)], []
        boxes, children = [], []
        cx = x + m.phrase_padding
        for item, text in phrase_items(word, lexeme.inflection(word.inflection)):
            w, h = self.chip_size(text)
            rect = (cx, y + m.phrase_padding, w, h)
            if isinstance(item, Word):
                style = 'chip-selected' if grid == item.id and not suffix else 'chip'
                item_target = WordTarget(item.id)
            else:
                # The noun stands for its phrase: pressing it moves or opens the phrase.
                style = 'token'
                item_target = target if item.part == 'n' else SlotTarget(word.id, item)
            boxes.append(LaidBox(rect, style, text, item_target if interactive else None))
            children.append(rect)
            cx += w + m.gap // 2
        width = cx - m.gap // 2 + m.phrase_padding - x
        rect = (x, y, width, self.chip_height + 2 * m.phrase_padding)
        return rect, [LaidBox(rect, 'phrase' + (suffix or selected), '', target), *boxes], children

    def scrollbar(self, panel: Rect, first: int, visible: int, total: int) -> list[LaidBox]:
        m = self.metrics
        x, y, w, h = panel
        track = (x + w - m.padding - m.scrollbar, y + m.padding, m.scrollbar, h - 2 * m.padding)
        if total <= visible:
            thumb = track
        else:
            height = max(2 * m.scrollbar, round(track[3] * visible / total))
            top = track[1] + round((track[3] - height) * first / (total - visible))
            thumb = (track[0], top, m.scrollbar, height)
        return [LaidBox(track, 'track'), LaidBox(thumb, 'thumb')]

    def layout(self, state) -> Layout:
        m = self.metrics
        vw, vh = state.viewport
        boxes, anchors, limits, scroll = [], {}, {}, {}
        chip_h = self.chip_height
        row_h = chip_h + m.gap

        # Inventory: every lexeme, pronouns first, then alphabetical.
        inventory_w = (max((self.chip_size(lexeme.display)[0] for lexeme in self.inventory), default=0)
                       + 2 * m.padding + m.gap + m.scrollbar)
        inventory = (m.margin, m.margin, inventory_w, vh - 2 * m.margin)
        boxes.append(LaidBox(inventory, 'panel', target=PanelTarget('inventory')))
        visible = max(1, (inventory[3] - 2 * m.padding + m.gap) // row_h)
        limits['inventory'] = max(0, len(self.inventory) - visible)
        first = scroll['inventory'] = max(0, min(state.inventory_scroll, limits['inventory']))
        for row, lexeme in enumerate(self.inventory[first:first + visible]):
            target = InventoryTarget(lexeme.id)
            rect = (inventory[0] + m.padding, inventory[1] + m.padding + row * row_h,
                    *self.chip_size(lexeme.display))
            boxes.append(LaidBox(rect, 'chip', lexeme.display, target))
            anchors[target] = rect
        boxes += self.scrollbar(inventory, first, visible, len(self.inventory))

        # Playmat: placed words left to right, then the close and talk buttons.
        left = inventory[0] + inventory_w + m.margin
        phrase_h = chip_h + 2 * m.phrase_padding
        bar_h = phrase_h + 2 * m.padding
        bar = (left, vh - m.margin - bar_h, vw - left - m.margin, bar_h)
        boxes.append(LaidBox(bar, 'panel', target=PanelTarget('playmat')))
        drag = state.drag
        playmat = state.playmat
        if drag is not None and drag.from_playmat:
            # The dragged item leaves its place, and the rest close up around the gap.
            playmat = (without_slot(playmat, drag.phrase, drag.item) if isinstance(drag.item, Slot)
                       else without(playmat, drag.item.id))
        placed = []
        x, y = bar[0] + m.padding, bar[1] + m.padding
        for word in playmat:
            rect, word_boxes, children = self.word(word, x, y, state.grid)
            boxes += word_boxes
            anchors[WordTarget(word.id)] = rect
            for box in word_boxes:
                if (isinstance(box.target, SlotTarget)
                        or isinstance(box.target, WordTarget) and box.target.id != word.id):
                    anchors[box.target] = box.rect
            placed.append(_Placed(word, rect, children))
            x += rect[2] + m.gap
        talk_w, button_h = self.chip_size(self.TALK)
        close_w, _ = self.chip_size(self.CLOSE)
        button_y = bar[1] + (bar_h - button_h) // 2
        talk = (bar[0] + bar[2] - m.padding - talk_w, button_y, talk_w, button_h)
        close = (talk[0] - m.gap - close_w, button_y, close_w, button_h)
        boxes.append(LaidBox(close, 'close', self.CLOSE, ButtonTarget('close')))
        boxes.append(LaidBox(talk, 'talk', self.TALK, ButtonTarget('talk')))

        # Inflection grid for the selected word, above the playmat.
        selected = find(state.playmat, state.grid) if state.grid is not None else None
        if selected is not None:
            lexeme = self.lexicon.lexemes[selected.lexeme]
            options = self.options(state.seed, lexeme)
            texts = ([' '.join(self.phrase_texts(selected, option)) for option in options]
                     if lexeme.is_noun_phrase else options)
            cell_w = max(self.chip_size(text)[0] for text in texts)
            inner_w = bar[2] - 2 * m.padding - m.gap - m.scrollbar
            columns = max(1, (inner_w + m.gap) // (cell_w + m.gap))
            rows = ceil(len(texts) / columns)
            visible_rows = min(rows, m.grid_rows)
            limits['grid'] = rows - visible_rows
            # A grid that was just opened scrolls to show the selected inflection.
            wanted = (options.index(selected.inflection) // columns - (visible_rows - 1) // 2
                      if state.grid_scroll is None else state.grid_scroll)
            first_row = scroll['grid'] = max(0, min(wanted, limits['grid']))
            grid_h = 2 * m.padding + visible_rows * row_h - m.gap
            grid = (left, bar[1] - m.margin // 2 - grid_h, bar[2], grid_h)
            boxes.append(LaidBox(grid, 'panel', target=PanelTarget('grid')))
            for index in range(first_row * columns, min(len(texts), (first_row + visible_rows) * columns)):
                row, column = divmod(index - first_row * columns, columns)
                rect = (grid[0] + m.padding + column * (cell_w + m.gap),
                        grid[1] + m.padding + row * row_h, cell_w, chip_h)
                style = 'cell-selected' if options[index] == selected.inflection else 'cell'
                boxes.append(LaidBox(rect, style, texts[index], CellTarget(selected.id, options[index])))
            boxes += self.scrollbar(grid, first_row, visible_rows, rows)

        if state.message:
            w, h = self.chip_size(state.message)
            boxes.append(LaidBox((left, m.margin, w, h), 'message', state.message))

        # Where a drag would land, its caret, and the dragged item itself.
        drop = None
        if drag is not None:
            pointer = drag.pointer
            def phrase_drop(item):
                index = sum(1 for r in item.children if r[0] + r[2] / 2 < pointer.x)
                boxes.append(self.caret(item.children, index, item.rect, m.gap // 2))
                return PhraseDrop(item.word.id, index)
            if isinstance(drag.item, Slot):
                # Articles and adpositions stay in their own phrase.
                drop = next((phrase_drop(item) for item in placed
                             if item.word.id == drag.phrase and contains(item.rect, pointer, m.gap)), None)
            elif self.lexicon.lexemes[drag.item.lexeme].part == 'adjective':
                drop = next((phrase_drop(item) for item in placed
                             if self.lexicon.lexemes[item.word.lexeme].part == 'noun'
                             and contains(item.rect, pointer, m.gap)), None)
            elif contains(bar, pointer):
                index = sum(1 for item in placed if item.rect[0] + item.rect[2] / 2 < pointer.x)
                drop = PlaymatDrop(index)
                rects = [item.rect for item in placed]
                boxes.append(self.caret(rects, index, (bar[0] + m.padding, y, 0, phrase_h), m.gap))
            if (drop is None and drag.from_playmat and not isinstance(drag.item, Slot)
                    and contains(inventory, pointer)):
                drop = RemoveDrop()
                label_w, label_h = self.chip_size('remove')
                boxes += [LaidBox(inventory, 'remove'),
                          LaidBox((inventory[0] + (inventory[2] - label_w) // 2,
                                   inventory[1] + inventory[3] - m.padding - label_h, label_w, label_h),
                                  'remove', 'remove')]
            origin = pointer - drag.grab
            if isinstance(drag.item, Slot):
                phrase = find(state.playmat, drag.phrase)
                text = slot_texts(self.lexicon.lexemes[phrase.lexeme].inflection(phrase.inflection))[drag.item]
                boxes.append(LaidBox((round(origin.x), round(origin.y), *self.chip_size(text)),
                                     'chip-dragged', text))
            else:
                if not self.lexicon.lexemes[drag.item.lexeme].is_noun_phrase:
                    origin.y -= m.phrase_padding  # `word()` insets single chips by this much
                _, ghost, _ = self.word(drag.item, round(origin.x), round(origin.y), None,
                                        interactive=False, suffix='-dragged')
                boxes += ghost
        return Layout(tuple(boxes), anchors, drop, limits, scroll)

    def caret(self, rects, index, container: Rect, gap: int) -> LaidBox:
        """A thin bar in the gap before `rects[index]`, or after the last rect."""
        if not rects:
            x = container[0]
        elif index < len(rects):
            x = rects[index][0] - gap // 2
        else:
            x = rects[-1][0] + rects[-1][2] + gap // 2
        # Taller than the chips, so it shows above and below a dragged chip.
        reach = self.metrics.phrase_padding * 2
        return LaidBox((x - 2, container[1] - reach, 4, container[3] + 2 * reach), 'caret')
