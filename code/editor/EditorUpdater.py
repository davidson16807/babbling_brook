"""Editor MVU transitions. Input and persistence remain outside the model."""
from bisect import bisect_left, bisect_right
from dataclasses import replace
from math import floor, isfinite, pi

from pyglm import glm

from ..codec.map.PpmImageCodec import PpmImage
from ..codec.map.ObjectPlacementCodec import ObjectPlacementCodec
from ..messages import (FocusLostMessage, KeyboardAction, KeyboardMessage,
                        KeyboardModifiers, MouseButton, MouseMotionMessage,
                        QuitMessage, ScrollMessage, WindowResizeMessage)


class EditorUpdater:
    def __init__(self, map_codec, object_palette, cursor, mouselook, keylook, history, cycle_system, box_archetypes=None):
        self.map_codec = map_codec
        self.object_palette = object_palette
        self.box_archetypes = box_archetypes or {}
        self.cursor = cursor
        self.mouselook = mouselook  # A vector updater, with no angle locking.
        self.keylook = keylook      # The regular game's composed look updater.
        self.history = history
        self.cycle_system = cycle_system
        self.tile_ids = sorted(map_codec.tile_palette)
        self.object_ids = sorted({0, *object_palette})

    def _move(self, state, messages):
        modifiers = KeyboardModifiers.NONE
        for message in messages:
            modifiers |= message.modifiers
        if modifiers & KeyboardModifiers.CTRL:
            return state
        if state.object_step is not None:
            center = state.content.object_center(state.selected_objects)
            if center is None:
                return replace(state, message='No objects selected. Highlight objects, then press E or Ctrl+E.')
            axes = glm.vec3(0)
            quadrant = floor(state.camera.look_azimuth / (pi / 2) + .5) % 4
            forward = glm.vec3(*((-1, 0), (0, -1), (1, 0), (0, 1))[quadrant], 0)
            right = glm.vec3(forward.y, -forward.x, 0)
            for message in messages:
                axes += {'w': forward, 's': -forward, 'a': -right, 'd': right,
                         'q': glm.vec3(0, 0, 1), 'z': glm.vec3(0, 0, -1)}.get(message.key, glm.vec3(0))
            state = self._move_objects(state, axes * state.object_step)
            moved = state.content.object_center(state.selected_objects)
            # Follow crossed tile boundaries, not key presses: fine movement
            # must not move the cursor ten times faster than the objects.
            delta = glm.ivec2(glm.floor(moved.xy) - glm.floor(center.xy))
            cursor = self.cursor.translate(state.cursor, state.map.dimensions, delta)
            return replace(state, cursor=cursor, quit_requested=False)
        cursor = self.cursor.update(
            state.cursor, state.map.dimensions, state.camera, messages,
            bool(modifiers & KeyboardModifiers.SHIFT),
        )
        return replace(state, cursor=cursor, quit_requested=False)

    def step(self, state, seconds, messages):
        """Rate-limit live held-key messages; never retain a held-input cache."""
        state = replace(state, cycles=self.cycle_system.step(state.cycles, seconds / 60 * state.time_warp))
        if not messages:
            return replace(state, cursor_delay=0.0)
        delay = max(0.0, state.cursor_delay - seconds)
        if delay > 0:
            return replace(state, cursor_delay=delay)
        return replace(self._move(state, messages), cursor_delay=.12)

    def _warp(self, state, faster):
        # At factor period/1min, that cycle takes one real minute. Include 1x so
        # normal time is reachable even when no configured period equals one.
        rates = {1.0, *(c.period for c in state.cycles.values()
                       if isfinite(c.period) and c.period > 0)}
        factors = sorted({0.0, *rates, *(-rate for rate in rates)})
        index = (bisect_right(factors, state.time_warp) if faster
                 else bisect_left(factors, state.time_warp)-1)
        factor = factors[max(0, min(len(factors)-1, index))]
        return replace(state, time_warp=factor, message=f'Time warp: {factor:g}x.')

    def _rebuild(self, state):
        # Placements are authoritative content now; only terrain is derived.
        return replace(state, map=self.map_codec.decode(state.content.image),
                       quit_requested=False)

    def _commit(self, state, pixels, message):
        pixels = tuple(pixels)
        if pixels == state.content.image.pixels:
            return state
        image = replace(state.content.image, pixels=pixels,
                        maximum=max(state.content.image.maximum, max(max(p) for p in pixels)))
        map_ = self.map_codec.decode(image)
        billboards, boxes = ObjectPlacementCodec(
            self.object_palette, map_, disable_validation=True,
            box_archetypes=self.box_archetypes, zone=state.content.zone).decode_components(image)
        # Regenerate map placements after a pixel edit, retaining explicit ones.
        previous = ObjectPlacementCodec(
            self.object_palette, state.map, disable_validation=True,
            box_archetypes=self.box_archetypes, zone=state.content.zone).decode(state.content.image)
        billboards.update((key, value) for key, value in state.content.billboards.items()
                          if key not in previous)
        boxes.update((key, value) for key, value in state.content.boxes.items()
                     if key not in previous)
        content = replace(state.content, image=image, billboards=billboards, boxes=boxes)
        return replace(self.history.do(state, content), map=map_,
                       message=message, quit_requested=False)

    def _object_mode(self, state, step):
        # Keep the same group when switching precision, even after it has moved.
        tiles = set(state.cursor)
        selected = state.selected_objects if state.object_step is not None else frozenset(
            key for table in (state.content.billboards, state.content.boxes,
                              state.content.character_instances)
            for key, item in table.items()
            if (floor(item.position.x), floor(item.position.y)) in tiles
        )
        return replace(state, channel=None, time_mode=False, object_step=step,
                       selected_objects=selected, cursor_delay=0.0, quit_requested=False,
                       message=f'Move {len(selected)} object(s), step {step:g}. Q up / Z down.')

    def _move_objects(self, state, offset, snap=False):
        if not state.selected_objects or (not snap and not glm.length(offset)):
            return state
        content = state.content
        pixels = list(content.image.pixels)
        mapped = ObjectPlacementCodec(self.object_palette, state.map, disable_validation=True,
                                      box_archetypes=self.box_archetypes, zone=state.content.zone).decode(content.image)
        tables = [dict(content.billboards), dict(content.boxes), dict(content.character_instances)]
        occupied = set().union(*tables)
        selected = set(state.selected_objects)
        for table in tables:
            for key in sorted(state.selected_objects & table.keys()):
                item = table[key]
                position = glm.vec3(*(round(v) for v in item.position)) if snap else item.position + offset
                if position == item.position:
                    continue
                new_key = key
                if key in mapped:
                    # Detach the PPM instance before moving it. Its old cell can
                    # now be painted independently, without resurrecting it.
                    x, y = map(int, glm.floor(mapped[key].position.xy))
                    index = y * content.image.width + x
                    pixels[index] = (*pixels[index][:2], 0)
                    suffix = 1
                    while f'editor-object-{suffix}' in occupied:
                        suffix += 1
                    new_key = f'editor-object-{suffix}'
                    occupied.add(new_key)
                    selected.remove(key)
                    selected.add(new_key)
                del table[key]
                table[new_key] = replace(item, position=position)
        content = replace(content, image=replace(content.image, pixels=tuple(pixels)),
                          billboards=tables[0], boxes=tables[1], character_instances=tables[2])
        return replace(self.history.do(state, content), selected_objects=frozenset(selected),
                       quit_requested=False, message='Objects snapped.' if snap else 'Objects moved.')

    def _zoom(self, state, amount):
        # A smaller orthographic span means a closer view. Bound the exponent
        # as well as the span to handle large wheel deltas without overflow.
        scale = state.camera.orthographic_scale * 1.1 ** -max(-100, min(100, amount))
        return replace(state, camera=replace(state.camera,
                       orthographic_scale=max(1.0, min(128.0, scale))))

    def _adjust(self, state, amount):
        if state.time_mode:
            for _ in range(abs(amount)):
                state = self._warp(state, amount > 0)
            return state
        if state.channel is None:
            return self._zoom(state, amount)
        channel = state.channel
        pixels = list(state.content.image.pixels)
        ids = self.tile_ids if channel == 1 else self.object_ids
        for x, y in state.cursor:
            index = y * state.content.image.width + x
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
        if state.time_mode:
            return (replace(state, time_warp=0.0, message='Time paused.')
                    if value == 0 else state)
        if state.channel is None:
            return state
        pixels = list(state.content.image.pixels)
        for x, y in state.cursor:
            index = y * state.content.image.width + x
            pixel = list(pixels[index])
            pixel[state.channel] = value
            pixels[index] = tuple(pixel)
        return self._commit(state, pixels,
                            f'Set channel {state.channel} to {value} on {len(state.cursor)} tile(s).')

    def _copy(self, state):
        x0, x1 = min(x for x, _ in state.cursor), max(x for x, _ in state.cursor)
        y0, y1 = min(y for _, y in state.cursor), max(y for _, y in state.cursor)
        clipboard = PpmImage(x1-x0+1, y1-y0+1, state.content.image.maximum, tuple(
            state.content.image.pixels[y*state.content.image.width + x]
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
                       for y in range(min(clipboard.height, state.content.image.height-y0))
                       for x in range(min(clipboard.width, state.content.image.width-x0))]
        pixels = list(state.content.image.pixels)
        for x, y, source in targets:
            index = y * state.content.image.width + x
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
        return replace(self._rebuild(updated), object_step=None, selected_objects=frozenset(),
                       message='Redone.' if redo else 'Undone.')

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
                if key == 'e':
                    return self._object_mode(state, .1)
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
                if state.object_step is not None and state.object_step < 1:
                    state = self._move_objects(state, glm.vec3(0), snap=True)
                return replace(state, channel=None, time_mode=False, object_step=None,
                               selected_objects=frozenset(), message='Zoom mode.', quit_requested=False)
            if key == 'e':
                return self._object_mode(state, 1.0)
            if key == 't':
                return replace(state, channel=None, time_mode=True, object_step=None,
                               selected_objects=frozenset(), message='Time mode. / pauses.')
            if key in ('r', 'g', 'b'):
                channel = {'r': 0, 'g': 1, 'b': 2}[key]
                label = ('Height', 'Tile', 'Object')[channel]
                return replace(state, channel=channel, time_mode=False, object_step=None,
                               selected_objects=frozenset(), message=f'{label} mode.', quit_requested=False)
            if key in ('+', '=', '[+]', 'kp +'):
                return self._zoom(state, 1)
            if key in ('-', '[-]', 'kp -'):
                return self._zoom(state, -1)
            if key in (',', '<', '.', '>'):
                return self._adjust(state, -1 if key in (',', '<') else 1)
            if key == '/':
                return self._set(state, 0)
            if key == 'delete':
                return self._set(state, 0)
            if key in '0123456789' and len(key) == 1:
                return self._set(state, int(key))
            if key in ('w', 'a', 's', 'd', 'z', 'q'):
                return replace(self._move(state, (message,)),
                               cursor_delay=.25)
            if key in ('i', 'j', 'k', 'l'):
                return replace(state, camera=self.keylook.update(state.camera, message))
        return state
