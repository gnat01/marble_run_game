from __future__ import annotations

import pymunk

from ..config import (
    PHYSICS_DAMPING,
    PHYSICS_DEFAULT_FRICTION,
    PHYSICS_GLOBAL_RESTITUTION,
    PHYSICS_GRAVITY_X,
    PHYSICS_GRAVITY_Y,
    PHYSICS_SOLVER_ITERATIONS,
    PLAYFIELD_BOTTOM,
    PLAYFIELD_LEFT,
    PLAYFIELD_RIGHT,
    PLAYFIELD_TOP,
)


class PhysicsWorld:
    """Wrapper around the shared 2D physics simulation space."""

    def __init__(self) -> None:
        self._space = pymunk.Space()
        self._space.gravity = (PHYSICS_GRAVITY_X, PHYSICS_GRAVITY_Y)
        self._space.damping = PHYSICS_DAMPING
        self._space.iterations = PHYSICS_SOLVER_ITERATIONS
        self._default_friction = PHYSICS_DEFAULT_FRICTION
        self._global_restitution = PHYSICS_GLOBAL_RESTITUTION
        self._boundaries = self._create_boundaries()

    @property
    def space(self) -> pymunk.Space:
        return self._space

    @property
    def gravity(self) -> tuple[float, float]:
        return self._space.gravity

    @property
    def damping(self) -> float:
        return self._space.damping

    @property
    def default_friction(self) -> float:
        return self._default_friction

    @property
    def global_restitution(self) -> float:
        return self._global_restitution

    @property
    def boundaries(self) -> list[pymunk.Segment]:
        return self._boundaries

    def configure_shape(self, shape: pymunk.Shape) -> pymunk.Shape:
        """Apply shared V1 material defaults to a collider shape."""
        shape.friction = self._default_friction
        shape.elasticity = self._global_restitution
        return shape

    def step(self, dt: float) -> None:
        self._space.step(dt)

    def reindex_body(self, body: pymunk.Body) -> None:
        self._space.reindex_shapes_for_body(body)

    def _create_boundaries(self) -> list[pymunk.Segment]:
        static_body = self._space.static_body
        segments = [
            pymunk.Segment(
                static_body,
                (PLAYFIELD_LEFT, PLAYFIELD_TOP),
                (PLAYFIELD_LEFT, PLAYFIELD_BOTTOM),
                4,
            ),
            pymunk.Segment(
                static_body,
                (PLAYFIELD_RIGHT, PLAYFIELD_TOP),
                (PLAYFIELD_RIGHT, PLAYFIELD_BOTTOM),
                4,
            ),
            pymunk.Segment(
                static_body,
                (PLAYFIELD_LEFT, PLAYFIELD_TOP),
                (PLAYFIELD_RIGHT, PLAYFIELD_TOP),
                4,
            ),
        ]
        configured_segments = [self.configure_shape(segment) for segment in segments]
        self._space.add(*configured_segments)
        return configured_segments
