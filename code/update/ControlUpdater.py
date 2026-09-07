from dataclasses import replace
from ..messages import (KeyboardMessage, KeyboardAction, MouseButtonMessage, ButtonAction, FocusLostMessage)
from ..model.ControlState import ControlState


class ControlUpdater:
    def update(self, model, message):
        if isinstance(message, FocusLostMessage):
            return ControlState()
        if isinstance(message, KeyboardMessage):
            keys = model.pressed_keys
            if message.action == KeyboardAction.PRESS:
                keys = keys | {message.key}
            elif message.action == KeyboardAction.RELEASE:
                keys = keys - {message.key}
            return replace(model, pressed_keys=frozenset(keys))
        if isinstance(message, MouseButtonMessage):
            buttons = model.pressed_mouse_buttons
            buttons = buttons | {message.button} if message.action == ButtonAction.PRESS else buttons - {message.button}
            return replace(model, pressed_mouse_buttons=frozenset(buttons))
        return model
