"""Text extents for layout, independent of any font library.

Layout needs only `width(text, size)` and `height(size)`. Any object with those
methods will do: `adapter.PygameFonts` measures real fonts; this class needs
none, which keeps layout tests free of Pygame.
"""


class MonospaceTextMetrics:
    def __init__(self, advance=0.6, line_height=1.2):
        self.advance = advance          # em per character
        self.line_height = line_height  # em per line

    def width(self, text: str, size: int) -> int:
        return round(len(text) * self.advance * size)

    def height(self, size: int) -> int:
        return round(self.line_height * size)
