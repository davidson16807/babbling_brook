from collections import defaultdict
from dataclasses import replace


class ActionRegistry:
    def __init__(self, actions):
        self.actions = dict(actions)

    def apply(self, action, model, entity):
        if action not in self.actions:
            return replace(model, message=f"Unknown action: {action}")
        return self.actions[action](model, entity)


def collect(item):
    def action(model, entity):
        inventory = defaultdict(int, model.inventory)
        inventory['player', item] += 1
        instances = replace(model.instances, **{name: {key: value for key, value in getattr(model.instances, name).items() if key != entity}
            for name in ('placements', 'physics', 'characters')})
        return replace(model, instances=instances, inventory=inventory, message=f"Picked up {item}. Press Tab to see your inventory.")
    return action


def greet(model, entity):
    return replace(model, message="Welcome to Babbling Brook! Try collecting an apple nearby.")
