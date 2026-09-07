from dataclasses import replace
from math import floor, pi


class ClampedAzimuthUpdater:
    def __init__(self, source):
        self.source = source

    def update(self, model, message):
        model = self.source.update(model, message)
        angle = pi / 4 + floor((model.raw_azimuth - pi / 4) / (pi / 2) + .5) * pi / 2
        return replace(model, look_azimuth=angle % (2 * pi))
