from __future__ import annotations

from dataclasses import dataclass

import pymunk

from ..config import (
    PLAYFIELD_BOTTOM,
    PLAYFIELD_LEFT,
    PLAYFIELD_RIGHT,
    RECEPTACLE_BOTTOM_OFFSET,
    RECEPTACLE_HEIGHT,
    RECEPTACLE_WALL_THICKNESS,
    RECEPTACLE_WIDTH,
)
from .world import PhysicsWorld


@dataclass(frozen=True)
class ReceptacleVariant:
    name: str
    width: float
    height: float


RECEPTACLE_VARIANTS: list[ReceptacleVariant] = [
    ReceptacleVariant("Shallow", 270, 63),
    ReceptacleVariant("Pocket", 170, 105),
    ReceptacleVariant("Deep", 145, 135),
    ReceptacleVariant("Wide", 320, 48),
]


class Receptacle:
    """Movable U-shaped receptacle near the bottom of the board."""

    def __init__(self, world: PhysicsWorld) -> None:
        self._world = world
        self.variant_name = "Shallow"
        self.width = RECEPTACLE_WIDTH
        self.height = RECEPTACLE_HEIGHT
        self.wall_thickness = RECEPTACLE_WALL_THICKNESS
        self.body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        self.body.position = (
            (PLAYFIELD_LEFT + PLAYFIELD_RIGHT) * 0.5,
            PLAYFIELD_BOTTOM - RECEPTACLE_BOTTOM_OFFSET,
        )
        self.segments: list[pymunk.Segment] = []
        world.space.add(self.body)
        self._rebuild_segments()

    @property
    def center_x(self) -> float:
        return float(self.body.position.x)

    @property
    def bottom_y(self) -> float:
        return float(self.body.position.y)

    @property
    def left_x(self) -> float:
        return self.center_x - self.width * 0.5

    @property
    def right_x(self) -> float:
        return self.center_x + self.width * 0.5

    @property
    def top_y(self) -> float:
        return self.bottom_y - self.height

    def set_position(self, center_x: float, bottom_y: float) -> None:
        self.body.position = (center_x, bottom_y)
        self._world.reindex_body(self.body)

    def apply_variant(self, variant: ReceptacleVariant) -> None:
        self.variant_name = variant.name
        self.width = variant.width
        self.height = variant.height
        self._rebuild_segments()

    def contains_point(self, x: float, y: float, margin: float = 0.0) -> bool:
        return (
            self.left_x + margin <= x <= self.right_x - margin
            and self.top_y + margin <= y <= self.bottom_y - margin
        )

    def contains_marble_center(self, x: float, y: float, radius: float) -> bool:
        horizontal_margin = radius * 0.9
        vertical_margin_top = radius * 1.15
        vertical_margin_bottom = radius * 0.6
        return (
            self.left_x + horizontal_margin <= x <= self.right_x - horizontal_margin
            and self.top_y + vertical_margin_top <= y <= self.bottom_y - vertical_margin_bottom
        )

    def hit_test(self, x: float, y: float, tolerance: float = 16.0) -> bool:
        return (
            self.left_x - tolerance <= x <= self.right_x + tolerance
            and self.top_y - tolerance <= y <= self.bottom_y + tolerance
        )

    def _rebuild_segments(self) -> None:
        if self.segments:
            self._world.space.remove(*self.segments)
        self.segments = [
            self._world.configure_shape(
                pymunk.Segment(
                    self.body,
                    (-self.width * 0.5, 0.0),
                    (self.width * 0.5, 0.0),
                    RECEPTACLE_WALL_THICKNESS,
                )
            ),
            self._world.configure_shape(
                pymunk.Segment(
                    self.body,
                    (-self.width * 0.5, -self.height),
                    (-self.width * 0.5, 0.0),
                    RECEPTACLE_WALL_THICKNESS,
                )
            ),
            self._world.configure_shape(
                pymunk.Segment(
                    self.body,
                    (self.width * 0.5, -self.height),
                    (self.width * 0.5, 0.0),
                    RECEPTACLE_WALL_THICKNESS,
                )
            ),
        ]
        self._world.space.add(*self.segments)
        self._world.reindex_body(self.body)
