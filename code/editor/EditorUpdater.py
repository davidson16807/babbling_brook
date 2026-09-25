"""Editor MVU transitions. Input and persistence remain outside the model."""
from dataclasses import replace
from math import pi

from pyglm import glm

from ..codec.map.ObjectPlacementCodec import ObjectPlacementCodec
from ..messages import (FocusLostMessage, KeyboardAction, KeyboardMessage,
                        KeyboardModifiers, MouseButton, MouseMotionMessage,
                        QuitMessage, ScrollMessage, WindowResizeMessage)


class EditorUpdater:
    def __init__(self, map_codec, object_palette, cursor, mouselook, keylook):
        self.map_codec = map_codec
        self.object_palette = object_palette
        self.cursor = cursor
        self.mouselook = mouselook  # A vector updater, with no angle locking.
        self.keylook = keylook      # The regular game's composed look updater.
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

    def _edit(self, state, channel, amount):
        if not amount:
            return state
        pixels = list(state.image.pixels)
        ids = self.tile_ids if channel == 1 else self.object_ids
        for x, y in state.cursor:
            index = y * state.image.width + x
            pixel = list(pixels[index])
            if channel == 0:
                pixel[0] = max(0, min(65535, pixel[0] + amount))
            else:
                # Palette IDs need not be consecutive. Never create an unknown ID.
                offset = max(0, min(len(ids) - 1, ids.index(pixel[channel]) + amount))
                pixel[channel] = ids[offset]
            pixels[index] = tuple(pixel)
        if tuple(pixels) == state.image.pixels:
            return state
        image = replace(state.image, pixels=tuple(pixels),
                        maximum=max(state.image.maximum, max(max(p) for p in pixels)))
        map_ = self.map_codec.decode(image)
        placements = ObjectPlacementCodec(self.object_palette, map_).decode(image)
        label = ('height', 'tile ID', 'object ID')[channel]
        return replace(state, image=image, map=map_, placements=placements, dirty=True,
                       quit_requested=False,
                       message=f'Changed {label} on {len(state.cursor)} selected tile(s).')

    def _quit(self, state):
        if state.dirty and not state.quit_requested:
            return replace(state, quit_requested=True,
                           message='Unsaved changes. Ctrl+S saves; Escape or close again discards.')
        return replace(state, running=False)

    def update(self, state, message):
        if isinstance(message, QuitMessage):
            return self._quit(state)
        if isinstance(message, WindowResizeMessage):
            return replace(state, viewport=message.size)
        if isinstance(message, FocusLostMessage):
            return replace(state, cursor_delay=0.0)
        if isinstance(message, MouseMotionMessage) and MouseButton.MIDDLE in message.buttons:
            v = self.mouselook.update(
                glm.vec2(state.camera.raw_azimuth, state.camera.raw_elevation), message)
            az, el = max(0.0, min(pi, v.x)), max(0.0, min(pi/2, v.y))
            return replace(state, camera=replace(state.camera,
                           raw_azimuth=az, raw_elevation=el,
                           look_azimuth=az, look_elevation=el))
        if isinstance(message, ScrollMessage):
            # Ctrl chooses tiles; Shift chooses objects; otherwise change height.
            channel = (1 if message.modifiers & KeyboardModifiers.CTRL else
                       2 if message.modifiers & KeyboardModifiers.SHIFT else 0)
            return self._edit(state, channel, int(message.offset.y))
        if isinstance(message, KeyboardMessage) and message.action == KeyboardAction.PRESS:
            key = message.key
            if key == 'escape':
                return self._quit(state)
            if key in ('w', 'a', 's', 'd'):
                return replace(self._move(state, (message,)),
                               cursor_delay=.25)
            if key in ('i', 'j', 'k', 'l'):
                return replace(state, camera=self.keylook.update(state.camera, message))
            edits = {',': (0, -1), '<': (0, -1), '.': (0, 1), '>': (0, 1),
                     '[': (1, -1), ']': (1, 1), '9': (2, -1), '0': (2, 1)}
            if key in edits:
                return self._edit(state, *edits[key])
        return state
