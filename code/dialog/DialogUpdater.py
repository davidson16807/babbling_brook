"""Pure model/message -> model update. Drag transactions commit only on drop."""
from dataclasses import replace

from ..messages import (ButtonAction, FocusLostMessage, KeyboardAction, KeyboardMessage,
                        MouseButton, MouseButtonMessage, MouseMotionMessage, QuitMessage,
                        ScrollMessage, WindowResizeMessage)
from .DialogState import DialogDrag, DialogPiece, DialogTurn, make_word, select_form


class DialogUpdater:
    def __init__(self, language, view, grammar):
        self.language, self.view, self.grammar = language, view, grammar

    def open(self, state, id):
        state = replace(state, selected=id, grid_open=True, grid_scroll=0, drag=None)
        # Scroll the canonical/current selection into view, wherever shuffled.
        scene = self.view.layout(state)
        selected = state.find(id)
        for element in scene.elements:
            if element.target and element.target.kind == 'option' and element.target.key == selected.text:
                overflow = element.rect.y + element.rect.h - (scene.grid.y + scene.grid.h)
                if overflow > 0:
                    state = replace(state, grid_scroll=min(scene.grid_max, overflow + 8))
                break
        return state

    def add(self, state, lexeme, index=None, parent=None, part_index=None):
        if lexeme not in self.language.lexemes:
            return state
        entry = self.language.lexemes[lexeme]
        word = make_word(self.language, lexeme, state.next_id)
        if entry.kind == 'adjective':
            owner = state.find(parent)
            if owner is None or self.language.lexemes[owner.lexeme].kind != 'noun':
                return state
            parts = list(owner.pieces)
            i = len(parts) if part_index is None else max(0, min(part_index, len(parts)))
            parts.insert(i, DialogPiece(f'adj:{word.id}', 'adj', '', word))
            state = state.replace_word(replace(owner, pieces=tuple(parts)))
        else:
            words = list(state.words)
            i = len(words) if index is None else max(0, min(index, len(words)))
            words.insert(i, word)
            state = replace(state, words=tuple(words))
        state = self.open(replace(state, next_id=state.next_id + 1, command=None), word.id)
        scene = self.view.layout(state)
        rect = next((r for owner, key, r in scene.pieces if key == f'adj:{word.id}'), None)
        if rect is None:
            rect = dict(scene.nodes)[word.id]
        if rect.y < scene.mat.y:
            state = replace(state, mat_scroll=max(0, state.mat_scroll + rect.y - scene.mat.y))
        elif rect.y + rect.h > scene.mat.y + scene.mat.h:
            state = replace(state, mat_scroll=min(scene.mat_max,
                            state.mat_scroll + rect.y + rect.h - scene.mat.y - scene.mat.h))
        return state

    def choose(self, state, text):
        word = state.find(state.selected)
        if word is None or text not in self.language.lexemes[word.lexeme].bundle:
            return state
        return replace(state.replace_word(select_form(self.language, word, text)), command=None)

    def remove(self, state, id):
        if state.find(id) is None:
            return state
        words = tuple(replace(w, pieces=tuple(p for p in w.pieces if not p.word or p.word.id != id))
                      for w in state.words if w.id != id)
        result = replace(state, words=words, command=None, drag=None)
        return replace(result, selected=None, grid_open=False) if result.find(state.selected) is None else result

    def talk(self, state):
        command = self.grammar.validate(state)
        text = ' '.join(w.surface for w in state.words)
        # The demo emits a command value; no explorer world is loaded or mutated.
        turn = DialogTurn(text or '...', 'All right.' if command else 'What?')
        return replace(state, command=command, turns=(*state.turns[-11:], turn), drag=None, grid_open=False)

    def _activate(self, state, target):
        if target is None:
            return state
        if target.kind == 'option':
            return self.choose(state, target.key)
        if target.kind == 'close':
            return replace(state, grid_open=False, drag=None)
        if target.kind == 'clear':
            return replace(state, words=(), selected=None, grid_open=False, drag=None, command=None, mat_scroll=0)
        if target.kind == 'talk':
            return self.talk(state)
        if target.kind == 'word':
            return self.open(state, target.word)
        if target.kind == 'part':
            word = state.find(target.word)
            part = next(p for p in word.pieces if p.key == target.key)
            return self.open(state, part.word.id if part.word else word.id)
        return state

    def _drop(self, state, source, position, scene):
        if source.kind != 'inventory' and scene.inventory.contains(position):
            if source.kind == 'part':
                owner = state.find(source.word)
                part = next(p for p in owner.pieces if p.key == source.key)
                # Stock words cannot be deleted independently of their inflection.
                return self.remove(state, part.word.id) if part.word else state
            return self.remove(state, source.word)
        if not scene.mat.contains(position):
            return state
        parent = next((id for id, rect in scene.nodes if rect.contains(position)), None)
        owner = state.find(parent)
        part_rects = [(key, rect) for id, key, rect in scene.pieces if id == parent]
        part_index = scene.insertion([r for _, r in part_rects], position)
        index = scene.insertion([r for _, r in scene.nodes], position)
        if source.kind == 'inventory':
            return self.add(state, source.key, index, parent, part_index)
        if source.kind == 'word':
            old = next(i for i, w in enumerate(state.words) if w.id == source.word)
            words = list(state.words)
            word = words.pop(old)
            words.insert(index - (old < index), word)
            return replace(state, words=tuple(words), command=None)
        if source.kind == 'part':
            source_owner = state.find(source.word)
            old = next(i for i, p in enumerate(source_owner.pieces) if p.key == source.key)
            piece = source_owner.pieces[old]
            if owner is None or self.language.lexemes[owner.lexeme].kind != 'noun' and owner.id != source_owner.id:
                return state
            if owner.id != source_owner.id and not piece.word:
                return state
            remaining = list(source_owner.pieces)
            remaining.pop(old)
            if owner.id == source_owner.id:
                remaining.insert(part_index - (old < part_index), piece)
                return replace(state.replace_word(replace(owner, pieces=tuple(remaining))), command=None)
            result = state.replace_word(replace(source_owner, pieces=tuple(remaining)))
            parts = list(owner.pieces)
            parts.insert(part_index, piece)
            return replace(result.replace_word(replace(owner, pieces=tuple(parts))), command=None)
        return state

    def update(self, state, message):
        if isinstance(message, QuitMessage):
            return replace(state, running=False, drag=None)
        if isinstance(message, FocusLostMessage):
            return replace(state, drag=None)
        if isinstance(message, WindowResizeMessage):
            return replace(state, viewport=(max(860, message.size[0]), max(680, message.size[1])), drag=None)
        if isinstance(message, KeyboardMessage) and message.action == KeyboardAction.PRESS:
            if message.key == 'escape':
                return replace(state, drag=None, grid_open=False)
            if message.key in ('return', 'enter', 'e') and state.drag is None:
                return self.talk(state)
            if message.key in ('delete', 'backspace'):
                return self.remove(state, state.selected)
        scene = self.view.layout(state)
        if isinstance(message, ScrollMessage) and message.position is not None:
            for field, region, maximum in [('inventory_scroll', scene.inventory, scene.inventory_max),
                                          ('grid_scroll', scene.grid, scene.grid_max),
                                          ('mat_scroll', scene.mat, scene.mat_max)]:
                if region.contains(message.position):
                    return replace(state, **{field: max(0, min(maximum, getattr(state, field) - int(message.offset.y * 48)))})
        if isinstance(message, MouseMotionMessage) and state.drag:
            position = tuple(message.position)
            start = state.drag.start
            moving = state.drag.moving or (position[0] - start[0]) ** 2 + (position[1] - start[1]) ** 2 >= 36
            return replace(state, drag=replace(state.drag, position=position, moving=moving))
        if isinstance(message, MouseButtonMessage) and message.button == MouseButton.LEFT and message.position is not None:
            position = tuple(message.position)
            target = scene.hit(position)
            if message.action == ButtonAction.PRESS:
                return replace(state, drag=DialogDrag(target, position, position)) if target else state
            if message.action == ButtonAction.RELEASE and state.drag:
                source, moving = state.drag.source, state.drag.moving
                result = replace(state, drag=None)
                if moving and source.kind in ('inventory', 'word', 'part'):
                    return self._drop(result, source, position, scene)
                if not moving and source == target:
                    return self._activate(result, target)
                return result
        return state
