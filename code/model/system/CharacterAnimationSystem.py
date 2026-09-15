# HUMAN VETTED

from dataclasses import replace

class CharacterAnimationSystem:
    def step(self, characters, seconds):
        return {entity: replace(state, elapsed=state.elapsed + seconds) for entity, state in characters.items()}
