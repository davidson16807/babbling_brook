"""Pure update function for dialog-mode messages."""
from __future__ import annotations

from dataclasses import replace
from math import dist

from .DialogLayout import DialogLayout, contains
from .DialogLexicon import default_phrase
from .DialogMessages import KeyPress, PointerDown, PointerMove, PointerUp, Quit, Resize
from .DialogState import DragState, NounPhraseItem, PhraseToken, WordItem
from .DialogValidator import DialogValidator


class DialogUpdater:
    def __init__(self, layout=None, validator=None):
        self.layout = layout or DialogLayout()
        self.validator = validator or DialogValidator()

    def _replace_item(self, state, changed):
        return replace(state, playmat=tuple(changed if item.id == changed.id else item
                                            for item in state.playmat))

    def _select_option(self, state, item_id, index):
        item = state.item(item_id)
        if item is None:
            return state
        text, option = self.layout.option(state, item, index)
        if isinstance(item, NounPhraseItem):
            return self._replace_item(state, replace(item, tokens=option))
        return self._replace_item(state, replace(item, text=text, tagpoints=option.tagpoints))

    def _pointer_down(self, state, position):
        layout = self.layout.build(state)
        hit = layout.hit(position)
        if hit.kind == 'close':
            return replace(state, active_item_id=None)
        if hit.kind == 'clear':
            return replace(state, playmat=(), active_item_id=None,
                           feedback='Playmat cleared.')
        if hit.kind == 'talk':
            return replace(state, feedback=self.validator.validate(state).text)
        if hit.kind == 'option':
            return self._select_option(state, hit.parent, hit.value)
        if hit.kind == 'inventory':
            drag = DragState('inventory', hit.value, position, position)
            return replace(state, drag=drag)
        if hit.kind == 'token':
            phrase = state.item(hit.parent)
            token = phrase.tokens[hit.value]
            if token.role == 'adjective':
                drag = DragState('adjective', hit.value, position, position,
                                 phrase_id=phrase.id)
            else:
                drag = DragState('item', phrase.id, position, position)
            return replace(state, drag=drag)
        if hit.kind == 'item':
            return replace(state, drag=DragState('item', hit.value, position, position))
        return state

    def _inventory_drop(self, state, drag, position, layout):
        lexeme = state.lexeme(str(drag.source_id))
        if lexeme.part_of_speech == 'adjective':
            phrase_id = layout.phrase_at(position)
            phrase = state.item(phrase_id) if phrase_id is not None else None
            if not isinstance(phrase, NounPhraseItem):
                return replace(state, drag=None, feedback='Adjectives belong inside noun phrases.')
            form = lexeme.inflections[0]
            token = PhraseToken('adjective', form.text, lexeme.id, form.tagpoints)
            index = self.layout.token_index(layout, phrase.id, position[0])
            tokens = list(phrase.tokens)
            tokens.insert(index, token)
            changed = replace(phrase, tokens=tuple(tokens))
            return replace(self._replace_item(state, changed), drag=None,
                           active_item_id=phrase.id, feedback='Choose a noun-phrase inflection.')
        if not contains(layout.playmat, position):
            return replace(state, drag=None)
        if lexeme.part_of_speech == 'noun':
            item = default_phrase(state.next_id, lexeme)
        else:
            form = next((form for form in lexeme.inflections if form.text == lexeme.canonical),
                        lexeme.inflections[0])
            item = WordItem(state.next_id, lexeme.id, form.text, form.tagpoints)
        index = self.layout.playmat_index(layout, state, position[0])
        playmat = list(state.playmat)
        playmat.insert(index, item)
        return replace(state, playmat=tuple(playmat), next_id=state.next_id + 1,
                       active_item_id=item.id, drag=None, feedback='Choose an inflection.')

    def _item_drop(self, state, drag, position, layout):
        if not drag.moved:
            return replace(state, drag=None, active_item_id=int(drag.source_id))
        if not contains(layout.playmat, position):
            return replace(state, drag=None)
        item = state.item(int(drag.source_id))
        remaining = tuple(candidate for candidate in state.playmat if candidate.id != item.id)
        temporary = replace(state, playmat=remaining)
        index = self.layout.playmat_index(self.layout.build(temporary), temporary, position[0])
        playmat = list(remaining)
        playmat.insert(index, item)
        return replace(state, playmat=tuple(playmat), drag=None, active_item_id=item.id)

    def _adjective_drop(self, state, drag, position, layout):
        source = state.item(drag.phrase_id)
        if not isinstance(source, NounPhraseItem) or int(drag.source_id) >= len(source.tokens):
            return replace(state, drag=None)
        token = source.tokens[int(drag.source_id)]
        target_id = layout.phrase_at(position)
        target = state.item(target_id) if target_id is not None else None
        if not isinstance(target, NounPhraseItem):
            return replace(state, drag=None, feedback='Adjectives belong inside noun phrases.')
        source_tokens = list(source.tokens)
        source_tokens.pop(int(drag.source_id))
        state = self._replace_item(state, replace(source, tokens=tuple(source_tokens)))
        target = state.item(target.id)
        # Rebuild after removing the source, so insertion indices match the view.
        current_layout = self.layout.build(state)
        index = self.layout.token_index(current_layout, target.id, position[0])
        target_tokens = list(target.tokens)
        target_tokens.insert(index, token)
        state = self._replace_item(state, replace(target, tokens=tuple(target_tokens)))
        return replace(state, drag=None, active_item_id=target.id)

    def update(self, state, message):
        if isinstance(message, Quit):
            return replace(state, running=False)
        if isinstance(message, Resize):
            return replace(state, viewport=(max(640, message.size[0]), max(480, message.size[1])))
        if isinstance(message, KeyPress):
            if message.key == 'escape':
                return (replace(state, active_item_id=None, drag=None) if state.active_item_id is not None
                        else replace(state, running=False))
            if message.key in ('e', 'return'):
                return replace(state, feedback=self.validator.validate(state).text)
            if message.key in ('delete', 'backspace'):
                return replace(state, playmat=(), active_item_id=None,
                               feedback='Playmat cleared.')
            return state
        if isinstance(message, PointerDown):
            return self._pointer_down(state, message.position)
        if isinstance(message, PointerMove) and state.drag is not None:
            moved = state.drag.moved or dist(state.drag.origin, message.position) >= 5
            return replace(state, drag=replace(state.drag, position=message.position, moved=moved))
        if isinstance(message, PointerUp) and state.drag is not None:
            layout = self.layout.build(state)
            if state.drag.kind == 'inventory':
                return self._inventory_drop(state, state.drag, message.position, layout)
            if state.drag.kind == 'item':
                return self._item_drop(state, state.drag, message.position, layout)
            return self._adjective_drop(state, state.drag, message.position, layout)
        return state
