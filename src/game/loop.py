from __future__ import annotations

from typing import Callable

import pygame

from ..config import FIXED_TIMESTEP_SECONDS, TARGET_FPS
from .state import GameState


class GameLoop:
    """Fixed-timestep loop with decoupled update and render calls."""

    def __init__(
        self,
        state: GameState,
        update_fn: Callable[[float], None],
        render_fn: Callable[[], None],
    ) -> None:
        self._state = state
        self._update_fn = update_fn
        self._render_fn = render_fn
        self._clock = pygame.time.Clock()

    def tick(self) -> None:
        frame_seconds = self._clock.tick(TARGET_FPS) / 1000.0
        self._state.accumulator += min(frame_seconds, 0.25)

        while self._state.accumulator >= FIXED_TIMESTEP_SECONDS:
            self._update_fn(FIXED_TIMESTEP_SECONDS)
            self._state.accumulator -= FIXED_TIMESTEP_SECONDS

        self._render_fn()
        self._state.frame_count += 1
