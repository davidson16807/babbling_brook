# HUMAN VETTED

from dataclasses import replace
from ..messages import MouseMotionMessage

class HemisphereLookUpdater:
    def update(self, camera, message):
        if isinstance(message, MouseMotionMessage):
            return replace(camera, raw_azimuth=camera.raw_azimuth - message.offset.x * .01)
        return camera
