from collections import defaultdict
from copy import copy
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
        inventory[item] += 1
        map_ = copy(model.map)
        map_.static_objects = {key: value for key, value in model.map.static_objects.items() if key != entity}
        instances = replace(model.instances, **{name: {key: value for key, value in getattr(model.instances, name).items() if key != entity}
            for name in ('positionables', 'archetyped', 'physics', 'characters')})
        return replace(model, map=map_, instances=instances, inventory=inventory, message=f"Picked up {item}. Press Tab to see your inventory.")
    return action


def greet(model, entity):
    return replace(model, message="Welcome to Babbling Brook! Try collecting an apple nearby.")


def default_actions():
    return ActionRegistry({'collect_apple': collect('apple'), 'collect_stick': collect('stick'), 'greet': greet})
