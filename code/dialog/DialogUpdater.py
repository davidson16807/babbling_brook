"""Dialog transitions consume internal messages and return a new state."""
from dataclasses import replace
from math import hypot

from ..messages import (ButtonAction, FocusLostMessage, KeyboardAction, KeyboardMessage,
                        MouseButton, MouseButtonMessage, MouseMotionMessage, QuitMessage,
                        ScrollMessage, WindowResizeMessage)
from .DialogView import active_form, contains, form_columns, hit_test, regions, sentence_rows


class DialogUpdater:
    def __init__(self, catalog, validate, sentence):
        self.catalog, self.validate, self.sentence = catalog, validate, sentence

    def _select(self, state, identity, part=None):
        selected = next((p for p in state.phrases if p['id'] == identity), None)
        if selected is None:
            return replace(state, selected=None, selected_part=None, form_scroll=0)
        part = part if part is not None and selected['parts'][part][0] == 'adj' else None
        state = replace(state, selected=identity, selected_part=part)
        lexeme, current = active_form(state, self.catalog)
        forms = dict(state.choices)[lexeme]
        size = max(1, (regions(state)['forms'][3]-52)//46)*form_columns(state)
        start = forms.index(current)//size*size
        row = next(row for phrase, _, row, _, _ in sentence_rows(state) if phrase['id'] == identity)
        return replace(state, selected=identity, form_scroll=start, sentence_scroll=row)

    def _form(self, state, form):
        phrases = []
        for phrase in state.phrases:
            if phrase['id'] == state.selected:
                if state.selected_part is not None:
                    words = list(phrase['parts'])
                    kind, _, lexeme = words[state.selected_part]
                    words[state.selected_part] = (kind, form, lexeme)
                    phrase = {**phrase, 'parts': tuple(words)}
                else:
                    generated = self.catalog[phrase['lexeme']]['parts'][form]
                    words = tuple((kind, word, '') for kind, word in generated)
                    adjectives = tuple(part for part in phrase['parts'] if part[0] == 'adj')
                    index = next((i for i, part in enumerate(words) if part[0] == 'n'), len(words))
                    phrase = {**phrase, 'form': form, 'parts': words[:index]+adjectives+words[index:]}
            phrases.append(phrase)
        return replace(state, phrases=tuple(phrases), command=None)

    def _insert(self, state, lexeme, target=None):
        entry = self.catalog[lexeme]
        if entry['kind'] == 'adjective':
            if target is not None and target[0] not in ('part', 'phrase'):
                return replace(state, message='Drop this word inside a noun phrase.')
            identity = target[1] if target and target[0] in ('part', 'phrase') else state.selected
            phrase = next((p for p in state.phrases if p['id'] == identity), None)
            if phrase is None or self.catalog[phrase['lexeme']]['kind'] != 'noun':
                return replace(state, message='Drop this word inside a noun phrase.')
            if any(part[0] == 'adj' and part[2] == lexeme for part in phrase['parts']):
                return replace(state, message='That word is already in this phrase.')
            parts = list(phrase['parts'])
            index = target[2] if target and target[0] == 'part' else next(i for i, p in enumerate(parts) if p[0] == 'n')
            parts.insert(index, ('adj', entry['canonical'], lexeme))
            phrases = tuple({**p, 'parts': tuple(parts)} if p['id'] == identity else p for p in state.phrases)
            return self._select(replace(state, phrases=phrases, command=None, message='Arrange the words inside the phrase.'), identity, index)
        form = entry['canonical']
        phrase = {'id': state.next_id, 'lexeme': lexeme, 'form': form,
                  'parts': tuple((kind, word, '') for kind, word in entry['parts'][form])}
        phrases = list(state.phrases)
        index = next((i for i, p in enumerate(phrases) if target and target[0] in ('phrase', 'part') and p['id'] == target[1]), len(phrases))
        phrases.insert(index, phrase)
        state = replace(state, phrases=tuple(phrases), next_id=state.next_id+1,
                        command=None, message='Choose a form, or keep the highlighted one.')
        return self._select(state, phrase['id'])

    def _drop(self, state, source, target):
        if target is None:
            return state
        if source[0] == 'inventory':
            if target[0] not in ('sentence', 'part', 'phrase'):
                return state
            return self._insert(state, source[1], target)
        identity = source[1]
        if target[0] == 'inventory':
            return self._remove(state, source)
        if target[0] not in ('sentence', 'phrase', 'part'):
            return state
        phrases = list(state.phrases)
        origin = next(p for p in phrases if p['id'] == identity)
        if source[0] == 'part' and target[0] in ('part', 'phrase'):
            destination = next(p for p in phrases if p['id'] == target[1])
            part = origin['parts'][source[2]]
            if (destination['id'] != identity and part[0] == 'adj'
                    and any(p[0] == 'adj' and p[2] == part[2] for p in destination['parts'])):
                return replace(state, message='That word is already in this phrase.')
            if destination['id'] == identity or (part[0] == 'adj' and self.catalog[destination['lexeme']]['kind'] == 'noun'):
                old_parts = list(origin['parts'])
                old_parts.pop(source[2])
                new_parts = old_parts if destination['id'] == identity else list(destination['parts'])
                index = target[2] if target[0] == 'part' else len(new_parts)
                if destination['id'] == identity and target[0] == 'part' and source[2] < index:
                    index -= 1
                new_parts.insert(index, part)
                phrases = tuple({**p, 'parts': tuple(new_parts)} if p['id'] == destination['id'] else
                                {**p, 'parts': tuple(old_parts)} if p['id'] == identity else p for p in phrases)
                return self._select(replace(state, phrases=phrases, command=None), destination['id'])
        if source[0] == 'part' and origin['parts'][source[2]][0] == 'adj':
            return replace(state, message='Keep this word inside a noun phrase.')
        if target[0] in ('phrase', 'part') and target[1] == identity:
            return self._select(state, identity)
        phrases.remove(origin)
        index = next((i for i, p in enumerate(phrases) if target[0] in ('phrase', 'part') and p['id'] == target[1]), len(phrases))
        phrases.insert(index, origin)
        return self._select(replace(state, phrases=tuple(phrases), command=None), identity)

    def _remove(self, state, target):
        identity = target[1]
        phrase = next(p for p in state.phrases if p['id'] == identity)
        if target[0] == 'part' and phrase['parts'][target[2]][0] == 'adj':
            parts = phrase['parts'][:target[2]]+phrase['parts'][target[2]+1:]
            phrases = tuple({**p, 'parts': parts} if p['id'] == identity else p for p in state.phrases)
        else:
            phrases = tuple(p for p in state.phrases if p['id'] != identity)
        return replace(state, phrases=phrases, selected=None, selected_part=None, command=None, sentence_scroll=0, pressed=None, dragging=False)

    def _speak(self, state):
        if not state.phrases:
            return replace(state, message='Make a sentence first.', command=None)
        command = self.validate(state.phrases, self.catalog)
        text = self.sentence(state.phrases)
        return replace(state, command=command, transcript=(*state.transcript[-7:], (text, command is not None)),
                       message='Sentence understood.' if command is not None else 'Try changing the forms or word order.')

    def _activate(self, state, target):
        if target is None:
            return state
        kind = target[0]
        if kind == 'inventory':
            return self._insert(state, target[1])
        if kind in ('phrase', 'part'):
            return self._select(state, target[1], target[2] if kind == 'part' else None)
        if kind == 'form':
            return self._form(state, target[1])
        if kind == 'close':
            return replace(state, selected=None, selected_part=None)
        if kind == 'clear':
            return replace(state, phrases=(), selected=None, selected_part=None, command=None, sentence_scroll=0,
                           message='Drag a word into the sentence.')
        if kind == 'speak':
            return self._speak(state)
        if kind == 'inventory-scroll':
            visible = max(1, (regions(state)['inventory'][3]-52)//44)
            return replace(state, inventory_scroll=max(0, min(len(self.catalog)-visible, state.inventory_scroll+target[1])))
        if kind == 'form-scroll' and state.selected is not None:
            lexeme, _ = active_form(state, self.catalog)
            count = len(dict(state.choices)[lexeme])
            size = max(1, (regions(state)['forms'][3]-52)//46)*form_columns(state)
            return replace(state, form_scroll=max(0, min((count-1)//size*size, state.form_scroll+target[1])))
        return state

    def update(self, state, message):
        if isinstance(message, QuitMessage):
            return replace(state, running=False)
        if isinstance(message, WindowResizeMessage):
            return replace(state, viewport=message.size, pressed=None, dragging=False,
                           form_scroll=0, sentence_scroll=0)
        if isinstance(message, FocusLostMessage):
            return replace(state, pressed=None, dragging=False)
        if isinstance(message, MouseMotionMessage):
            pointer = tuple(message.position)
            dragging = state.dragging or bool(state.pressed and state.pressed[0] in ('inventory', 'phrase', 'part')
                                              and hypot(pointer[0]-state.press_position[0], pointer[1]-state.press_position[1]) > 5)
            return replace(state, pointer=pointer, dragging=dragging)
        if isinstance(message, MouseButtonMessage) and message.position is not None:
            pointer = tuple(message.position)
            target = hit_test(state, self.catalog, pointer)
            if message.button == MouseButton.RIGHT and message.action == ButtonAction.PRESS:
                return self._remove(state, target) if target and target[0] in ('part', 'phrase') else state
            if message.button != MouseButton.LEFT:
                return state
            if message.action == ButtonAction.PRESS:
                return replace(state, pressed=target, pointer=pointer, press_position=pointer, dragging=False)
            source, dragging = state.pressed, state.dragging
            state = replace(state, pressed=None, dragging=False, pointer=pointer)
            return self._drop(state, source, target) if source and dragging else self._activate(state, target) if source == target else state
        if isinstance(message, ScrollMessage):
            point = tuple(message.position) if message.position is not None else state.pointer
            offset = -int(message.offset.y)
            area = regions(state)
            if contains(area['inventory'], point):
                return self._activate(state, ('inventory-scroll', offset))
            if contains(area['forms'], point):
                return self._activate(state, ('form-scroll', offset*form_columns(state)))
            if contains(area['sentence'], point):
                rows = sentence_rows(state)
                maximum = rows[-1][2] if rows else 0
                return replace(state, sentence_scroll=max(0, min(maximum, state.sentence_scroll+offset)))
        if isinstance(message, KeyboardMessage) and message.action == KeyboardAction.PRESS:
            if message.key == 'escape':
                return replace(state, selected=None, selected_part=None, pressed=None, dragging=False)
            if message.key in ('return', 'enter'):
                return self._speak(state)
            if state.selected is not None:
                if message.key in ('delete', 'backspace'):
                    return self._remove(state, ('phrase', state.selected))
                if message.key in ('left', 'right'):
                    phrases = list(state.phrases)
                    index = next(i for i, p in enumerate(phrases) if p['id'] == state.selected)
                    destination = max(0, min(len(phrases)-1, index+(-1 if message.key == 'left' else 1)))
                    phrases.insert(destination, phrases.pop(index))
                    return replace(state, phrases=tuple(phrases), command=None)
        return state
