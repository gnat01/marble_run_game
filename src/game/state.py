from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..data.leaderboard import LocalLeaderboard
    from ..physics.world import PhysicsWorld
    from ..physics.marble import Marble
    from ..physics.pieces import CircleReflector, CircleVariant, RectReflector, RectVariant
    from ..physics.receptacle import Receptacle


@dataclass
class GameState:
    """Mutable runtime state for the prototype."""

    is_running: bool = True
    accumulator: float = 0.0
    frame_count: int = 0
    should_reset: bool = False
    debug_messages: list[str] = field(default_factory=list)
    physics_world: PhysicsWorld | None = None
    marble: Marble | None = None
    receptacle: Receptacle | None = None
    rect_reflectors: list[RectReflector] = field(default_factory=list)
    circle_reflectors: list[CircleReflector] = field(default_factory=list)
    selected_rect_id: int | None = None
    selected_circle_id: int | None = None
    palette_selection: tuple[str, object] | None = None
    log_elapsed_ms: float = 0.0
    simulation_active: bool = False
    speed_value: float = 0.0
    angle_value: float = 0.0
    dragging_speed_slider: bool = False
    dragging_angle_slider: bool = False
    attempt_result: int | None = None
    entered_receptacle: bool = False
    settle_elapsed_seconds: float = 0.0
    safe_receptacle_frames: int = 0
    result_recorded: bool = False
    leaderboard: LocalLeaderboard | None = None
    ball_selected: bool = False
    ball_support_normal: tuple[float, float] | None = None
    last_launch_ball_position: tuple[float, float] | None = None
    last_launch_ball_support_normal: tuple[float, float] | None = None
    selected_receptacle: bool = False
    drag_target_type: str | None = None
    drag_target_id: int | None = None
    drag_offset_x: float = 0.0
    drag_offset_y: float = 0.0
    drag_moved: bool = False
    drag_start_mouse_x: float = 0.0
    drag_start_mouse_y: float = 0.0
    palette_scroll_y: float = 0.0
