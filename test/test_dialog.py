"""Dialog GUI checks. Model, layout, and updater tests need no Pygame display or GL.

    python -m unittest discover -s test -v
    BB_TEST_GL=1 python -m unittest discover -s test -v   # also renders the harness offscreen
"""
import os
import sys
import tempfile
import unittest
from dataclasses import replace
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if 'babbling_brook' not in sys.modules:
    spec = spec_from_file_location('babbling_brook', ROOT / 'code' / '__init__.py',
                                   submodule_search_locations=[str(ROOT / 'code')])
    package = module_from_spec(spec)
    sys.modules['babbling_brook'] = package
    spec.loader.exec_module(package)

from pyglm import glm

from babbling_brook.codec.LexiconCodec import LexiconStringCodec
from babbling_brook.dialog.DialogDemo import DialogDemo
from babbling_brook.dialog.DialogLayout import (ButtonTarget, DialogLayout, DialogMetrics,
                                                InventoryTarget, PanelTarget, WordTarget)
from babbling_brook.dialog.DialogState import DialogState, Dismissed, Spoke
from babbling_brook.dialog.DialogUpdater import DialogUpdater
from babbling_brook.dialog.playmat import find, phrase_sequence, sequence_modifiers, tokens
from babbling_brook.messages import (FocusLostMessage, KeyboardAction, KeyboardMessage,
                                     ScrollMessage, WindowResizeMessage)
from babbling_brook.model.Lexicon import Token
from babbling_brook.view.TextMetrics import MonospaceTextMetrics

LEXICON = LexiconStringCodec().decode((ROOT / 'data' / 'lexicon' / 'english.tsv').read_text(encoding='utf-8'))


def key(name):
    return KeyboardMessage(name, KeyboardAction.PRESS)


class DialogTestCase(unittest.TestCase):
    def setUp(self):
        self.layout = DialogLayout(LEXICON, DialogMetrics(MonospaceTextMetrics()))
        self.updater = DialogUpdater(self.layout)
        self.demo = DialogDemo(self.updater)
        self.state = DialogState(seed=7)

    def said(self, state):
        return ' '.join(tokens(state.playmat, LEXICON))

    def word(self, state, lexeme):
        return next(word for word in state.playmat if word.lexeme == lexeme)

    def hold(self, state, target, destination):
        """Press, then move far enough to drag, without releasing."""
        start = self.demo.point(state, target)
        state, _ = self.demo.send(state, [self.demo.press(start), self.demo.move(start + glm.vec2(8, 0)),
                                          self.demo.move(destination)])
        return state


class LexiconTests(unittest.TestCase):
    def test_round_trip(self):
        codec = LexiconStringCodec()
        self.assertEqual(codec.decode(codec.encode(LEXICON)), LEXICON)

    def test_homonyms_keep_every_interpretation(self):
        give = LEXICON.lexemes['give']
        self.assertEqual(len({inflection.text for inflection in give.inflections}), len(give.inflections))
        self.assertEqual(len(give.inflection('give').tagpoints), 5)
        self.assertEqual(sum(len(inflection.tagpoints) for inflection in give.inflections), 54)
        # English is generated as the native gloss language; plain "you" replaces "all of you".
        self.assertNotIn('all of you', [i.text for i in LEXICON.lexemes['pronoun'].inflections])
        self.assertGreaterEqual(len(LEXICON.lexemes['pronoun'].inflection('you').tagpoints), 4)

    def test_noun_phrase_tokens(self):
        inflection = LEXICON.lexemes['boy'].inflection('to the boy')
        self.assertEqual([token.part for token in inflection.tokens], ['adposition', 'det', 'n'])
        self.assertEqual(inflection.head, 2)

    def test_rejects_unknown_default(self):
        text = (ROOT / 'data' / 'lexicon' / 'english.tsv').read_text(encoding='utf-8')
        with self.assertRaises(KeyError):
            LexiconStringCodec().decode(text.replace('give\tverb\tgive\tgive', 'give\tverb\tgive\tgiven'))


