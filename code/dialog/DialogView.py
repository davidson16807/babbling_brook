"""Pure dialog layout shared by drawing and hit testing."""
from ..view.UiBox import UiBox, UiBoxStyle

BACKGROUND = (22, 32, 36, 255)
PANEL = (30, 44, 47, 255)
INK = (242, 235, 217)
MUTED = (172, 185, 180)
BORDER = (69, 89, 88, 255)
GOLD = (227, 187, 113, 255)


def contains(rect, point):
    x, y, w, h = rect
    return x <= point[0] < x+w and y <= point[1] < y+h


def regions(state):
    w, h = state.viewport
    left = 232
    return {'inventory': (24, 94, 192, h-120),
            'forms': (left+24, 260, w-left-48, h-494),
            'sentence': (left+24, h-212, w-left-48, 124)}


def form_columns(state):
    return max(1, (state.viewport[0]-304)//220)


def active_form(state, catalog):
    phrase = next((p for p in state.phrases if p['id'] == state.selected), None)
    if phrase is None:
        return None
    if state.selected_part is not None:
        part = phrase['parts'][state.selected_part]
        return part[2], part[1]
    return phrase['lexeme'], phrase['form']


def form_text(phrase, form, catalog):
    words = list(catalog[phrase['lexeme']]['parts'][form])
    index = next((i for i, part in enumerate(words) if part[0] == 'n'), len(words))
    words[index:index] = [(kind, word) for kind, word, _ in phrase['parts'] if kind == 'adj']
    return ' '.join(word for _, word in words)


def sentence_rows(state):
    width = regions(state)['sentence'][2]-24
    x, row, rows = 0, 0, []
    for phrase in state.phrases:
        widths = [max(40, len(part[1])*12+22) for part in phrase['parts']]
        size = sum(widths)+8*(len(widths)-1)+20
        if x+size > width and x:
            x, row = 0, row+1
        rows.append((phrase, x, row, size, widths))
        x += size+12
    return rows


def layout(state, catalog):
    w, h = state.viewport
    area = regions(state)
    items = []
    def box(rect, text='', target=None, background=PANEL, border=BORDER, size=23, color=INK):
        items.append((UiBox(tuple(map(int, rect)), UiBoxStyle(background, border, 1, color, size), text), target))
    def label(rect, text, size=21, color=MUTED):
        box(rect, text, background=BACKGROUND, border=BACKGROUND, size=size, color=color)
    box((0, 0, w, h), background=BACKGROUND, border=BACKGROUND)
    label((24, 18, 196, 42), 'Babbling Brook', 29, INK)
    label((252, 18, w-276, 42), 'DIALOG  /  English', 26, INK)
    label((24, 62, 192, 28), 'Words', 22, GOLD[:3])
    x, y, aw, ah = area['inventory']
    box((x, y, aw, ah))
    words = sorted(catalog, key=lambda key: catalog[key]['label'].casefold())
    visible = max(1, (ah-52)//44)
    start = min(state.inventory_scroll, max(0, len(words)-visible))
    for i, key in enumerate(words[start:start+visible]):
        box((x+12, y+12+i*44, aw-24, 36), catalog[key]['label'], ('inventory', key),
            background=(44, 59, 60, 255))
    box((x+12, y+ah-36, 72, 26), 'Up', ('inventory-scroll', -1), size=19)
    box((x+aw-84, y+ah-36, 72, 26), 'Down', ('inventory-scroll', 1), size=19)
    label((252, 64, w-276, 28), 'Make a sentence. Choose its forms. Put the words in order.', 21)
    box((256, 100, w-280, 128))
    if state.transcript:
        for i, (text, accepted) in enumerate(state.transcript[-2:]):
            box((270, 110+i*54, w-308, 30), text, border=PANEL, size=23)
            box((270, 140+i*54, w-308, 20), 'Understood.' if accepted else 'What?',
                border=PANEL, size=18, color=(174, 206, 165) if accepted else (230, 170, 149))
    else:
        box((276, 132, w-320, 40), 'Your conversation will appear here.', border=PANEL, color=MUTED)
    label((256, 232, w-280, 28), 'Choose a form' if state.selected is not None else 'Click a sentence word to change its form.', 21, GOLD[:3])
    x, y, aw, ah = area['forms']
    box((x, y, aw, ah))
    selected = next((p for p in state.phrases if p['id'] == state.selected), None)
    if selected:
        lexeme, current = active_form(state, catalog)
        forms = dict(state.choices)[lexeme]
        columns = form_columns(state)
        rows = max(1, (ah-52)//46)
        page_size = rows*columns
        start = min(state.form_scroll, max(0, ((len(forms)-1)//page_size)*page_size))
        cell_width = (aw-32)//columns
        for i, form in enumerate(forms[start:start+page_size]):
            box((x+12+(i%columns)*cell_width, y+12+(i//columns)*46, cell_width-8, 38),
                form_text(selected, form, catalog) if state.selected_part is None else form,
                ('form', form), border=GOLD if form == current else BORDER,
                background=(64, 70, 55, 255) if form == current else (40, 55, 57, 255))
        box((x+12, y+ah-32, 70, 24), 'Previous', ('form-scroll', -page_size), size=18)
        label((x+88, y+ah-32, aw-268, 24), f'{start+1}-{min(start+page_size, len(forms))} of {len(forms)}', 18)
        box((x+aw-164, y+ah-32, 70, 24), 'Next', ('form-scroll', page_size), size=18)
        box((x+aw-84, y+ah-32, 72, 24), 'Close', ('close',), size=18)
    else:
        box((x+16, y+20, aw-32, max(32, ah-40)), 'Drag red or small inside a noun phrase.', border=PANEL, color=MUTED)
    x, y, aw, ah = area['sentence']
    label((x, y-26, aw, 24), 'Your sentence  /  drag the frame to move a phrase; drag words to arrange them', 19, GOLD[:3])
    box((x, y, aw, ah), target=('sentence',))
    if not state.phrases:
        box((x+20, y+38, aw-40, 42), 'Drop words here', ('sentence',), border=PANEL, color=MUTED)
    # The sentence wraps into rows. The wheel scrolls when it grows beyond the tray.
    rows = sentence_rows(state)
    scroll = min(state.sentence_scroll, max(0, rows[-1][2] if rows else 0))
    for phrase, offset, row, pw, widths in rows:
        px = x+12+offset
        py = y+10+(row-scroll)*66
        if y <= py and py+58 <= y+ah:
            box((px, py, pw, 58), target=('phrase', phrase['id']),
                border=GOLD if phrase['id'] == state.selected else BORDER,
                background=(51, 64, 61, 255))
            tx = px+10
            for index, (part, cw) in enumerate(zip(phrase['parts'], widths)):
                box((tx, py+15, cw, 34), part[1], ('part', phrase['id'], index),
                    background=(70, 76, 55, 255) if part[0] == 'adj' else (38, 52, 55, 255))
                tx += cw+8
    label((256, h-78, w-540, 22), state.message, 17)
    label((256, h-52, w-540, 24), 'Enter: Speak   Esc: Close forms   Arrows: Move phrase   Delete: Remove', 17)
    box((w-264, h-66, 104, 42), 'Clear', ('clear',), size=22)
    box((w-148, h-66, 124, 42), 'Speak', ('speak',), background=(91, 114, 79, 255), border=(145, 163, 108, 255))
    if state.dragging and state.pressed:
        target = state.pressed
        if target[0] == 'inventory':
            text = catalog[target[1]]['label']
        else:
            phrase = next(p for p in state.phrases if p['id'] == target[1])
            text = phrase['parts'][target[2]][1] if target[0] == 'part' else ' '.join(p[1] for p in phrase['parts'])
        box((state.pointer[0]+12, state.pointer[1]+12, max(70, len(text)*12+24), 38), text,
            background=(79, 84, 61, 255), border=GOLD)
    return tuple(items)


def hit_test(state, catalog, point):
    return next((target for box, target in reversed(layout(state, catalog))
                 if target and contains(box.rect, point)), None)


class DialogView:
    def __init__(self, ui, catalog):
        self.ui, self.catalog = ui, catalog

    def draw(self, state):
        self.ui.draw_boxes(state.viewport, tuple(box for box, _ in layout(state, self.catalog)))

    def release(self):
        self.ui.release()
