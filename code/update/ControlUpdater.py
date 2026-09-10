# HUMAN VETTED

from dataclasses import replace
from ..messages import (KeyboardMessage, KeyboardAction, MouseButtonMessage, ButtonAction, FocusLostMessage)
from ..model.ControlState import ControlState

class ControlUpdater:
    def update(self, control_state, message):
        if isinstance(message, FocusLostMessage):
            return ControlState()
        if isinstance(message, KeyboardMessage):
            keys = control_state.pressed_keys
            if message.action == KeyboardAction.PRESS:
                keys = keys | {message.key}
            elif message.action == KeyboardAction.RELEASE:
                keys = keys - {message.key}
            return replace(control_state, pressed_keys=frozenset(keys))
        if isinstance(message, MouseButtonMessage):
            buttons = control_state.pressed_mouse_buttons
            if message.action == ButtonAction.PRESS:
                buttons = buttons | {message.button}
            else:
                buttons = buttons - {message.button}
            return replace(control_state, pressed_mouse_buttons=frozenset(buttons))
        return control_state
