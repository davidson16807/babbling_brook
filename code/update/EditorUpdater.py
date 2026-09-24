"""Pure level editing, cursor movement, and camera updates."""
from dataclasses import replace
from math import floor, pi

from ..codec.map.MapCodec import MapCodec
from ..codec.map.ObjectPlacementCodec import ObjectPlacementCodec
from ..messages import (KeyboardAction, KeyboardMessage, KeyboardModifiers, MouseButton,
                        MouseMotionMessage, QuitMessage, ScrollMessage, WindowResizeMessage)


class EditorUpdater:
    def __init__(self, movement_keys, camera_keys, mouselook):
        self.movement_keys = movement_keys
        self.camera_keys = camera_keys
        self.mouselook = mouselook

    def _rebuild(self, state, image, **changes):
        map_ = MapCodec(state.tile_palette, state.tile_archetypes).decode(image)
        return replace(state, image=image, map=map_,
                       placements=ObjectPlacementCodec(state.object_palette, map_).decode(image),
                       quit_pending=False, **changes)

    def _edit(self, state, delta, channel):
        if not delta:
            return state
        if channel != 0:
            palette = state.tile_palette if channel == 1 else state.object_palette
            definitions = state.tile_archetypes if channel == 1 else state.object_archetypes
            options = sorted({key for key, archetype in palette.items()
                              if 0 <= key <= 65535 and archetype in definitions}
                             | ({0} if channel == 2 else set()))
        pixels = list(state.image.pixels)
        maximum = state.image.maximum
        for x, y in state.cursor:
            index = y * state.image.width + x
            pixel = list(pixels[index])
            if channel == 0:
                value = max(0, min(65535, pixel[0] + delta))
            else:
                candidates = [value for value in options if (value - pixel[channel]) * delta > 0]
                if not candidates:
                    continue
                count = min(abs(delta), len(candidates))
                value = candidates[count - 1] if delta > 0 else candidates[-count]
            pixel[channel] = value
            pixels[index] = tuple(pixel)
            maximum = max(maximum, value)
        if tuple(pixels) == state.image.pixels:
            return replace(state, message='No further palette entry in that direction.') if channel else state
        image = replace(state.image, pixels=tuple(pixels), maximum=maximum)
        return self._rebuild(state, image, undo=(*state.undo[-99:], state.image), redo=(),
                             message='')

    def _move(self, state, keys, extend=False):
        axes = self.movement_keys.update(keys)
        if not (axes.x or axes.y):
            return state
        # At the initial isometric angle W follows -X and D follows +Y.
        dx, dy = -int(axes.y), int(axes.x)
        quarter = floor(state.camera.azimuth / (pi / 2)) % 4
        for _ in range(quarter):
            dx, dy = -dy, dx
        x, y = state.cursor[-1]
        coordinate = x + dx, y + dy
        if coordinate not in state.map:
            return state
        cursor = [coordinate]
        if extend and coordinate != state.cursor[0]:
            anchor = state.cursor[0]
            xmin, xmax = sorted((anchor[0], coordinate[0]))
            ymin, ymax = sorted((anchor[1], coordinate[1]))
            cursor = [anchor] + [
                (x, y) for y in range(ymin, ymax + 1) for x in range(xmin, xmax + 1)
                if (x, y) != anchor and (x, y) != coordinate
            ] + [coordinate]
        return replace(state, cursor=cursor, quit_pending=False, message='')

    def _look(self, state, axes):
        return replace(state, camera=replace(state.camera,
            azimuth=max(0, min(pi, state.camera.azimuth + axes.x)),
            elevation=max(0, min(pi / 2, state.camera.elevation + axes.y))),
            quit_pending=False)

    def step(self, state, seconds, pressed_keys):
        axes = self.movement_keys.update(pressed_keys)
        if not (axes.x or axes.y) or {'left ctrl', 'right ctrl'} & pressed_keys:
            return replace(state, cursor_delay=0.0)
        delay = state.cursor_delay - seconds
        if delay > 0:
            return replace(state, cursor_delay=delay)
        extend = bool({'shift', 'right shift'} & pressed_keys)
        return replace(self._move(state, pressed_keys, extend), cursor_delay=0.12)

    def update(self, state, message):
        if isinstance(message, QuitMessage) or (isinstance(message, KeyboardMessage)
                and message.action == KeyboardAction.PRESS and message.key == 'escape'):
            if state.dirty and not state.quit_pending:
                return replace(state, quit_pending=True,
                               message='Unsaved changes. Ctrl+S saves; Escape again discards and closes.')
            return replace(state, running=False)
        if isinstance(message, WindowResizeMessage):
            return replace(state, viewport=message.size)
        if isinstance(message, MouseMotionMessage) and MouseButton.MIDDLE in message.buttons:
            return self._look(state, self.mouselook.update(message))
        if isinstance(message, ScrollMessage):
            return self._edit(state, int(message.offset.y), 0)
        if not isinstance(message, KeyboardMessage) or message.action != KeyboardAction.PRESS:
            return state
        if message.modifiers & KeyboardModifiers.CTRL:
            if message.key == 'z' and state.undo:
                return self._rebuild(state, state.undo[-1], undo=state.undo[:-1],
                                     redo=(*state.redo, state.image), message='Undone.')
            if message.key == 'y' and state.redo:
                return self._rebuild(state, state.redo[-1], redo=state.redo[:-1],
                                     undo=(*state.undo, state.image), message='Redone.')
        if message.key in (',', '<', '.', '>'):
            return self._edit(state, -1 if message.key in (',', '<') else 1, 0)
        if message.key in ('[', ']'):
            return self._edit(state, -1 if message.key == '[' else 1, 1)
        if message.key in ('(', ')') or (message.key in ('9', '0')
                and message.modifiers & KeyboardModifiers.SHIFT):
            return self._edit(state, -1 if message.key in ('(', '9') else 1, 2)
        if not message.modifiers & KeyboardModifiers.CTRL:
            moved = self._move(state, frozenset((message.key,)),
                               bool(message.modifiers & KeyboardModifiers.SHIFT))
            if moved is not state:
                return replace(moved, cursor_delay=0.25)
        axes = self.camera_keys.update(frozenset((message.key,)))
        if axes.x or axes.y:
            return self._look(state, axes)
        return state
