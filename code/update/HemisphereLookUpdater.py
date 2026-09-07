from dataclasses import replace
from ..messages import MouseMotionMessage


class HemisphereLookUpdater:
    def update(self, model, message):
        if isinstance(message, MouseMotionMessage):
            return replace(model, raw_azimuth=model.raw_azimuth - message.offset.x * .01)
        return model
