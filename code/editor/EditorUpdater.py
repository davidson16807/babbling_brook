"""Editor MVU transitions. Input and persistence remain outside the model."""
from bisect import bisect_left, bisect_right
from dataclasses import replace

from ..codec.map.PpmImageCodec import PpmImage
from ..codec.map.ObjectPlacementCodec import ObjectPlacementCodec
from ..messages import (FocusLostMessage, KeyboardAction, KeyboardMessage,
                        KeyboardModifiers, MouseButton, MouseMotionMessage,
                        QuitMessage, ScrollMessage, WindowResizeMessage)


class EditorUpdater:
    def __init__(self, map_codec, object_palette, cursor, mouselook, keylook, history):
        self.map_codec = map_codec
        self.object_palette = object_palette
        self.cursor = cursor
        self.mouselook = mouselook  # A vector updater, with no angle locking.
        self.keylook = keylook      # The regular game's composed look updater.
        self.history = history
        self.tile_ids = sorted(map_codec.tile_palette)
        self.object_ids = sorted({0, *object_palette})

    def _move(self, state, messages):
        modifiers = KeyboardModifiers.NONE
        for message in messages:
            modifiers |= message.modifiers
        if modifiers & KeyboardModifiers.CTRL:
            return state
        cursor = self.cursor.update(
            state.cursor, state.map.dimensions, state.camera, messages,
            bool(modifiers & KeyboardModifiers.SHIFT),
        )
        return replace(state, cursor=cursor, quit_requested=False)

    def step(self, state, seconds, messages):
        """Rate-limit live held-key messages; never retain a held-input cache."""
        if not messages:
            return replace(state, cursor_delay=0.0)
        delay = max(0.0, state.cursor_delay - seconds)
        if delay > 0:
            return replace(state, cursor_delay=delay)
        return replace(self._move(state, messages), cursor_delay=.12)

    def _rebuild(self, state):
        map_ = self.map_codec.decode(state.image)
        placements = ObjectPlacementCodec(self.object_palette, map_, disable_validation=True).decode(state.image)
        return replace(state, map=map_, placements=placements, quit_requested=False)

    def _commit(self, state, pixels, message):
        pixels = tuple(pixels)
        if pixels == state.image.pixels:
            return state
        image = replace(state.image, pixels=pixels,
                        maximum=max(state.image.maximum, max(max(p) for p in pixels)))
        return replace(self._rebuild(self.history.do(state, image)), message=message)

    def _zoom(self, state, amount):
        # A smaller orthographic span means a closer view. Bound the exponent
        # as well as the span to handle large wheel deltas without overflow.
        scale = state.camera.orthographic_scale * 1.1 ** -max(-100, min(100, amount))
        return replace(state, camera=replace(state.camera,
                       orthographic_scale=max(1.0, min(128.0, scale))))

    def _adjust(self, state, amount):
        if state.channel is None:
            return self._zoom(state, amount)
        channel = state.channel
        pixels = list(state.image.pixels)
        ids = self.tile_ids if channel == 1 else self.object_ids
        for x, y in state.cursor:
            index = y * state.image.width + x
            pixel = list(pixels[index])
            if channel == 0:
                pixel[0] = max(0, min(65535, pixel[0] + amount))
            else:
                # Continue palette stepping even after typing an unassigned ID.
                if not ids or not amount:
                    continue
                offset = (bisect_right(ids, pixel[channel]) + amount - 1 if amount > 0
                          else bisect_left(ids, pixel[channel]) + amount)
                pixel[channel] = ids[max(0, min(len(ids) - 1, offset))]
            pixels[index] = tuple(pixel)
        label = ('height', 'tile ID', 'object ID')[channel]
        return self._commit(state, pixels,
                            f'Changed {label} on {len(state.cursor)} selected tile(s).')

    def _set(self, state, value):
        if state.channel is None:
            return state
        pixels = list(state.image.pixels)
        for x, y in state.cursor:
            index = y * state.image.width + x
            pixel = list(pixels[index])
            pixel[state.channel] = value
            pixels[index] = tuple(pixel)
        return self._commit(state, pixels,
                            f'Set channel {state.channel} to {value} on {len(state.cursor)} tile(s).')

    def _copy(self, state):
        x0, x1 = min(x for x, _ in state.cursor), max(x for x, _ in state.cursor)
        y0, y1 = min(y for _, y in state.cursor), max(y for _, y in state.cursor)
        clipboard = PpmImage(x1-x0+1, y1-y0+1, state.image.maximum, tuple(
            state.image.pixels[y*state.image.width + x]
            for y in range(y0, y1+1) for x in range(x0, x1+1)
        ))
        return replace(state, clipboard=clipboard,
                       message=f'Copied {clipboard.width} x {clipboard.height} tiles.')

    def _paste(self, state):
        clipboard = state.clipboard
        if clipboard is None:
            return replace(state, message='Clipboard is empty.')
        if clipboard.width == clipboard.height == 1:
            targets = [(x, y, clipboard.pixels[0]) for x, y in state.cursor]
        else:
            # The yellow head is the northwest corner regardless of camera or
            # selection direction. Clip to existing map bounds; never resize it.
            x0, y0 = state.cursor[-1]
            targets = [(x0+x, y0+y, clipboard.pixels[y*clipboard.width+x])
                       for y in range(min(clipboard.height, state.image.height-y0))
                       for x in range(min(clipboard.width, state.image.width-x0))]
        pixels = list(state.image.pixels)
        for x, y, source in targets:
            index = y * state.image.width + x
            if state.channel is None:
                pixels[index] = source
            else:
                pixel = list(pixels[index])
                pixel[state.channel] = source[state.channel]
                pixels[index] = tuple(pixel)
        return self._commit(state, pixels, f'Pasted onto {len(targets)} tile(s).')

    def _traverse(self, state, redo=False):
        updated = self.history.redo(state) if redo else self.history.undo(state)
        if updated is state:
            return replace(state, message='Nothing to redo.' if redo else 'Nothing to undo.')
        return replace(self._rebuild(updated), message='Redone.' if redo else 'Undone.')

    def _quit(self, state):
        if state.dirty and not state.quit_requested:
            return replace(state, quit_requested=True,
                           message='Unsaved changes. Ctrl+S saves; close again discards.')
        return replace(state, running=False)

    def update(self, state, message):
        if isinstance(message, QuitMessage):
            return self._quit(state)
        if isinstance(message, WindowResizeMessage):
            return replace(state, viewport=message.size)
        if isinstance(message, FocusLostMessage):
            return replace(state, cursor_delay=0.0)
        if isinstance(message, MouseMotionMessage) and MouseButton.MIDDLE in message.buttons:
            return replace(state, camera=self.mouselook.update(state.camera, message))
        if isinstance(message, ScrollMessage):
            return self._adjust(state, int(message.offset.y))
        if isinstance(message, KeyboardMessage) and message.action == KeyboardAction.PRESS:
            key = message.key
            if message.modifiers & KeyboardModifiers.CTRL:
                if key == 'c':
                    return self._copy(state)
                if key == 'v':
                    return self._paste(state)
                if key == 'z':
                    return self._traverse(state, bool(message.modifiers & KeyboardModifiers.SHIFT))
                if key == 'y':
                    return self._traverse(state, redo=True)
                if key == 'w':
                    return self._quit(state)
                return state
            if key == 'escape':
                return replace(state, channel=None, message='Zoom mode.', quit_requested=False)
            if key in ('t', 'z', 'e'):
                channel = {'z': 0, 't': 1, 'e': 2}[key]
                label = ('Height', 'Tile', 'Object')[channel]
                return replace(state, channel=channel, message=f'{label} mode.', quit_requested=False)
            if key in ('+', '=', '[+]', 'kp +'):
                return self._zoom(state, 1)
            if key in ('-', '[-]', 'kp -'):
                return self._zoom(state, -1)
            if key in (',', '[', '.', ']'):
                return self._adjust(state, -1 if key in (',', '[') else 1)
            if key == 'delete':
                return self._set(state, 0)
            if key in '0123456789' and len(key) == 1:
                return self._set(state, int(key))
            if key in ('w', 'a', 's', 'd'):
                return replace(self._move(state, (message,)),
                               cursor_delay=.25)
            if key in ('i', 'j', 'k', 'l'):
                return replace(state, camera=self.keylook.update(state.camera, message))
        return state
