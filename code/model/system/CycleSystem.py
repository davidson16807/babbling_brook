"""Advance cycle components without mutating their input collection."""


class CycleSystem:
    def step(self, cycles, minutes):
        return {key: cycle + minutes / cycle.period for key, cycle in cycles.items()}
