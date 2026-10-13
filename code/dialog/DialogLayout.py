"""Pure geometry for the dialog: where every box goes, and what the pointer is over.

`DialogUpdater` hit-tests against the same layout that `DialogView` draws, so the
GUI keeps no positions of its own between frames. Boxes carry style names, not
colors; `DialogView` maps names to appearances. The statement's phrases are laid
out left to right on the playmat, and a noun phrase's words within its frame, both
in the order of their `Rule`'s content.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from math import ceil

from pyglm import glm

Rect = tuple[int, int, int, int]  # left, top, width, height in viewport pixels

# The parts of speech the player may add to each part of speech. Everything else in a
# `Rule` came with its inflection, and moves only within the phrase it came with.
ACCEPTS = {'clause': {'np', 'vp'}, 'np': {'adj'}}


def tag(node):
    """The part of speech of a `Rule`, or None for a word."""
    return getattr(node, 'tag', None)


def added(parent, node) -> bool:
    """Whether the player adds `node` to `parent`, rather than it coming with `parent`'s inflection."""
    return parent is not None and tag(node) in ACCEPTS.get(parent.tag, ())


# What a press refers to.
@dataclass(frozen=True)
class InventoryTarget:
    lexeme: str

@dataclass(frozen=True)
class WordTarget:
    address: tuple   # a placed phrase, or a word in a noun phrase; pressing a noun refers to its phrase

@dataclass(frozen=True)
class CellTarget:
    index: int       # of the inflection, among the open grid's options

@dataclass(frozen=True)
class ButtonTarget:
    name: str        # 'talk' or 'close'

@dataclass(frozen=True)
class PanelTarget:
    name: str        # 'inventory', 'grid', or 'playmat'


# Where a drag would land.
@dataclass(frozen=True)
class PlaceDrop:
    parent: tuple    # address of the `Rule` it goes in, in the statement without the dragged node
    index: int       # in that `Rule`'s content

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
    address: tuple
    node: object
    rect: Rect
    children: list  # (content index, rect) of each word shown, for noun phrases


