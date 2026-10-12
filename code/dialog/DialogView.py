"""Pure layout and presentation: the same geometry drives drawing and hit tests."""
from dataclasses import dataclass
from .DialogState import DialogTarget, select_form


@dataclass(frozen=True)
class Rect:
    x: int
    y: int
    w: int
    h: int

    def contains(self, p):
        return p is not None and self.x <= p[0] < self.x + self.w and self.y <= p[1] < self.y + self.h

    @property
    def center(self):
        return (self.x + self.w / 2, self.y + self.h / 2)


@dataclass(frozen=True)
class Element:
    rect: Rect
    text: str = ''
    style: str = 'chip'
    target: DialogTarget | None = None
    clip: Rect | None = None
    size: int = 20


@dataclass(frozen=True)
class DialogScene:
    elements: tuple
    inventory: Rect
    grid: Rect
    mat: Rect
    nodes: tuple
    pieces: tuple
    inventory_max: int
    grid_max: int
    mat_max: int

    def hit(self, position):
        return next((e.target for e in reversed(self.elements)
                     if e.target and e.rect.contains(position)
                     and (e.clip is None or e.clip.contains(position))), None)

    @staticmethod
    def insertion(rects, position):
        for i, r in enumerate(rects):
            if position[1] < r.y or position[1] < r.y + r.h and position[0] < r.center[0]:
                return i
        return len(rects)


