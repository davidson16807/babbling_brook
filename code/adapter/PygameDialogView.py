"""Stateful rendering boundary. Owns only fonts; never owns dialog/widget state."""
import pygame


class PygameDialogView:
    COLORS = {
        'background': ((239, 235, 226), None, (42, 57, 52)),
        'panel': ((251, 249, 244), (209, 212, 198), (42, 57, 52)),
        'inventory': ((234, 238, 226), (202, 210, 192), (44, 65, 52)),
        'chip': ((255, 254, 250), (171, 182, 164), (43, 58, 50)),
        'selected': ((226, 238, 207), (77, 118, 68), (34, 65, 36)),
        'phrase': ((231, 233, 224), (152, 171, 146), (43, 58, 50)),
        'phrase-selected': ((225, 233, 214), (77, 118, 68), (43, 58, 50)),
        'talk': ((62, 98, 76), None, (255, 255, 244)),
        'close': ((239, 224, 212), (210, 188, 170), (105, 64, 45)),
        'ghost': ((251, 228, 174), (122, 96, 47), (58, 51, 36)),
        'scroll': ((138, 157, 132), None, (43, 58, 50)),
        'overlay': (None, None, (100, 66, 137)),
    }

    def __init__(self):
        self.fonts = {}

    def draw(self, surface, scene):
        for element in scene.elements:
            r = element.rect
            rect = pygame.Rect(r.x, r.y, r.w, r.h)
            old_clip = surface.get_clip()
            if element.clip:
                c = element.clip
                surface.set_clip(pygame.Rect(c.x, c.y, c.w, c.h))
            fill, border, ink = self.COLORS.get(element.style, (None, None, (52, 72, 61)))
            if element.style == 'hint':
                ink = (123, 133, 117)
            if fill:
                pygame.draw.rect(surface, fill, rect, border_radius=6 if element.style != 'background' else 0)
            if border:
                pygame.draw.rect(surface, border, rect, 2 if element.style in ('selected', 'phrase-selected') else 1, border_radius=6)
            if element.text:
                font = self.fonts.get(element.size)
                if font is None:
                    font = self.fonts[element.size] = pygame.font.SysFont('DejaVu Sans Mono', element.size)
                text = font.render(element.text, True, ink)
                # Text is clipped to its own element as well as its parent panel.
                surface.set_clip(old_clip.clip(rect) if element.clip is None else surface.get_clip().clip(rect))
                pad = 10 if element.style in self.COLORS and element.style not in ('overlay',) else 0
                surface.blit(text, (rect.x + pad, rect.y + (rect.h - text.get_height()) // 2))
            surface.set_clip(old_clip)

    def release(self):
        self.fonts.clear()