class PlaymatTests(unittest.TestCase):
    def test_sequence_round_trip(self):
        from babbling_brook.dialog.DialogState import Modifier, Word
        inflection = LEXICON.lexemes['ball'].inflection('to the ball')
        modifiers = (Modifier(Word(1, 'big', 'big'), -3), Modifier(Word(2, 'red', 'red'), -1),
                     Modifier(Word(3, 'big', 'bigger'), 1))
        sequence = phrase_sequence(inflection, modifiers)
        self.assertEqual([item.text if isinstance(item, Token) else item.word.inflection for item in sequence],
                         ['big', 'to', 'the', 'red', 'ball', 'bigger'])
        self.assertEqual(sequence_modifiers(sequence, inflection.head), modifiers)

    def test_offsets_clamp_to_shorter_phrases(self):
        from babbling_brook.dialog.DialogState import Modifier, Word
        sequence = phrase_sequence(LEXICON.lexemes['ball'].inflection('balls'),
                                   (Modifier(Word(1, 'big', 'big'), -3),))
        self.assertEqual([getattr(item, 'text', None) for item in sequence], [None, 'balls'])


class LayoutTests(DialogTestCase):
    def test_inventory_lists_pronouns_then_alphabetical(self):
        shown = [box.target.lexeme for box in self.layout.layout(self.state).boxes
                 if isinstance(box.target, InventoryTarget)]
        self.assertEqual(shown, ['pronoun', 'ball', 'big', 'boy', 'dog', 'give', 'house', 'red', 'talk', 'walk'])

    def test_boxes_stay_in_viewport_and_playmat_words_do_not_overlap(self):
        state = self.demo.mockup(self.state)
        layout = self.layout.layout(state)
        for box in layout.boxes:
            x, y, w, h = box.rect
            self.assertTrue(0 <= x and 0 <= y and x + w <= 1280 and y + h <= 720, box)
        words = sorted(layout.anchors[WordTarget(word.id)] for word in state.playmat)
        for (x0, _, w0, _), (x1, _, _, _) in zip(words, words[1:]):
            self.assertLessEqual(x0 + w0, x1)

    def test_grid_order_is_fixed_per_lexeme_and_session(self):
        ball, boy = LEXICON.lexemes['ball'], LEXICON.lexemes['boy']
        order = self.layout.options(7, ball)
        self.assertEqual(order, self.layout.options(7, ball))
        self.assertEqual(sorted(order), sorted(i.text for i in ball.inflections))
        self.assertNotEqual(order, self.layout.options(8, ball))
        self.assertNotEqual([text.replace('ball', '') for text in order],
                            [text.replace('boy', '') for text in self.layout.options(7, boy)])

    def test_new_grid_scrolls_to_its_selection(self):
        state, id = self.demo.place(self.state, 'ball', 'the ball')
        state = replace(state, grid=None)
        state, _ = self.demo.click(state, WordTarget(id))
        selected = [box for box in self.layout.layout(state).boxes if box.style == 'cell-selected']
        self.assertEqual([box.text for box in selected], ['the ball'])