class DialogView:
    def __init__(self, language):
        self.language = language

    @staticmethod
    def width(text):
        return max(52, len(text) * 12 + 24)

    def layout(self, state):
        width, height = state.viewport
        left, right = 242, width - 286
        inventory = Rect(28, 147, 198, height - 185)
        grid = Rect(left + 34, height - 384, right - 28, 162)
        mat = Rect(left + 22, height - 186, right - 4, 102)
        elements, nodes, pieces = [], [], []
        def add(rect, text='', style='chip', target=None, clip=None, size=20):
            elements.append(Element(rect, text, style, target, clip, size))
        add(Rect(0, 0, width, height), style='background')
        add(Rect(26, 18, width - 52, 34), 'Babbling Brook', 'title', size=27)
        add(Rect(28, 56, width - 56, 24), 'DIALOG  /  ENGLISH', 'subtitle', size=14)
        add(Rect(16, 99, 224, height - 118), style='panel')
        add(Rect(28, 111, 198, 24), 'Words', 'label', size=16)
        add(Rect(left + 14, 99, right + 12, height - 528), style='panel')
        add(Rect(left + 30, 112, right - 20, 24), 'Conversation', 'label', size=16)
        convo = Rect(left + 30, 148, right - 20, max(10, height - 592))
        if not state.turns:
            lines = ['Choose your words.', 'Drag them below, then talk.']
        else:
            lines = []
            for turn in state.turns[-3:]:
                lines += ['> ' + turn.text, turn.reply]
        # Target-language utterances wrap; the renderer sees only display text.
        wrapped = []
        limit = max(20, (convo.w - 16) // 12)
        for line in lines:
            import textwrap
            wrapped.extend(textwrap.wrap(line, limit) or [''])
        count = max(1, convo.h // 31)
        for i, line in enumerate(wrapped[-count:]):
            add(Rect(convo.x, convo.y + i * 31, convo.w, 28), line, 'prose', clip=convo)

        inv_max = max(0, len(self.language.inventory) * 51 - inventory.h)
        scroll = min(state.inventory_scroll, inv_max)
        for i, key in enumerate(self.language.inventory):
            entry = self.language.lexemes[key]
            add(Rect(inventory.x, inventory.y + i * 51 - scroll, inventory.w - 10, 41), entry.label,
                'inventory', DialogTarget('inventory', key=key), inventory)
        self._scrollbar(elements, inventory, scroll, inv_max)

        add(Rect(left + 14, height - 426, right + 12, 218), style='panel')
        selected = state.find(state.selected)
        add(Rect(left + 30, height - 414, right - 80, 26),
            selected.surface if selected and state.grid_open else 'Click a word to choose its form.', 'label', size=16)
        grid_max = 0
        if state.grid_open and selected:
            add(Rect(width - 70, height - 415, 34, 28), 'x', 'close', DialogTarget('close'), size=18)
            options = state.options(self.language)
            labels = {text: select_form(self.language, selected, text).surface for text in options}
            cell_w = min(grid.w - 12, max(152, max(self.width(v) for v in labels.values())))
            cols = max(1, (grid.w - 12) // (cell_w + 12))
            grid_max = max(0, ((len(options) + cols - 1) // cols) * 48 - grid.h)
            scroll = min(state.grid_scroll, grid_max)
            for i, text in enumerate(options):
                add(Rect(grid.x + i % cols * (cell_w + 12), grid.y + i // cols * 48 - scroll, cell_w, 38),
                    labels[text], 'selected' if text == selected.text else 'chip',
                    DialogTarget('option', selected.id, text), grid)
            self._scrollbar(elements, grid, scroll, grid_max)
        else:
            add(Rect(grid.x, grid.y + 44, grid.w, 36), 'Drag a word onto the playmat to begin.', 'hint', size=17)

        add(Rect(left + 14, height - 198, right + 12, 128), style='panel')
        x, y, row_height = mat.x + 8, 0, 0
        placements = []
        for word in state.words:
            word_width = (sum(self.width(p.word.surface if p.word else p.text) + 7 for p in word.pieces) + 13
                          if word.pieces else self.width(word.text))
            word_width = min(mat.w - 24, word_width)
            inner, px, py = [], 8, 28
            for piece in word.pieces:
                text = piece.word.surface if piece.word else piece.text
                pw = self.width(text)
                if px + pw > word_width - 6 and px > 8:
                    px, py = 8, py + 47
                inner.append((piece, px, py, pw))
                px += pw + 7
            word_height = py + 50 if word.pieces else 78
            if x + word_width > mat.x + mat.w - 10 and x > mat.x + 8:
                x, y, row_height = mat.x + 8, y + row_height + 10, 0
            row_height = max(row_height, word_height)
            placements.append((word, x, y, word_width, word_height, inner))
            x += word_width + 14
        mat_max = max(0, y + row_height + 8 - mat.h) if placements else 0
        scroll = min(state.mat_scroll, mat_max)
        for word, x, y, word_width, word_height, inner in placements:
            box = Rect(x, mat.y + y - scroll, word_width, word_height)
            nodes.append((word.id, box))
            if word.pieces:
                add(box, style='phrase-selected' if state.selected == word.id else 'phrase',
                    target=DialogTarget('word', word.id), clip=mat)
                add(Rect(x + 8, box.y + 2, 50, 19), '...', 'grip', clip=mat, size=15)
                for piece, px, py, pw in inner:
                    text = piece.word.surface if piece.word else piece.text
                    rect = Rect(x + px, box.y + py, pw, 39)
                    add(rect, text, 'selected' if piece.word and state.selected == piece.word.id else 'chip',
                        DialogTarget('part', word.id, piece.key), mat)
                    pieces.append((word.id, piece.key, rect))
                labels = [p.word.surface if p.word else p.text for p in word.pieces]
                local = [r for owner, key, r in pieces if owner == word.id]
                for start, stop, text in self.language.contractions(labels):
                    a, b = local[start], local[stop - 1]
                    add(Rect(a.x, box.y + 1, b.x + b.w - a.x, 24), text, 'overlay', clip=mat, size=16)
            else:
                rect = Rect(x, box.y + 28, word_width, 39)
                add(rect, word.text, 'selected' if state.selected == word.id else 'chip',
                    DialogTarget('word', word.id), mat)
        self._scrollbar(elements, mat, scroll, mat_max)
        if not state.words:
            add(Rect(mat.x + 10, mat.y + 32, mat.w - 20, 30), 'Drop words here', 'hint', size=18)
        add(Rect(left + 18, height - 55, 98, 36), 'Clear', 'close', DialogTarget('clear'), size=17)
        add(Rect(width - 189, height - 55, 159, 36), 'Talk  [Enter]', 'talk', DialogTarget('talk'), size=17)
        add(Rect(left + 130, height - 51, right - 325, 26), 'Esc: close   |   Delete: remove', 'hint', size=13)
        if state.drag and state.drag.moving:
            source = state.drag.source
            word = state.find(source.word)
            if source.kind == 'inventory':
                text = self.language.lexemes[source.key].label
            elif source.kind == 'part' and word:
                p = next(p for p in word.pieces if p.key == source.key)
                text = p.word.surface if p.word else p.text
            else:
                text = word.surface if word else ''
            px, py = state.drag.position
            add(Rect(int(px) + 14, int(py) + 15, self.width(text), 38), text, 'ghost')
        return DialogScene(tuple(elements), inventory, grid, mat, tuple(nodes), tuple(pieces), inv_max, grid_max, mat_max)

    @staticmethod
    def _scrollbar(elements, region, scroll, maximum):
        if maximum:
            thumb = max(24, int(region.h * region.h / (maximum + region.h)))
            y = region.y + int((region.h - thumb) * scroll / maximum)
            elements.append(Element(Rect(region.x + region.w - 5, y, 4, thumb), style='scroll'))
