import os
import unittest

os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT', '1')
try:
    import pygame
except ImportError:
    pygame = None

from babbling_brook.messages import (
    ButtonAction, FocusLostMessage, KeyboardAction, KeyboardModifiers, MouseButton,
)


@unittest.skipIf(pygame is None, 'Install the render extra to check the Pygame adapter')
class MessageAdapterTests(unittest.TestCase):
    def test_key_and_mouse_actions_use_their_own_internal_enums(self):
        from babbling_brook.adapters.PygameMessageQueue import PygameMessageQueue
        events = [
            pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e, mod=pygame.KMOD_CTRL),
            pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=2),
            pygame.event.Event(pygame.KEYUP, key=pygame.K_e, mod=0),
        ]
        key_down, mouse_down, key_up = PygameMessageQueue(lambda: events).poll()
        self.assertIs(key_down.action, KeyboardAction.PRESS)
        self.assertEqual(key_down.modifiers, KeyboardModifiers.CTRL)
        self.assertIs(mouse_down.action, ButtonAction.PRESS)
        self.assertIs(mouse_down.button, MouseButton.MIDDLE)
        self.assertEqual(mouse_down.modifiers, KeyboardModifiers.CTRL)
        self.assertIs(key_up.action, KeyboardAction.RELEASE)

    def test_focus_loss_clears_modifiers_and_repeats_are_filtered(self):
        from babbling_brook.adapters.PygameMessageQueue import PygameMessageQueue
        events = [
            pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e, mod=pygame.KMOD_CTRL, repeat=True),
            pygame.event.Event(pygame.WINDOWFOCUSLOST),
            pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=2),
        ]
        focus, mouse = PygameMessageQueue(lambda: events).poll()
        self.assertIsInstance(focus, FocusLostMessage)
        self.assertEqual(mouse.modifiers, KeyboardModifiers.NONE)