class UpdaterTests(DialogTestCase):
    def test_mockup_statement(self):
        state = self.demo.mockup(self.state)
        self.assertEqual(self.said(state), 'you give the red ball to the boy')
        self.assertEqual(state.grid, self.word(state, 'ball').id)

    def test_drop_places_default_inflection_and_opens_its_grid(self):
        state, id = self.demo.place(self.state, 'give')
        self.assertEqual(find(state.playmat, id).inflection, 'give')
        self.assertEqual(state.grid, id)
        self.assertEqual(state.next_id, id + 1)

    def test_choosing_keeps_grid_open_and_escape_keeps_the_choice(self):
        state, id = self.demo.place(self.state, 'give', 'gave')
        self.assertEqual(state.grid, id)
        state, outcome = self.updater.update(state, key('escape'))
        self.assertIsNone(outcome)
        self.assertIsNone(state.grid)
        self.assertEqual(find(state.playmat, id).inflection, 'gave')

    def test_close_button_collapses_the_grid(self):
        state, id = self.demo.place(self.state, 'give', 'gave')
        state, _ = self.demo.click(state, ButtonTarget('close'))
        self.assertIsNone(state.grid)
        self.assertEqual(find(state.playmat, id).inflection, 'gave')

    def test_reorder_by_dragging(self):
        state, _ = self.demo.place(self.state, 'pronoun', 'you')
        state, give = self.demo.place(state, 'give')
        before_you = self.demo.left_of(state, lambda box: box.target == WordTarget(self.word(state, 'pronoun').id))
        state, _ = self.demo.drag(state, WordTarget(give), before_you)
        self.assertEqual(self.said(state), 'give you')

    def test_adjectives_only_drop_onto_common_noun_phrases(self):
        state, _ = self.demo.place(self.state, 'pronoun', 'you')
        state, _ = self.demo.place(state, 'give')
        for destination in (self.demo.playmat_end(state),
                            self.demo.point(state, WordTarget(self.word(state, 'give').id)),
                            self.demo.point(state, WordTarget(self.word(state, 'pronoun').id))):
            dropped, _ = self.demo.drag(state, InventoryTarget('red'), destination)
            self.assertEqual(self.said(dropped), 'you give')
            self.assertEqual(dropped.next_id, state.next_id)

    def test_adjective_stays_by_its_noun_when_reinflected(self):
        state, ball = self.demo.place(self.state, 'ball', 'the ball')
        noun = lambda box: box.style == 'token' and box.text == 'ball'
        state, _ = self.demo.place(state, 'red', destination=self.demo.left_of(state, noun))
        self.assertEqual(self.said(state), 'the red ball')
        state, _ = self.demo.click(state, WordTarget(ball))
        state, _ = self.demo.choose(state, ball, 'to the ball')
        self.assertEqual(self.said(state), 'to the red ball')
        state, _ = self.demo.choose(state, ball, 'balls')
        self.assertEqual(self.said(state), 'red balls')

    def test_adjective_order_is_the_players(self):
        state, ball = self.demo.place(self.state, 'ball', 'a ball')
        noun = lambda box: box.style == 'token' and box.text == 'ball'
        article = lambda box: box.style == 'token' and box.text == 'a'
        state, _ = self.demo.place(state, 'red', destination=self.demo.left_of(state, noun))
        state, _ = self.demo.place(state, 'big', destination=self.demo.left_of(state, article))
        self.assertEqual(self.said(state), 'big a red ball')  # wrong, but the player's to make
        big = next(m.word.id for m in self.word(state, 'ball').modifiers if m.word.lexeme == 'big')
        # While dragged, "big" leaves the phrase and the rest closes up, so aim at the
        # layout as it is during the drag, as a player would.
        held = self.hold(state, WordTarget(big), glm.vec2(700, 100))
        red = [box for box in self.layout.layout(held).boxes
               if box.text == 'red' and box.style == 'chip' and box.target is not None][-1]
        destination = glm.vec2(red.rect[0] + 1, red.rect[1] + red.rect[3] / 2)
        state, _ = self.demo.send(held, [self.demo.move(destination), self.demo.release(destination)])
        self.assertEqual(self.said(state), 'a big red ball')

    def test_drag_to_inventory_removes(self):
        state = self.demo.mockup(self.state)
        state, _ = self.demo.drag(state, WordTarget(self.word(state, 'ball').id), glm.vec2(60, 300))
        self.assertEqual(self.said(state), 'you give to the boy')
        self.assertIsNone(state.grid)  # the removed word's grid closes with it

    def test_dropping_nowhere_cancels(self):
        state = self.demo.mockup(self.state)
        state, _ = self.demo.drag(state, WordTarget(self.word(state, 'give').id), glm.vec2(700, 100))
        self.assertEqual(self.said(state), 'you give the red ball to the boy')

    def test_small_motion_is_a_click_not_a_drag(self):
        state, id = self.demo.place(self.state, 'give')
        state = replace(state, grid=None)
        point = self.demo.point(state, WordTarget(id))
        state, _ = self.demo.send(state, [self.demo.press(point), self.demo.move(point + glm.vec2(2, 1)),
                                          self.demo.release(point + glm.vec2(2, 1))])
        self.assertIsNone(state.drag)
        self.assertEqual(state.grid, id)

    def test_focus_loss_and_escape_cancel_a_drag(self):
        state = self.demo.mockup(self.state)
        for message in (FocusLostMessage(), key('escape')):
            held = self.hold(state, WordTarget(self.word(state, 'give').id), glm.vec2(60, 300))
            self.assertIsNotNone(held.drag)
            cancelled, outcome = self.updater.update(held, message)
            self.assertIsNone(cancelled.drag)
            self.assertIsNone(outcome)
            self.assertEqual(cancelled.playmat, state.playmat)

    def test_escape_closes_innermost_then_dismisses(self):
        state = self.demo.mockup(self.state)
        state, outcome = self.updater.update(state, key('escape'))
        self.assertIsNone(state.grid)
        self.assertIsNone(outcome)
        state, outcome = self.updater.update(state, key('escape'))
        self.assertIsInstance(outcome, Dismissed)

    def test_talk(self):
        state, outcome = self.updater.update(self.state, key('e'))
        self.assertIsNone(outcome)
        self.assertTrue(state.message)
        state = self.demo.mockup(self.state)
        spoken, outcome = self.updater.update(state, key('e'))
        self.assertEqual(outcome, Spoke(state.playmat))
        clicked, outcomes = self.demo.click(state, ButtonTarget('talk'))
        self.assertEqual(outcomes, [Spoke(state.playmat)])

    def test_delete_removes_selected_word(self):
        state = self.demo.mockup(self.state)
        state, _ = self.updater.update(state, key('delete'))
        self.assertEqual(self.said(state), 'you give to the boy')

    def test_inventory_scroll_is_clamped(self):
        state = replace(self.state, viewport=(1280, 300))
        inventory = self.demo.center(self.demo.box(state, lambda box: box.target == PanelTarget('inventory')).rect)
        limit = self.layout.layout(state).limits['inventory']
        self.assertGreater(limit, 0)
        for _ in range(limit + 5):
            state, _ = self.updater.update(state, ScrollMessage(glm.vec2(0, -1), position=inventory))
        self.assertEqual(state.inventory_scroll, limit)
        state, _ = self.updater.update(state, ScrollMessage(glm.vec2(0, 1), position=inventory))
        self.assertEqual(state.inventory_scroll, limit - 1)
        shown = [box for box in self.layout.layout(state).boxes if isinstance(box.target, InventoryTarget)]
        self.assertTrue(all(box.rect[1] + box.rect[3] <= 300 - 16 for box in shown))

    def test_resize(self):
        state, _ = self.updater.update(self.state, WindowResizeMessage((800, 600)))
        self.assertEqual(state.viewport, (800, 600))


