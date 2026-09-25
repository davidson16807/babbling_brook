# HUMAN VETTED

from dataclasses import replace

from pyglm import glm

from ..messages import MouseMotionMessage, KeyboardMessage

pi = 3.141592653589793238462643383279
oo = float('inf')


class LockedLookUpdater:
    def __init__(self, vector_updater, azimuths, elevations):
        self.vector_updater = vector_updater
        self.azimuths = azimuths
        self.elevations = elevations

    def update(self, camera, message):
        v = self.vector_updater.update(
            glm.vec2(camera.raw_azimuth, camera.raw_elevation), message)
        v.x %= 2*pi
        return replace(
            camera,
            raw_azimuth=v.x,
            raw_elevation=v.y,
            look_azimuth=(
                min(self.azimuths, key=lambda az: abs(az-v.x))
                if self.azimuths else v.x
            ),
            look_elevation=(
                min(self.elevations, key=lambda el: abs(el-v.y))
                if self.elevations else v.y
            ),
        )


class DirectLookUpdater:
    def __init__(self, vector_updater):
        self.vector_updater = vector_updater

    def update(self, camera, message):
        v = self.vector_updater.update(
            glm.vec2(camera.raw_azimuth, camera.raw_elevation), message)
        v.x %= 2*pi
        return replace(
            camera,
            raw_azimuth=v.x,
            raw_elevation=v.y,
            look_azimuth=v.x,
            look_elevation=v.y,
        )


class BoundedVectorUpdater:
    def __init__(self, vector_updater, x0=-oo, x1=oo, y0=-oo, y1=oo):
        self.vector_updater = vector_updater
        self.x0 = x0
        self.x1 = x1
        self.y0 = y0
        self.y1 = y1

    def update(self, state, message):
        v = self.vector_updater.update(state, message)
        return glm.vec2(
            max(self.x0, min(self.x1, v.x)),
            max(self.y0, min(self.y1, v.y)),
        )


class VectorMouseUpdater:
    def __init__(self, magnitude):
        self.magnitude = magnitude

    def update(self, state, message):
        return (
            state + self.magnitude * message.offset
            if isinstance(message, MouseMotionMessage) else state
        )


class VectorKeysUpdater:
    def __init__(self, up, left, down, right, magnitude=1):
        self.up = up
        self.left = left
        self.down = down
        self.right = right
        self.magnitude = glm.vec2(magnitude)

    def update(self, state, message) -> glm.vec2:
        return state + self.magnitude * glm.vec2(
            int(self.right == message.key) - int(self.left == message.key),
            int(self.up == message.key) - int(self.down == message.key),
        ) if isinstance(message, KeyboardMessage) else state
