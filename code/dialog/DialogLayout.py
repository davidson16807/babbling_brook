"""Pure geometry for the dialog: where every box goes, and what the pointer is over.

`DialogUpdater` hit-tests against the same layout that `DialogView` draws, so the
GUI keeps no positions of its own between frames. Boxes carry style names, not
colors; `DialogView` maps names to appearances. The statement's phrases are laid
out left to right on the playmat, and a noun phrase's children within its frame.
Which drops are allowed is `DialogDragOperations`' to say; the layout only maps the
pointer to one of them.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from math import ceil

from pyglm import glm

from .DialogDragOperations import PlaceDrop, RemoveDrop
from .DialogState import Constituent

Rect = tuple[int, int, int, int]  # left, top, width, height in viewport pixels


# What a press refers to.
@dataclass(frozen=True)
class InventoryTarget:
    lexeme: str

@dataclass(frozen=True)
class ConstituentTarget:
    address: tuple   # a placed constituent, or a child a noun phrase was generated with;
                     # pressing a phrase's noun refers to the phrase

@dataclass(frozen=True)
class CellTarget:
    index: int       # of the inflection, among the open grid's options

@dataclass(frozen=True)
class ButtonTarget:
    name: str        # 'talk' or 'close'

@dataclass(frozen=True)
class PanelTarget:
    name: str        # 'inventory', 'grid', or 'playmat'


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
    address: tuple
    constituent: Constituent
    rect: Rect
    children: list  # display-sequence rects, for noun phrases


class DialogLayout:
    TALK = 'talk (E)'
    CLOSE = 'X'

    def __init__(self, inventory, metrics: DialogMetrics, *, addresses, address_operations, drag_operations):
        self.metrics = metrics
        self.addresses = addresses                      # see ConstituentAddresses.py
        self.address_operations = address_operations    # see ConstituentAddressOperations.py
        self.drag_operations = drag_operations          # see DialogDragOperations.py
        # `inventory` is lexeme → the `Rule` trees its entry shows, in order; several are
        # a sample of the lexeme's inflections, as in "I, you, he…".
        text = address_operations.text
        self.inventory = {lexeme: ', '.join(text(rule) for rule in rules) + '…' * (len(rules) > 1)
                          for lexeme, rules in inventory.items()}

    def chip_size(self, text: str) -> tuple[int, int]:
        m = self.metrics
        return (m.text.width(text, m.font_size) + 2 * m.chip_padding[0],
                m.text.height(m.font_size) + 2 * m.chip_padding[1])

    @property
    def chip_height(self) -> int:
        return self.chip_size('')[1]

    def word(self, root, address, x: int, y: int, grid, interactive=True, suffix=''):
        """Lay out the constituent at this address of `root` with its top-left at (x, y):
        (rect, boxes, child rects).

        `grid` is the open `Grid`, if any, whose constituent is drawn selected.
        """
        m = self.metrics
        constituent = self.addresses.resolve(root, address)
        selected = '-selected' if grid is not None and grid.address == address else ''
        target = ConstituentTarget(address) if interactive else None
        if constituent.inflection.tag != 'np':
            text = self.address_operations.text(root, address)
            w, h = self.chip_size(text)
            rect = (x, y + m.phrase_padding, w, h)
            return rect, [LaidBox(rect, 'chip' + (suffix or selected), text, target)], []
        boxes, children = [], []
        cx = x + m.phrase_padding
        for label in constituent.arrangement:
            # Children are read from the constituent itself; `child_address` is where they are in `root`.
            child_address = self.addresses.child(address, label)
            text = self.address_operations.text(constituent, (label,))
            w, h = self.chip_size(text)
            rect = (cx, y + m.phrase_padding, w, h)
            if isinstance(self.addresses.resolve(constituent, (label,)), Constituent):
                chosen = grid is not None and grid.address == child_address and not suffix
                style, child_target = 'chip-selected' if chosen else 'chip', ConstituentTarget(child_address)
            else:
                # The noun stands for its phrase: pressing it moves or opens the phrase.
                style = 'token'
                child_target = target if label[0] == 'n' else ConstituentTarget(child_address)
            boxes.append(LaidBox(rect, style, text, child_target if interactive else None))
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

        # Inventory: every lexeme, in the order given.
        inventory_w = (max((self.chip_size(label)[0] for label in self.inventory.values()), default=0)
                       + 2 * m.padding + m.gap + m.scrollbar)
        inventory = (m.margin, m.margin, inventory_w, vh - 2 * m.margin)
        boxes.append(LaidBox(inventory, 'panel', target=PanelTarget('inventory')))
        visible = max(1, (inventory[3] - 2 * m.padding + m.gap) // row_h)
        limits['inventory'] = max(0, len(self.inventory) - visible)
        first = scroll['inventory'] = max(0, min(state.inventory_scroll, limits['inventory']))
        for row, (lexeme, label) in enumerate(list(self.inventory.items())[first:first + visible]):
            target = InventoryTarget(lexeme)
            rect = (inventory[0] + m.padding, inventory[1] + m.padding + row * row_h,
                    *self.chip_size(label))
            boxes.append(LaidBox(rect, 'chip', label, target))
            anchors[target] = rect
        boxes += self.scrollbar(inventory, first, visible, len(self.inventory))

        # Playmat: placed words left to right, then the close and talk buttons.
        left = inventory[0] + inventory_w + m.margin
        phrase_h = chip_h + 2 * m.phrase_padding
        bar_h = phrase_h + 2 * m.padding
        bar = (left, vh - m.margin - bar_h, vw - left - m.margin, bar_h)
        boxes.append(LaidBox(bar, 'panel', target=PanelTarget('playmat')))
        drag, statement = state.drag, state.statement
        if drag is not None and drag.address is not None:
            # The dragged item leaves its place, and the rest close up around the gap.
            statement = self.address_operations.hide(statement, drag.address)
        placed = []
        x, y = bar[0] + m.padding, bar[1] + m.padding
        for label in statement.arrangement:
            address = self.addresses.child(self.addresses.ROOT, label)
            rect, word_boxes, children = self.word(statement, address, x, y, state.grid)
            boxes += word_boxes
            anchors[ConstituentTarget(address)] = rect
            for box in word_boxes:
                if isinstance(box.target, ConstituentTarget) and box.target.address != address:
                    anchors[box.target] = box.rect
            placed.append(_Placed(address, self.addresses.resolve(statement, address), rect, children))
            x += rect[2] + m.gap
        talk_w, button_h = self.chip_size(self.TALK)
        close_w, _ = self.chip_size(self.CLOSE)
        button_y = bar[1] + (bar_h - button_h) // 2
        talk = (bar[0] + bar[2] - m.padding - talk_w, button_y, talk_w, button_h)
        close = (talk[0] - m.gap - close_w, button_y, close_w, button_h)
        boxes.append(LaidBox(close, 'close', self.CLOSE, ButtonTarget('close')))
        boxes.append(LaidBox(talk, 'talk', self.TALK, ButtonTarget('talk')))

        # Inflection grid for the selected constituent, above the playmat.
        if state.grid is not None:
            address, options = state.grid.address, state.grid.options
            # Each cell reads as the constituent would with that inflection, added children and all.
            selected = self.addresses.resolve(state.statement, address)
            reinflect, text, root = self.address_operations.reinflect, self.address_operations.text, self.addresses.ROOT
            texts = [text(reinflect(selected, root, option)) for option in options]
            cell_w = max(self.chip_size(text)[0] for text in texts)
            inner_w = bar[2] - 2 * m.padding - m.gap - m.scrollbar
            columns = max(1, (inner_w + m.gap) // (cell_w + m.gap))
            rows = ceil(len(texts) / columns)
            visible_rows = min(rows, m.grid_rows)
            limits['grid'] = rows - visible_rows
            # A grid that was just opened scrolls to show the selected inflection.
            words = self.address_operations.words
            chosen = [words(option) for option in options].index(words(selected.inflection))
            wanted = (chosen // columns - (visible_rows - 1) // 2
                      if state.grid_scroll is None else state.grid_scroll)
            first_row = scroll['grid'] = max(0, min(wanted, limits['grid']))
            grid_h = 2 * m.padding + visible_rows * row_h - m.gap
            grid = (left, bar[1] - m.margin // 2 - grid_h, bar[2], grid_h)
            boxes.append(LaidBox(grid, 'panel', target=PanelTarget('grid')))
            for index in range(first_row * columns, min(len(texts), (first_row + visible_rows) * columns)):
                row, column = divmod(index - first_row * columns, columns)
                rect = (grid[0] + m.padding + column * (cell_w + m.gap),
                        grid[1] + m.padding + row * row_h, cell_w, chip_h)
                style = 'cell-selected' if index == chosen else 'cell'
                boxes.append(LaidBox(rect, style, texts[index], CellTarget(index)))
            boxes += self.scrollbar(grid, first_row, visible_rows, rows)

        if state.message:
            w, h = self.chip_size(state.message)
            boxes.append(LaidBox((left, m.margin, w, h), 'message', state.message))

        # Where a drag would land, its caret, and the dragged item itself.
        drop = None
        if drag is not None:
            pointer = drag.pointer
            source = drag.new if drag.address is None else drag.address
            dragged = drag.new if drag.address is None else self.addresses.resolve(state.statement, drag.address)
            targets = self.drag_operations.targets(state.statement, source)
            def place(parent, rects, container, gap):
                index = sum(1 for r in rects if r[0] + r[2] / 2 < pointer.x)
                boxes.append(self.caret(rects, index, container, gap))
                return PlaceDrop(parent, index)
            drop = next((place(item.address, item.children, item.rect, m.gap // 2) for item in placed
                         if item.address in targets and contains(item.rect, pointer, m.gap)), None)
            if drop is None and self.addresses.ROOT in targets and contains(bar, pointer):
                drop = place(self.addresses.ROOT, [item.rect for item in placed],
                             (bar[0] + m.padding, y, 0, phrase_h), m.gap)
            if (drop is None and self.drag_operations.removable(state.statement, source)
                    and contains(inventory, pointer)):
                drop = RemoveDrop()
                label_w, label_h = self.chip_size('remove')
                boxes += [LaidBox(inventory, 'remove'),
                          LaidBox((inventory[0] + (inventory[2] - label_w) // 2,
                                   inventory[1] + inventory[3] - m.padding - label_h, label_w, label_h),
                                  'remove', 'remove')]
            origin = pointer - drag.grab
            if not isinstance(dragged, Constituent):
                text = self.address_operations.text(state.statement, drag.address)
                boxes.append(LaidBox((round(origin.x), round(origin.y), *self.chip_size(text)),
                                     'chip-dragged', text))
            else:
                if dragged.inflection.tag != 'np':
                    origin.y -= m.phrase_padding  # `word()` insets single chips by this much
                root, address = ((drag.new, self.addresses.ROOT) if drag.address is None
                                 else (state.statement, drag.address))
                _, ghost, _ = self.word(root, address, round(origin.x), round(origin.y), None,
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