class DialogLayout:
    TALK = 'talk (E)'
    CLOSE = 'X'

    def __init__(self, inventory, metrics: DialogMetrics, *, addresses, text):
        """`inventory` is lexeme → the `Rule` trees its entry shows, in order; several are a
        sample of the lexeme's inflections, as in "I, you, he…". `text(node)` is what a `Rule`
        tree, or a word in one, reads as."""
        self.metrics = metrics
        self.addresses = addresses      # see RuleAddresses.py
        self.text = text
        self.inventory = {lexeme: ', '.join(text(rule) for rule in rules) + '…' * (len(rules) > 1)
                          for lexeme, rules in inventory.items()}

    def chip_size(self, text: str) -> tuple[int, int]:
        m = self.metrics
        return (m.text.width(text, m.font_size) + 2 * m.chip_padding[0],
                m.text.height(m.font_size) + 2 * m.chip_padding[1])

    @property
    def chip_height(self) -> int:
        return self.chip_size('')[1]

    def word(self, node, address, x: int, y: int, grid, interactive=True, suffix=''):
        """Lay out `node`, at this address, with its top-left at (x, y): (rect, boxes, children).

        A noun phrase is a frame around a chip per word it shows; anything else is one chip.
        `grid` is the open `Grid`, if any, whose node is drawn selected.
        """
        m = self.metrics
        selected = '-selected' if grid is not None and grid.address == address else ''
        target = WordTarget(address) if interactive else None
        if tag(node) != 'np':
            text = self.text(node)
            w, h = self.chip_size(text)
            rect = (x, y + m.phrase_padding, w, h)
            return rect, [LaidBox(rect, 'chip' + (suffix or selected), text, target)], []
        boxes, children = [], []
        cx = x + m.phrase_padding
        for index, child in enumerate(node.content):
            text = self.text(child)
            if not text:
                continue  # a linguistic zero, such as English's adposition for a subject
            child_address = address + (index,)
            w, h = self.chip_size(text)
            rect = (cx, y + m.phrase_padding, w, h)
            if added(node, child):
                chosen = not suffix and grid is not None and grid.address == child_address
                style, child_target = 'chip-selected' if chosen else 'chip', WordTarget(child_address)
            else:
                # The noun stands for its phrase: pressing it moves or opens the phrase.
                style = 'token'
                child_target = target if tag(child) == 'n' else WordTarget(child_address)
            boxes.append(LaidBox(rect, style, text, child_target if interactive else None))
            children.append((index, rect))
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

        # Playmat: placed phrases left to right, then the close and talk buttons.
        left = inventory[0] + inventory_w + m.margin
        phrase_h = chip_h + 2 * m.phrase_padding
        bar_h = phrase_h + 2 * m.padding
        bar = (left, vh - m.margin - bar_h, vw - left - m.margin, bar_h)
        boxes.append(LaidBox(bar, 'panel', target=PanelTarget('playmat')))
        drag, statement = state.drag, state.statement
        if drag is not None and drag.address is not None:
            # The dragged node leaves its place, and the rest close up around the gap.
            # Drops are addressed in this statement, which is the one they are made in.
            statement = self.addresses.remove(statement, drag.address)
        placed = []
        x, y = bar[0] + m.padding, bar[1] + m.padding
        for index, node in enumerate(statement.content):
            address = (index,)
            rect, word_boxes, children = self.word(node, address, x, y, state.grid)
            boxes += word_boxes
            for box in word_boxes:
                if box.target is not None:
                    anchors.setdefault(box.target, rect if box.target == WordTarget(address) else box.rect)
            placed.append(_Placed(address, node, rect, children))
            x += rect[2] + m.gap
        talk_w, button_h = self.chip_size(self.TALK)
        close_w, _ = self.chip_size(self.CLOSE)
        button_y = bar[1] + (bar_h - button_h) // 2
        talk = (bar[0] + bar[2] - m.padding - talk_w, button_y, talk_w, button_h)
        close = (talk[0] - m.gap - close_w, button_y, close_w, button_h)
        boxes.append(LaidBox(close, 'close', self.CLOSE, ButtonTarget('close')))
        boxes.append(LaidBox(talk, 'talk', self.TALK, ButtonTarget('talk')))

        # Inflection grid for the selected phrase or adjective, above the playmat.
        if state.grid is not None:
            texts = [self.text(option) for option in state.grid.options]
            # A phrase the player added to reads as none of the options, so none is selected.
            current = self.text(self.addresses.resolve(state.statement, state.grid.address))
            chosen = texts.index(current) if current in texts else None
            cell_w = max(self.chip_size(text)[0] for text in texts)
            inner_w = bar[2] - 2 * m.padding - m.gap - m.scrollbar
            columns = max(1, (inner_w + m.gap) // (cell_w + m.gap))
            rows = ceil(len(texts) / columns)
            visible_rows = min(rows, m.grid_rows)
            limits['grid'] = rows - visible_rows
            # A grid that was just opened scrolls to show the selected inflection.
            wanted = (state.grid_scroll if state.grid_scroll is not None
                      else 0 if chosen is None else chosen // columns - (visible_rows - 1) // 2)
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

        # Where a drag would land, its caret, and the dragged node itself.
        drop = None
        if drag is not None:
            pointer, node = drag.pointer, drag.node
            # A node that came with its phrase's inflection moves only within that phrase.
            home = None if drag.address is None else drag.address[:-1]
            source = None if drag.address is None else self.addresses.resolve(state.statement, home)
            def allowed(parent, address):
                return added(parent, node) or address == home
            def place(parent, children, container, gap):
                rects = [rect for _, rect in children]
                position = sum(1 for r in rects if r[0] + r[2] / 2 < pointer.x)
                boxes.append(self.caret(rects, position, container, gap))
                index = children[position][0] if position < len(children) else len(parent.content)
                return index
            for item in placed:
                if allowed(item.node, item.address) and contains(item.rect, pointer, m.gap):
                    drop = PlaceDrop(item.address, place(item.node, item.children, item.rect, m.gap // 2))
                    break
            if drop is None and allowed(statement, ()) and contains(bar, pointer):
                children = [(index, item.rect) for index, item in enumerate(placed)]
                drop = PlaceDrop((), place(statement, children, (bar[0] + m.padding, y, 0, phrase_h), m.gap))
            if (drop is None and drag.address is not None and added(source, node)
                    and contains(inventory, pointer)):
                drop = RemoveDrop()
                label_w, label_h = self.chip_size('remove')
                boxes += [LaidBox(inventory, 'remove'),
                          LaidBox((inventory[0] + (inventory[2] - label_w) // 2,
                                   inventory[1] + inventory[3] - m.padding - label_h, label_w, label_h),
                                  'remove', 'remove')]
            origin = pointer - drag.grab
            if tag(node) != 'np':
                origin.y -= m.phrase_padding  # `word()` insets single chips by this much
            _, ghost, _ = self.word(node, (), round(origin.x), round(origin.y), None,
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