class MessageQueueTests(unittest.TestCase):
    def test_button_messages_carry_position(self):
        try:
            import pygame
        except ImportError:
            self.skipTest('pygame is not installed')
        from babbling_brook.adapter.PygameMessageQueue import PygameMessageQueue
        from babbling_brook.messages import ButtonAction, MouseButton, MouseButtonMessage
        event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(12, 34))
        [message] = PygameMessageQueue(lambda: [event]).poll()
        self.assertEqual(message, MouseButtonMessage(MouseButton.LEFT, ButtonAction.PRESS,
                                                     message.modifiers, glm.vec2(12, 34)))


@unittest.skipUnless(os.environ.get('BB_TEST_GL'), 'set BB_TEST_GL=1 to render with EGL')
class HarnessRenderTests(unittest.TestCase):
    def test_demo_renders(self):
        import pygame
        from babbling_brook.dialog.dialog import BACKGROUND, main
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'dialog.png'
            main(['--headless', '--demo', '--seed', '7', '--frames', '2', '--screenshot', str(path)])
            pygame.init()
            image = pygame.image.load(str(path))
            self.assertEqual(image.get_size(), (1280, 720))
            background = tuple(round(channel * 255) for channel in BACKGROUND)
            # The world area stays clear; the playmat and inventory are drawn.
            self.assertEqual(tuple(image.get_at((700, 100)))[:3], background)
            self.assertNotEqual(tuple(image.get_at((700, 680)))[:3], background)
            self.assertNotEqual(tuple(image.get_at((40, 400)))[:3], background)


if __name__ == '__main__':
    unittest.main()
