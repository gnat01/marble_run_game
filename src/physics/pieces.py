from __future__ import annotations

from dataclasses import dataclass
from math import degrees, radians
from typing import ClassVar

import pymunk

from .world import PhysicsWorld


@dataclass(frozen=True)
class RectVariant:
    name: str
    width: float
    height: float


@dataclass(frozen=True)
class CircleVariant:
    name: str
    radius: float


RECT_VARIANTS: list[RectVariant] = [
    RectVariant("Rect S1", 110, 14),
    RectVariant("Rect S2", 140, 16),
    RectVariant("Rect M1", 170, 18),
    RectVariant("Rect M2", 210, 20),
    RectVariant("Rect L1", 260, 24),
]

CIRCLE_VARIANTS: list[CircleVariant] = [
    CircleVariant("Circle S", 18),
    CircleVariant("Circle M", 28),
    CircleVariant("Circle L", 40),
]


class RectReflector:
    """Static rectangular reflector."""

    _next_id: ClassVar[int] = 1

    def __init__(
        self,
        world: PhysicsWorld,
        variant: RectVariant,
        position: tuple[float, float],
        angle_degrees: float,
    ) -> None:
        self.id = RectReflector._next_id
        RectReflector._next_id += 1
        self._world = world
        self.variant = variant
        self.body = pymunk.Body(body_type=pymunk.Body.STATIC)
        self.body.position = position
        self.body.angle = radians(angle_degrees)
        self.shape = world.configure_shape(
            pymunk.Poly.create_box(self.body, (variant.width, variant.height))
        )
        world.space.add(self.body, self.shape)

    @property
    def angle_degrees(self) -> float:
        return degrees(self.body.angle)

    def set_position(self, position: tuple[float, float]) -> None:
        self.body.position = position
        self._world.reindex_body(self.body)

    def rotate(self, delta_degrees: float) -> None:
        self.body.angle += radians(delta_degrees)
        self._world.reindex_body(self.body)


class CircleReflector:
    """Static circular bumper."""

    _next_id: ClassVar[int] = 1

    def __init__(
        self,
        world: PhysicsWorld,
        variant: CircleVariant,
        position: tuple[float, float],
    ) -> None:
        self.id = CircleReflector._next_id
        CircleReflector._next_id += 1
        self._world = world
        self.variant = variant
        self.body = pymunk.Body(body_type=pymunk.Body.STATIC)
        self.body.position = position
        self.shape = world.configure_shape(pymunk.Circle(self.body, variant.radius))
        world.space.add(self.body, self.shape)

    def set_position(self, position: tuple[float, float]) -> None:
        self.body.position = position
        self._world.reindex_body(self.body)
