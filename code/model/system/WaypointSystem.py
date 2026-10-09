"""Move characters between zones through waypoints.

A waypoint with a `CardinalWaypoint` component leads to the zone in that direction
(`ZoneDirections`) and arrives at the waypoint facing back, with the same color code.
A waypoint with a `Waypoint` component leads to the zone that shares a
`ZoneAdjacency` of its color code and arrives at that zone's waypoint of the same color code.
Doors are activated by interaction; other waypoints are activated on entry.
Invalid data is reported with a warning and leaves placements unchanged.
"""
from dataclasses import replace

from pyglm import glm


DIRECTIONS = {'n': 'north', 's': 'south', 'e': 'east', 'w': 'west'}
OPPOSITES = {'n': 's', 's': 'n', 'e': 'w', 'w': 'e'}


class WaypointSystem:
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
            if waypoint is not None:
                placements = self.travel(entity, waypoint, placements, maps,
                                         waypoints, cardinal_waypoints, zone_adjacencies, zone_directions)
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

    def travel(self, entity, waypoint, placements, maps,
               waypoints, cardinal_waypoints, zone_adjacencies, zone_directions):
        """Place `entity` on the waypoint that `waypoint` leads to, in the adjacent zone."""
        origin = placements[waypoint]
        archetype, zone = origin.archetype, origin.zone
        if archetype in cardinal_waypoints:
            if archetype in waypoints:
                print(f"Warning: waypoint archetype {archetype!r} is both a cardinal and a colorcoded waypoint; "
                      "treating it as cardinal")
            cardinal = cardinal_waypoints[archetype]
            if cardinal.direction not in DIRECTIONS:
                print(f"Warning: cardinal waypoint {archetype!r} has unknown direction {cardinal.direction!r}")
                return placements
            directions = zone_directions.get(zone)
            destination = getattr(directions, DIRECTIONS[cardinal.direction]) if directions is not None else None
            if destination is None:
                print(f"Warning: zone {zone!r} has no zone to the {DIRECTIONS[cardinal.direction]} "
                      f"for waypoint {waypoint!r}")
                return placements
            colorcode = cardinal.colorcode
            arrivals = {key for key, item in cardinal_waypoints.items()
                        if item.direction == OPPOSITES[cardinal.direction] and item.colorcode == colorcode}
        elif archetype in waypoints:
            colorcode = waypoints[archetype].colorcode
            adjacency = zone_adjacencies.get((zone, colorcode))
            if adjacency is None:
                print(f"Warning: zone {zone!r} has no adjacency with colorcode {colorcode!r} "
                      f"for waypoint {waypoint!r}")
                return placements
            destination = adjacency.zone2 if adjacency.zone1 == zone else adjacency.zone1
            arrivals = {key for key, item in waypoints.items() if item.colorcode == colorcode}
        else:
            print(f"Warning: {waypoint!r} is not a waypoint")
            return placements
        if destination not in maps:
            print(f"Warning: waypoint {waypoint!r} leads to zone {destination!r}, which has no map")
            return placements
        candidates = sorted(key for key, item in placements.items()
                            if item.zone == destination and item.archetype in arrivals)
        if not candidates:
            print(f"Warning: waypoint {waypoint!r} leads to zone {destination!r}, "
                  f"which has no matching waypoint with colorcode {colorcode!r}")
            return placements
        if len(candidates) > 1:
            print(f"Warning: waypoint {waypoint!r} leads to zone {destination!r}, "
                  f"which has several matching waypoints {candidates}; using {candidates[0]!r}")
        arrival = placements[candidates[0]]
        return {**placements,
                entity: replace(placements[entity], zone=destination, position=glm.vec3(arrival.position))}
