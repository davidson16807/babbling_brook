"""Pure level editing, cursor movement, and camera updates."""
from dataclasses import replace
from math import pi

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

    def _edit(self, state, delta, modifiers):
        if not delta:
            return state
        x, y = state.cursor
        index = y * state.image.width + x
        pixel = list(state.image.pixels[index])
        channel = 1 if modifiers & KeyboardModifiers.CTRL else 2 if modifiers & KeyboardModifiers.SHIFT else 0
        if channel == 0:
            value = max(0, min(65535, pixel[0] + delta))
        else:
            palette = state.tile_palette if channel == 1 else state.object_palette
            definitions = state.tile_archetypes if channel == 1 else state.object_archetypes
            options = sorted({key for key, archetype in palette.items()
                              if 0 <= key <= 65535 and archetype in definitions}
                             | ({0} if channel == 2 else set()))
            candidates = [value for value in options if (value - pixel[channel]) * delta > 0]
            if not candidates:
                return replace(state, message='No further palette entry in that direction.')
            value = candidates[min(abs(delta), len(candidates)) - 1] if delta > 0 else candidates[-min(abs(delta), len(candidates))]
        if pixel[channel] == value:
            return state
        pixel[channel] = value
        pixels = list(state.image.pixels)
        pixels[index] = tuple(pixel)
        image = replace(state.image, pixels=tuple(pixels), maximum=max(state.image.maximum, value))
        return self._rebuild(state, image, undo=(*state.undo[-99:], state.image), redo=(),
                             message='')

    def _move(self, state, keys):
        axes = self.movement_keys.update(keys)
        # At the initial isometric angle W follows -X and D follows +Y.
        dx, dy = -int(axes.y), int(axes.x)
        quarter = round((state.camera.look_azimuth() - pi / 4) / (pi / 2)) % 4
        for _ in range(quarter):
            dx, dy = -dy, dx
        coordinate = state.cursor[0] + dx, state.cursor[1] + dy
        if coordinate not in state.map or coordinate == state.cursor:
            return state
        return replace(state, cursor=coordinate, quit_pending=False, message='')

    def step(self, state, seconds, pressed_keys):
        axes = self.movement_keys.update(pressed_keys)
        if not (axes.x or axes.y) or {'left ctrl', 'right ctrl'} & pressed_keys:
            return replace(state, cursor_delay=0.0)
        delay = state.cursor_delay - seconds
        if delay > 0:
            return replace(state, cursor_delay=delay)
        return replace(self._move(state, pressed_keys), cursor_delay=0.12)

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
            return replace(state, camera=self.mouselook.update(state.camera, message), quit_pending=False)
        if isinstance(message, ScrollMessage):
            return self._edit(state, int(message.offset.y), message.modifiers)
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
            return self._edit(state, -1 if message.key in (',', '<') else 1, message.modifiers)
        if not message.modifiers & KeyboardModifiers.CTRL:
            moved = self._move(state, frozenset((message.key,)))
            if moved is not state:
                return replace(moved, cursor_delay=0.25)
        axes = self.camera_keys.update(frozenset((message.key,)))
        if axes.x or axes.y:
            return replace(state, camera=replace(state.camera,
                raw_azimuth=(state.camera.look_azimuth() + axes.x * pi / 2) % (2 * pi),
                elevation=max(pi / 6, min(pi / 3, state.camera.elevation + axes.y * pi / 6))),
                quit_pending=False)
        return state
