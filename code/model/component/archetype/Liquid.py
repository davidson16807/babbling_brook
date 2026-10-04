# HUMAN VETTED

from dataclasses import dataclass


@dataclass(frozen=True)
class Liquid:
    top_texture1: str
    top_texture2: str
    side_texture: str
    freezing_temperature: float
    frozen_texture: str
    viscosity: float
    is_unpassable: bool = False
