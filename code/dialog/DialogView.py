"""Draw the dialog: map the layout's style names to appearances, then hand boxes to the UI adapter."""
from ..view.UiBox import UiBox, UiBoxStyle

PANEL = (22, 33, 37, 230)       # the explorer and editor panel colors
LINE = (147, 169, 146, 255)
DIM_LINE = (98, 120, 104, 255)
CREAM = (239, 241, 223)
AMBER = (243, 222, 166)
CHIP = (48, 66, 70, 255)
NONE = (0, 0, 0, 0)


def dialog_styles(font_size=22):
    def style(background, border, border_width=1, text_color=CREAM):
        return UiBoxStyle(background, border, border_width, text_color, font_size)
    selected = style(CHIP, (*AMBER, 255), 3, AMBER)
    return {
        'panel': style(PANEL, LINE),
        'chip': style(CHIP, LINE),
        'chip-selected': selected,
        'chip-dragged': style((*CHIP[:3], 170), (*AMBER, 255), 2),
        # Articles and adpositions that come with a noun phrase's inflection.
        'token': style((36, 52, 56, 255), DIM_LINE),
        'phrase': style(NONE, LINE),
        'phrase-selected': style(NONE, (*AMBER, 255), 3),
        'phrase-dragged': style((22, 33, 37, 150), (*AMBER, 255), 2),
        'cell': style(CHIP, LINE),
        'cell-selected': selected,
        'talk': style((78, 140, 84, 255), (190, 225, 170, 255), 1, (245, 250, 235)),
        'close': style((168, 74, 70, 255), (235, 170, 160, 255), 1, (250, 240, 235)),
        'track': style((12, 20, 23, 255), DIM_LINE),
        'thumb': style(LINE, NONE, 0),
        'caret': style((*AMBER, 255), NONE, 0),
        'remove': style((168, 74, 70, 110), (235, 170, 160, 255), 2, (250, 240, 235)),
        'message': style(PANEL, LINE, 1, AMBER),
    }


class DialogView:
    def __init__(self, layout, ui, styles):
        self.layout = layout
        self.ui = ui
        self.styles = styles

    def boxes(self, state) -> tuple[UiBox, ...]:
        return tuple(UiBox(box.rect, self.styles[box.style], box.text)
                     for box in self.layout.layout(state).boxes)

    def draw(self, state):
        self.ui.draw(state.viewport, self.boxes(state))

    def release(self):
        self.ui.release()
