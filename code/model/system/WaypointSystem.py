"""Move characters between zones through the non-door waypoints they enter.

Where a waypoint leads is decided by the injected `WaypointQuery`; doors are
activated by interaction instead (see `ExplorerUpdater`).
"""
from dataclasses import replace

from pyglm import glm


class WaypointSystem:
    def __init__(self, waypoint_query):
        self.waypoint_query = waypoint_query

    def step(self, before, after, characters, billboards, boxes, maps,
             waypoints, cardinal_waypoints, zone_adjacencies, zone_directions):
        """Send each character that has just entered a non-door waypoint through it.

        `before` and `after` are placements at the start and end of a step; a waypoint
        the character already intersected at the start does not activate again, so a
        character arriving on a waypoint must leave it before it can return.
        """
        placements = after
        for entity in characters:
            if entity not in after:
                continue
            waypoint = self.entered(entity, before, after, billboards, boxes, waypoints, cardinal_waypoints)
            if waypoint is None:
                continue
            arrival = self.waypoint_query.destination(
                waypoint, placements, maps, waypoints, cardinal_waypoints, zone_adjacencies, zone_directions)
            if arrival is not None:
                placements = {**placements, entity: replace(
                    placements[entity], zone=arrival.zone, position=glm.vec3(arrival.position))}
        return placements

    def entered(self, entity, before, after, billboards, boxes, waypoints, cardinal_waypoints):
        """The nearest non-door waypoint in `entity`'s zone that it intersects in `after` but not in `before`."""
        placement = after[entity]
        previous = before.get(entity)
        entered = []
        for key, item in after.items():
            if key == entity or item.zone != placement.zone:
                continue
            is_waypoint = item.archetype in cardinal_waypoints or (
                item.archetype in waypoints and not waypoints[item.archetype].door)
            if not is_waypoint:
                continue
            if not self.intersects(placement, item, billboards, boxes):
                continue
            if (previous is not None and previous.zone == item.zone
                    and self.intersects(previous, item, billboards, boxes)):
                continue
            entered.append((glm.distance(placement.position.xy, item.position.xy), key))
        return min(entered)[1] if entered else None

    def intersects(self, body, waypoint, billboards, boxes):
        """Whether a body's billboard cylinder meets a waypoint's billboard cylinder or box."""
        # A body without a billboard component is treated as a point.
        shape = billboards.get(body.archetype)
        radius, height = (shape.radius, shape.height) if shape is not None else (0.0, 0.0)
        bottom, top = body.position.z, body.position.z + height
        xy = body.position.xy
        billboard = billboards.get(waypoint.archetype)
        if (billboard is not None
                and glm.distance(xy, waypoint.position.xy) <= radius + billboard.radius
                and bottom <= waypoint.position.z + billboard.height and top >= waypoint.position.z):
            return True
        box = boxes.get(waypoint.archetype)
        if box is not None:
            bounds = box.bounds(waypoint.position)
            if (glm.distance(xy, glm.clamp(xy, bounds.minimum.xy, bounds.maximum.xy)) <= radius
                    and bottom <= bounds.maximum.z and top >= bounds.minimum.z):
                return True
        return False
