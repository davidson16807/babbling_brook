"""Exercise the real language runtime, dialog state and event boundary."""
from dataclasses import replace
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from random import Random
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
if 'babbling_brook' not in sys.modules:
    spec = spec_from_file_location('babbling_brook', ROOT/'code/__init__.py', submodule_search_locations=[str(ROOT/'code')])
    module = module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

from pyglm import glm
from babbling_brook.adapter.LanguagesLibrary import LanguagesLibrary
from babbling_brook.dialog.DialogState import DialogState
from babbling_brook.dialog.DialogUpdater import DialogUpdater
from babbling_brook.dialog.DialogView import layout, sentence_rows
from babbling_brook.messages import (ButtonAction, FocusLostMessage, KeyboardAction,
    KeyboardMessage, MouseButton, MouseButtonMessage, MouseMotionMessage, ScrollMessage, WindowResizeMessage)


class DialogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.language = LanguagesLibrary().import_module('babbling_brook.inflection.EnglishDialog')
        cls.catalog = cls.language.build_catalog()
        cls.updater = DialogUpdater(cls.catalog, cls.language.validate, cls.language.sentence)

    def state(self, seed=7):
        choices = []
        for lexeme, entry in self.catalog.items():
            forms = list(entry['forms'])
            Random(f'{seed}:{lexeme}').shuffle(forms)
            choices.append((lexeme, tuple(forms)))
        return DialogState(choices=tuple(choices))

    def make(self, pairs):
        state = self.state()
        for lexeme, form in pairs:
            state = self.updater._insert(state, lexeme)
            state = self.updater._form(state, form)
        return state

    def point(self, state, target):
        box = next(box for box, action in layout(state, self.catalog) if action == target)
        x, y, w, h = box.rect
        return glm.vec2(x+w/2, y+4 if target[0] == 'phrase' else y+h/2)

    def click(self, state, target):
        point = self.point(state, target)
        for action in (ButtonAction.PRESS, ButtonAction.RELEASE):
            state = self.updater.update(state, MouseButtonMessage(MouseButton.LEFT, action, position=point))
        return state

    def drag(self, state, source, target):
        start, finish = self.point(state, source), self.point(state, target)
        state = self.updater.update(state, MouseButtonMessage(MouseButton.LEFT, ButtonAction.PRESS, position=start))
        state = self.updater.update(state, MouseMotionMessage(finish, finish-start, frozenset({MouseButton.LEFT})))
        return self.updater.update(state, MouseButtonMessage(MouseButton.LEFT, ButtonAction.RELEASE, position=finish))

    def test_real_inflections_keep_homonyms_and_dictstore(self):
        entry = self.catalog['give']
        self.assertEqual(set(entry['forms']), {'give', 'gives'})
        self.assertGreater(len(entry['forms']['give']), 1)
        self.assertIn('gives', str(entry['inflections'][entry['forms']['gives'][0]]))
        self.assertIn('to the boys', self.catalog['boy']['forms'])
        for entry in self.catalog.values():
            self.assertFalse(any('❔' in text or '—' in text for text in entry['forms']))

    def test_agreement_and_pronoun_case(self):
        for subject, verb, valid in [('I','walk',True),('he','walks',True),('they','walk',True),
                                     ('you','walk',True),('he','walk',False),('me','walk',False),('I','walks',False)]:
            with self.subTest(subject=subject, verb=verb):
                state = self.make([('I', subject), ('walk', verb)])
                self.assertEqual(self.language.validate(state.phrases, self.catalog) is not None, valid)

    def test_plural_and_preposition(self):
        state = self.make([('boy','the boys'),('walk','walk'),('house','to a house')])
        self.assertIsNotNone(self.language.validate(state.phrases, self.catalog))
        state = self.updater._form(state, 'a house')
        self.assertIsNone(self.language.validate(state.phrases, self.catalog))

    def test_give_adjective_and_word_order(self):
        state = self.make([('I','I'),('give','give'),('ball','the ball'),('boy','to the boy')])
        state = self.updater._insert(state, 'red', ('part',3,1))
        self.assertEqual(self.language.sentence(state.phrases), 'I give the red ball to the boy')
        command = self.language.validate(state.phrases, self.catalog)
        self.assertEqual(command['arguments'][1]['adjectives'], ('red',))
        state = self.updater._drop(state, ('part',3,1), ('phrase',3))
        self.assertEqual(self.language.sentence(state.phrases), 'I give the ball red to the boy')
        self.assertIsNone(self.language.validate(state.phrases, self.catalog))
        state = replace(state, phrases=(state.phrases[1],state.phrases[0],*state.phrases[2:]))
        self.assertIsNone(self.language.validate(state.phrases, self.catalog))

    def test_drag_add_change_form_escape_and_immutability(self):
        before = self.state()
        after = self.drag(before, ('inventory','boy'), ('sentence',))
        self.assertEqual(before.phrases, ())
        self.assertEqual(after.selected, 1)
        after = self.click(after, ('form','the boys'))
        after = self.updater.update(after, KeyboardMessage('escape', KeyboardAction.PRESS))
        self.assertIsNone(after.selected)
        self.assertEqual(after.phrases[0]['form'], 'the boys')
        self.assertEqual(before.choices, after.choices)

    def test_adjective_confinement_and_grid(self):
        state = self.make([('ball','the ball')])
        rejected = self.drag(state, ('inventory','red'), ('sentence',))
        self.assertEqual(rejected.phrases, state.phrases)
        state = self.drag(state, ('inventory','red'), ('part',1,1))
        self.assertEqual(state.selected_part, 1)
        self.assertIn(('form','red'), [target for _,target in layout(state,self.catalog)])
        state = self.click(state, ('part',1,2))
        self.assertIsNone(state.selected_part)
        self.assertIn('the red ball', [box.text for box,target in layout(state,self.catalog) if target and target[0]=='form'])

    def test_drag_phrase_reorder_and_keyboard_removal(self):
        state = self.make([('I','I'),('walk','walk')])
        state = self.drag(state, ('phrase',2), ('phrase',1))
        self.assertEqual(self.language.sentence(state.phrases), 'walk I')
        state = self.updater.update(state, KeyboardMessage('right', KeyboardAction.PRESS))
        self.assertEqual(self.language.sentence(state.phrases), 'I walk')
        state = self.updater.update(state, KeyboardMessage('delete', KeyboardAction.PRESS))
        self.assertEqual(self.language.sentence(state.phrases), 'I')

    def test_speak_feedback_and_no_stale_command(self):
        state = self.make([('I','I'),('walk','walk')])
        state = self.click(state, ('speak',))
        self.assertIsNotNone(state.command)
        self.assertEqual(state.transcript[-1], ('I walk', True))
        state = self.updater._form(state, 'walks')
        self.assertIsNone(state.command)
        state = self.updater.update(state, KeyboardMessage('return', KeyboardAction.PRESS))
        self.assertEqual(state.transcript[-1], ('I walks', False))

    def test_focus_loss_and_resize(self):
        state = self.make([('I','I')])
        state = replace(state, pressed=('inventory','boy'), dragging=True)
        state = self.updater.update(state, FocusLostMessage())
        self.assertIsNone(state.pressed)
        self.assertFalse(state.dragging)
        resized = self.updater.update(state, WindowResizeMessage((980,680)))
        self.assertEqual(state.phrases,resized.phrases)
        for box,target in layout(resized,self.catalog):
            if target:
                x,y,w,h=box.rect
                self.assertTrue(0<=x and 0<=y and x+w<=980 and y+h<=680, (target,box.rect))

    def test_sentence_scrolling_is_bounded(self):
        state = self.make([('house','to the houses')]*12)
        state = self.updater.update(state, ScrollMessage(glm.vec2(0,-100), position=glm.vec2(300,630)))
        self.assertEqual(state.sentence_scroll, sentence_rows(state)[-1][2])
        self.assertIn(('phrase',12), [target for _,target in layout(state,self.catalog)])

    def test_shuffle_stability(self):
        self.assertNotEqual(self.state(7).choices,self.state(8).choices)
        self.assertEqual(self.state(7).choices,self.state(7).choices)

    def test_pygame_event_boundary(self):
        import pygame
        from babbling_brook.adapter.PygameMessageQueue import PygameMessageQueue
        pygame.display.init()
        try:
            state=self.state()
            point=tuple(map(int,self.point(state,('inventory','I'))))
            events=[pygame.event.Event(kind,button=1,pos=point) for kind in (pygame.MOUSEBUTTONDOWN,pygame.MOUSEBUTTONUP)]
            for message in PygameMessageQueue(lambda:events).poll():
                state=self.updater.update(state,message)
            self.assertEqual(self.language.sentence(state.phrases),'I')
        finally:
            pygame.display.quit()

if __name__=='__main__':
    unittest.main()
