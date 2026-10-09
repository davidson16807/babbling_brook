"""Find the waypoint that another waypoint leads to.

A waypoint with a `CardinalWaypoint` component leads to the zone in that direction
(`ZoneDirections`) and arrives at the waypoint facing back, with the same color code.
A waypoint with a `Waypoint` component leads to the zone that shares a
`ZoneAdjacency` of its color code and arrives at that zone's waypoint of the same color code.
Invalid data is reported with a warning and yields no destination.
"""


DIRECTIONS = {'n': 'north', 's': 'south', 'e': 'east', 'w': 'west'}
OPPOSITES = {'n': 's', 's': 'n', 'e': 'w', 'w': 'e'}


class WaypointQuery:
    def destination(self, waypoint, placements, maps,
                    waypoints, cardinal_waypoints, zone_adjacencies, zone_directions):
        """The placement of the waypoint that `waypoint` leads to, or None if there is none."""
        origin = placements[waypoint]
        archetype, zone = origin.archetype, origin.zone
        if archetype in cardinal_waypoints:
            if archetype in waypoints:
                print(f"Warning: waypoint archetype {archetype!r} is both a cardinal and a colorcoded waypoint; "
                      "treating it as cardinal")
            cardinal = cardinal_waypoints[archetype]
            if cardinal.direction not in DIRECTIONS:
                print(f"Warning: cardinal waypoint {archetype!r} has unknown direction {cardinal.direction!r}")
                return None
            directions = zone_directions.get(zone)
            destination = getattr(directions, DIRECTIONS[cardinal.direction]) if directions is not None else None
            if destination is None:
                print(f"Warning: zone {zone!r} has no zone to the {DIRECTIONS[cardinal.direction]} "
                      f"for waypoint {waypoint!r}")
                return None
            colorcode = cardinal.colorcode
            arrivals = {key for key, item in cardinal_waypoints.items()
                        if item.direction == OPPOSITES[cardinal.direction] and item.colorcode == colorcode}
        elif archetype in waypoints:
            colorcode = waypoints[archetype].colorcode
            adjacency = zone_adjacencies.get((zone, colorcode))
            if adjacency is None:
                print(f"Warning: zone {zone!r} has no adjacency with colorcode {colorcode!r} "
                      f"for waypoint {waypoint!r}")
                return None
            destination = adjacency.zone2 if adjacency.zone1 == zone else adjacency.zone1
            arrivals = {key for key, item in waypoints.items() if item.colorcode == colorcode}
        else:
            print(f"Warning: {waypoint!r} is not a waypoint")
            return None
        if destination not in maps:
            print(f"Warning: waypoint {waypoint!r} leads to zone {destination!r}, which has no map")
            return None
        candidates = sorted(key for key, item in placements.items()
                            if item.zone == destination and item.archetype in arrivals)
        if not candidates:
            print(f"Warning: waypoint {waypoint!r} leads to zone {destination!r}, "
                  f"which has no matching waypoint with colorcode {colorcode!r}")
            return None
        if len(candidates) > 1:
            print(f"Warning: waypoint {waypoint!r} leads to zone {destination!r}, "
                  f"which has several matching waypoints {candidates}; using {candidates[0]!r}")
        return placements[candidates[0]]
