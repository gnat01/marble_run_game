from __future__ import annotations

from math import cos, radians, sin

import pymunk

from ..config import MARBLE_MASS, MARBLE_RADIUS, MARBLE_SPAWN_X, MARBLE_SPAWN_Y
from .world import PhysicsWorld


class Marble:
    """Dynamic marble body and shape."""

    def __init__(self, world: PhysicsWorld) -> None:
        moment = pymunk.moment_for_circle(MARBLE_MASS, 0, MARBLE_RADIUS)
        self.body = pymunk.Body(MARBLE_MASS, moment)
        self.body.position = (MARBLE_SPAWN_X, MARBLE_SPAWN_Y)

        self.shape = world.configure_shape(pymunk.Circle(self.body, MARBLE_RADIUS))
        world.space.add(self.body, self.shape)

    @property
    def position(self) -> tuple[float, float]:
        return self.body.position

    @property
    def velocity(self) -> tuple[float, float]:
        return self.body.velocity

    def set_position(self, position: tuple[float, float]) -> None:
        self.body.position = position
        self.body.velocity = (0.0, 0.0)
        self.body.angular_velocity = 0.0
        self.body.force = (0.0, 0.0)
        self.body.torque = 0.0

    def set_velocity_from_polar(self, speed: float, angle_degrees: float) -> None:
        angle_radians = radians(angle_degrees)
        vx = speed * cos(angle_radians)
        vy = -speed * sin(angle_radians)
        self.body.velocity = (vx, vy)

    def set_velocity(self, velocity: tuple[float, float]) -> None:
        self.body.velocity = velocity
