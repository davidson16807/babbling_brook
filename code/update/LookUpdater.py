# HUMAN VETTED

from dataclasses import replace

from pyglm import glm

pi = 3.141592653589793238462643383279


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
        return replace(
            camera,
            raw_azimuth=v.x,
            raw_elevation=v.y,
            look_azimuth=v.x%(2*pi),
            look_elevation=v.y,
        )
