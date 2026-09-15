"""Only this module interprets Pygame events, key codes, or mouse-button codes."""
from collections.abc import Callable, Iterable

from pyglm import glm
import pygame

from ..messages import (ButtonAction, FocusLostMessage, KeyboardMessage,
                        KeyboardAction, KeyboardModifiers, MouseButton, MouseButtonMessage,
                        MouseMotionMessage, QuitMessage, ScrollMessage,
                        WindowResizeMessage)


def _modifiers(bits: int) -> KeyboardModifiers:
    result = KeyboardModifiers.NONE
    for mask, flag in ((pygame.KMOD_SHIFT, KeyboardModifiers.SHIFT),
                       (pygame.KMOD_CTRL, KeyboardModifiers.CTRL),
                       (pygame.KMOD_ALT, KeyboardModifiers.ALT),
                       (pygame.KMOD_GUI, KeyboardModifiers.SUPER),
                       (pygame.KMOD_CAPS, KeyboardModifiers.CAPS),
                       (pygame.KMOD_NUM, KeyboardModifiers.NUM)):
        if bits & mask:
            result |= flag
    return result


'''
"MessageQueue" is a proper object oriented class 
that seals off event driven functionality within python,
making it easier to guarantee the elimination of side effects
within other parts of code.
It encapsulates a queue of "messages" 
(as understood within the context of Model/View/Update architecture),
and a set of event callback functions.
The queue is updated by the event callback functions,
which can be registered and deregistered to a python window 
using the `register()` and `deregister()` methods.
A deep copy of the queue can be requested using poll(),
but there is no way for the queue to be modified by external code. 

MessageQueue also encapsulates state that's relevant to providing enhanced 
descriptions of control state at a given moment,
such as tracking the change in the position of a mouse since the last poll.
'''
class PygameMessageQueue:
    def __init__(self, events: Callable[[], Iterable] = pygame.event.get):
        self.events = events
        self.modifiers = KeyboardModifiers.NONE

    def poll(self) -> list:
        return [message for event in self.events()
                if (message := self._translate(event)) is not None]

    def _translate(self, event):
        if event.type == pygame.QUIT:
            return QuitMessage()
        if event.type in (pygame.KEYDOWN, pygame.KEYUP):
            self.modifiers = _modifiers(event.mod)
            if getattr(event, "repeat", False):
                return None
            action = KeyboardAction.PRESS if event.type == pygame.KEYDOWN else KeyboardAction.RELEASE
            aliases = {pygame.K_LSHIFT: "shift", pygame.K_RSHIFT: "right shift"}
            return KeyboardMessage(aliases.get(event.key, pygame.key.name(event.key)), action, self.modifiers)
        if event.type == pygame.MOUSEMOTION:
            return MouseMotionMessage(glm.vec2(event.pos), glm.vec2(event.rel))
        if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
            button = {1: MouseButton.LEFT, 2: MouseButton.MIDDLE, 3: MouseButton.RIGHT}.get(event.button)
            if button is not None:
                action = ButtonAction.PRESS if event.type == pygame.MOUSEBUTTONDOWN else ButtonAction.RELEASE
                return MouseButtonMessage(button, action, self.modifiers)
        if event.type == pygame.MOUSEWHEEL:
            return ScrollMessage(glm.vec2(event.x, event.y))
        if event.type in (pygame.WINDOWRESIZED, pygame.WINDOWSIZECHANGED):
            return WindowResizeMessage((max(1, event.x), max(1, event.y)))
        if event.type == pygame.WINDOWFOCUSLOST:
            self.modifiers = KeyboardModifiers.NONE
            return FocusLostMessage()
        return None
