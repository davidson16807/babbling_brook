"""Pure geometry for the dialog: where every box goes, and what lies under a point.

A `Layout` plays the part a DOM plays for xcraft's views. Its boxes carry keys as xcraft's
elements carry data attributes: a `SourceKey` is a draggable placed constituent or child, by
address (`data-path`); an `InventoryKey`, `CellKey`, or `ButtonKey` is something else to press.
While a drag is in progress, the layout also holds a `DropRegion` for each constituent the
source may be placed in, and the inventory if it may be removed (`data-valid-drop`), so
`Layout.drop` answers what `elementFromPoint` answers in a browser. `DialogView` both draws a
layout and hit-tests it, so the dialog keeps no positions between frames. Boxes carry style
names, not colors.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from math import ceil

from pyglm import glm

from .ConstituentDragOperations import PlaceDrop, RemoveDrop
from .DialogState import Constituent
from .DragState import DragState

Rect = tuple[int, int, int, int]  # left, top, width, height in viewport pixels


@dataclass(frozen=True)
class SourceKey:
    address: tuple       # a placed constituent, or a child a phrase was generated with

@dataclass(frozen=True)
class InventoryKey:
    lexeme: str

@dataclass(frozen=True)
class CellKey:
    index: int           # of the inflection, among the open grid's options

@dataclass(frozen=True)
class ButtonKey:
    name: str            # 'talk' or 'close'

@dataclass(frozen=True)
class PanelKey:
    name: str            # 'inventory', 'grid', or 'playmat'


@dataclass(frozen=True)
class LaidBox:
    rect: Rect
    style: str
    text: str = ''
    key: object = None


@dataclass(frozen=True)
class DropRegion:
    """A constituent the dragged source may be placed in: dropping within `rect` places it
    among `children`, the rects of the constituent's children in the player's order."""
    parent: tuple
    rect: Rect
    children: tuple


def contains(rect: Rect, point, margin=0) -> bool:
    x, y, w, h = rect
    return x - margin <= point.x < x + w + margin and y - margin <= point.y < y + h + margin


@dataclass(frozen=True)
class Layout:
    boxes: tuple[LaidBox, ...]                                  # in draw order
    anchors: dict = field(default_factory=dict)                 # key → rect of each draggable box
    regions: tuple[DropRegion, ...] = ()                        # innermost first
    removal: Rect | None = None                                 # where a drop removes the source
    limits: dict = field(default_factory=dict)                  # greatest scroll of each panel
    scroll: dict = field(default_factory=dict)                  # first visible row of each panel
    margin: int = 8                                             # around regions, for dropping

    def hit(self, point: glm.vec2):
        """The key of the topmost box under `point` that has one, else None."""
        for box in reversed(self.boxes):
            if box.key is not None and not isinstance(box.key, PanelKey) and contains(box.rect, point):
                return box.key
        return None

    def panel(self, point: glm.vec2):
        """The name of the panel under `point`, else None."""
        for box in reversed(self.boxes):
            if isinstance(box.key, PanelKey) and contains(box.rect, point):
                return box.key.name
        return None

    def drop(self, point: glm.vec2):
        """The allowed drop under `point`, else None."""
        for region in self.regions:
            if contains(region.rect, point, self.margin):
                return PlaceDrop(region.parent, sum(1 for r in region.children if r[0] + r[2] / 2 < point.x))
        if self.removal is not None and contains(self.removal, point):
            return RemoveDrop()
        return None


@dataclass(frozen=True)
class DialogMetrics:
    text: object          # with `width(text, size)` and `height(size)`, e.g. `PygameFonts`
    font_size: int = 22
    margin: int = 16      # around panels
    padding: int = 10     # inside panels
    gap: int = 8          # between chips
    chip_padding: tuple[int, int] = (8, 4)
    phrase_padding: int = 5
    scrollbar: int = 10
    grid_rows: int = 4    # visible rows before the grid scrolls
    drag_threshold: float = 4.0   # how far a press must move to lift what it pressed; less is a click


class DialogLayout:
    TALK = 'talk (E)'
    CLOSE = 'X'

    def __init__(self, inventory, metrics, addresses, address_operations, text):
        """`inventory` is lexeme → the `Rule`s its entry shows, in order; several are a sample of
        the lexeme's inflections, as in "I, you, he…". `text(rule)` reads a `Rule`."""
        self.metrics = metrics
        self.addresses = addresses
        self.address_operations = address_operations
        self.text = text
        self.inventory = {lexeme: ', '.join(text(rule) for rule in rules) + '…' * (len(rules) > 1)
                          for lexeme, rules in inventory.items()}

    def chip_size(self, text: str) -> tuple[int, int]:
        m = self.metrics
        return (m.text.width(text, m.font_size) + 2 * m.chip_padding[0],
                m.text.height(m.font_size) + 2 * m.chip_padding[1])

    def constituent(self, root, address, x, y, grid, hidden=None, interactive=True, suffix=''):
        """Lay out the constituent at this address of `root` with its top-left at (x, y), leaving out
        the child at address `hidden`: (rect, boxes, rects of its children in the player's order).
        A noun phrase is framed, with a chip per child; anything else is a single chip."""
        m = self.metrics
        constituent = self.addresses.resolve(root, address)
        key = SourceKey(address) if interactive else None
        selected = '-selected' if grid is not None and grid.address == address and not suffix else ''
        if constituent.inflection.tag != 'np':
            text = self.text(self.addresses.rule(root, address))
            rect = (x, y + m.phrase_padding, *self.chip_size(text))
            return rect, [LaidBox(rect, 'chip' + (suffix or selected), text, key)], []
        boxes, children = [], []
        cx = x + m.phrase_padding
        for label in constituent.arrangement:
            child_address = self.addresses.child(address, label)
            if child_address == hidden:
                continue
            child = self.addresses.resolve(constituent, (label,))
            text = self.text(self.addresses.rule(root, child_address))
            rect = (cx, y + m.phrase_padding, *self.chip_size(text))
            if isinstance(child, Constituent):
                chosen = grid is not None and grid.address == child_address and not suffix
                style, child_key = ('chip-selected' if chosen else 'chip'), SourceKey(child_address)
            else:
                # The noun stands for its phrase: pressing it presses the phrase.
                style, child_key = 'token', key if label[0] == 'n' else SourceKey(child_address)
            boxes.append(LaidBox(rect, style, text, child_key if interactive else None))
            children.append(rect)
            cx += rect[2] + m.gap // 2
        rect = (x, y, cx - m.gap // 2 + m.phrase_padding - x, self.chip_size('')[1] + 2 * m.phrase_padding)
        return rect, [LaidBox(rect, 'phrase' + (suffix or selected), '', key), *boxes], children

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

    def caret(self, rects, index, container: Rect, gap: int) -> LaidBox:
        """A thin bar in the gap before `rects[index]`, or after the last rect, taller than the chips."""
        if not rects:
            x = container[0]
        elif index < len(rects):
            x = rects[index][0] - gap // 2
        else:
            x = rects[-1][0] + rects[-1][2] + gap // 2
        reach = self.metrics.phrase_padding * 2
        return LaidBox((x - 2, container[1] - reach, 4, container[3] + 2 * reach), 'caret')

    def layout(self, state) -> Layout:
        m = self.metrics
        vw, vh = state.viewport
        boxes, anchors, limits, scroll = [], {}, {}, {}
        chip_h = self.chip_size('')[1]
        row_h = chip_h + m.gap
        drag = state.drag_state if state.drag_type.id == DragState.constituent else None
        if drag is not None and glm.distance(drag.current, drag.start) < m.drag_threshold:
            drag = None  # not lifted yet: a press that may still be a click
        hidden = drag.source if drag is not None and isinstance(drag.source, tuple) else None

        # Inventory: every lexeme, in the order given.
        inventory_w = (max((self.chip_size(label)[0] for label in self.inventory.values()), default=0)
                       + 2 * m.padding + m.gap + m.scrollbar)
        inventory = (m.margin, m.margin, inventory_w, vh - 2 * m.margin)
        boxes.append(LaidBox(inventory, 'panel', key=PanelKey('inventory')))
        visible = max(1, (inventory[3] - 2 * m.padding + m.gap) // row_h)
        limits['inventory'] = max(0, len(self.inventory) - visible)
        first = scroll['inventory'] = max(0, min(state.inventory_scroll, limits['inventory']))
        for row, (lexeme, label) in enumerate(list(self.inventory.items())[first:first + visible]):
            rect = (inventory[0] + m.padding, inventory[1] + m.padding + row * row_h, *self.chip_size(label))
            boxes.append(LaidBox(rect, 'chip', label, InventoryKey(lexeme)))
            anchors[InventoryKey(lexeme)] = rect
        boxes += self.scrollbar(inventory, first, visible, len(self.inventory))

        # Playmat: the statement's phrases left to right, then the close and talk buttons.
        left = inventory[0] + inventory_w + m.margin
        phrase_h = chip_h + 2 * m.phrase_padding
        bar_h = phrase_h + 2 * m.padding
        bar = (left, vh - m.margin - bar_h, vw - left - m.margin, bar_h)
        boxes.append(LaidBox(bar, 'panel', key=PanelKey('playmat')))
        statement, root = state.statement, self.addresses.ROOT
        placed = {}  # address → (rect, child rects)
        x, y = bar[0] + m.padding, bar[1] + m.padding
        for label in statement.arrangement:
            address = self.addresses.child(root, label)
            if address == hidden:
                continue
            rect, word_boxes, children = self.constituent(statement, address, x, y, state.grid, hidden)
            boxes += word_boxes
            for box in word_boxes:
                if isinstance(box.key, SourceKey):
                    anchors.setdefault(box.key, rect if box.key.address == address else box.rect)
            placed[address] = (rect, children)
            x += rect[2] + m.gap
        talk_w, button_h = self.chip_size(self.TALK)
        close_w, _ = self.chip_size(self.CLOSE)
        button_y = bar[1] + (bar_h - button_h) // 2
        talk = (bar[0] + bar[2] - m.padding - talk_w, button_y, talk_w, button_h)
        close = (talk[0] - m.gap - close_w, button_y, close_w, button_h)
        boxes.append(LaidBox(close, 'close', self.CLOSE, ButtonKey('close')))
        boxes.append(LaidBox(talk, 'talk', self.TALK, ButtonKey('talk')))

        # Inflection grid of the selected constituent, above the playmat.
        if state.grid is not None:
            selected, options = self.addresses.resolve(statement, state.grid.address), state.grid.options
            # Each cell reads as the constituent would with that inflection, added children and all.
            texts = [self.text(self.addresses.rule(self.address_operations.reinflect(selected, root, option)))
                     for option in options]
            chosen = [self.text(option) for option in options].index(self.text(selected.inflection))
            cell_w = max(self.chip_size(text)[0] for text in texts)
            inner_w = bar[2] - 2 * m.padding - m.gap - m.scrollbar
            columns = max(1, (inner_w + m.gap) // (cell_w + m.gap))
            rows = ceil(len(texts) / columns)
            visible_rows = min(rows, m.grid_rows)
            limits['grid'] = rows - visible_rows
            # A grid that was just opened scrolls to show the selected inflection.
            wanted = chosen // columns - (visible_rows - 1) // 2 if state.grid_scroll is None else state.grid_scroll
            first_row = scroll['grid'] = max(0, min(wanted, limits['grid']))
            grid_h = 2 * m.padding + visible_rows * row_h - m.gap
            grid = (left, bar[1] - m.margin // 2 - grid_h, bar[2], grid_h)
            boxes.append(LaidBox(grid, 'panel', key=PanelKey('grid')))
            for index in range(first_row * columns, min(len(texts), (first_row + visible_rows) * columns)):
                row, column = divmod(index - first_row * columns, columns)
                rect = (grid[0] + m.padding + column * (cell_w + m.gap), grid[1] + m.padding + row * row_h,
                        cell_w, chip_h)
                boxes.append(LaidBox(rect, 'cell-selected' if index == chosen else 'cell', texts[index],
                                     CellKey(index)))
            boxes += self.scrollbar(grid, first_row, visible_rows, rows)

        if state.message:
            w, h = self.chip_size(state.message)
            boxes.append(LaidBox((left, m.margin, w, h), 'message', state.message))

        # While dragging: where the source may go, the caret at the drop under the pointer, and the source.
        regions, removal = [], None
        if drag is not None:
            for address in drag.candidates:
                if address == root:
                    continue
                if address in placed:
                    regions.append(DropRegion(address, *placed[address]))
            if root in drag.candidates:
                regions.append(DropRegion(root, bar, tuple(rect for rect, _ in placed.values())))
            if drag.removable:
                removal = inventory
            region = next((region for region in regions
                           if isinstance(drag.target, PlaceDrop) and region.parent == drag.target.parent), None)
            if region is not None:
                if region.parent == root:
                    boxes.append(self.caret(region.children, drag.target.index,
                                            (bar[0] + m.padding, y, 0, phrase_h), m.gap))
                else:
                    boxes.append(self.caret(region.children, drag.target.index, region.rect, m.gap // 2))
            elif isinstance(drag.target, RemoveDrop):
                label_w, label_h = self.chip_size('remove')
                boxes += [LaidBox(inventory, 'remove'),
                          LaidBox((inventory[0] + (inventory[2] - label_w) // 2,
                                   inventory[1] + inventory[3] - m.padding - label_h, label_w, label_h),
                                  'remove', 'remove')]
            origin = drag.current - drag.grab
            if hidden is not None and not isinstance(self.addresses.resolve(statement, hidden), Constituent):
                text = self.text(self.addresses.resolve(statement, hidden))
                boxes.append(LaidBox((round(origin.x), round(origin.y), *self.chip_size(text)), 'chip-dragged', text))
            else:
                ghost_root, ghost_address = ((statement, hidden) if hidden is not None
                                             else (self.address_operations.constituent(drag.source), root))
                if self.addresses.resolve(ghost_root, ghost_address).inflection.tag != 'np':
                    origin.y -= m.phrase_padding  # `constituent()` insets single chips by this much
                _, ghost, _ = self.constituent(ghost_root, ghost_address, round(origin.x), round(origin.y), None,
                                               interactive=False, suffix='-dragged')
                boxes += ghost
        return Layout(tuple(boxes), anchors, tuple(regions), removal, limits, scroll, m.gap)
