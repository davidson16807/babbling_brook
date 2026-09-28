"""Advance cycle components without mutating their input collection."""


class CycleSystem:
    def step(self, cycles, seconds):
        return {key: cycle + seconds / cycle.period for key, cycle in cycles.items()}
