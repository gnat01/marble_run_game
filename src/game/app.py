from __future__ import annotations

import json
from math import cos, radians, sin

import pygame
import pymunk

from ..config import (
    BACKGROUND_COLOR,
    BOARD_FILL_COLOR,
    BALL_ON_REFLECTOR_CLEARANCE,
    BOARD_LINE_COLOR,
    DIAGNOSTIC_LOG_INTERVAL_MS,
    DIAGNOSTIC_LOG_PATH,
    LAUNCH_BUTTON_HEIGHT,
    LAUNCH_BUTTON_WIDTH,
    LEADERBOARD_PATH,
    MARBLE_COLOR,
    MARBLE_DEFAULT_ANGLE_DEGREES,
    MARBLE_DEFAULT_SPEED,
    MARBLE_MAX_ANGLE_DEGREES,
    MARBLE_MAX_SPEED,
    MARBLE_MIN_ANGLE_DEGREES,
    MARBLE_MIN_SPEED,
    MUTED_TEXT_COLOR,
    PALETTE_BORDER_COLOR,
    PALETTE_FILL_COLOR,
    PALETTE_WIDTH,
    PLAYFIELD_BOTTOM,
    PLAYFIELD_LEFT,
    PLAYFIELD_RIGHT,
    PLAYFIELD_TOP,
    RECEPTACLE_SAFE_FRAMES_REQUIRED,
    RECEPTACLE_SETTLE_SPEED_THRESHOLD,
    RECEPTACLE_SETTLE_TIME_SECONDS,
    RECEPTACLE_VERTICAL_STOP_THRESHOLD,
    RECEPTACLE_COLOR,
    REFLECTOR_COLOR,
    SLIDER_HEIGHT,
    SLIDER_KNOB_RADIUS,
    SLIDER_WIDTH,
    TEXT_COLOR,
    WINDOW_HEIGHT,
    WINDOW_TITLE,
    WINDOW_WIDTH,
)
from ..data.leaderboard import LocalLeaderboard
from ..physics.marble import Marble
from ..physics.pieces import CIRCLE_VARIANTS, RECT_VARIANTS, CircleReflector, RectReflector
from ..physics.receptacle import RECEPTACLE_VARIANTS, Receptacle
from .loop import GameLoop
from .state import GameState
from ..physics.world import PhysicsWorld


class MarbleRunApp:
    """Minimal application shell for the prototype."""

    def __init__(self) -> None:
        pygame.init()
        self._screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption(WINDOW_TITLE)
        self._font = pygame.font.SysFont(None, 24)
        self._small_font = pygame.font.SysFont(None, 20)
        self._tiny_font = pygame.font.SysFont(None, 18)
        self._state = GameState()
        self._state.leaderboard = LocalLeaderboard(LEADERBOARD_PATH)
        self._rebuild_world()
        self._loop = GameLoop(
            state=self._state,
            update_fn=self._update,
            render_fn=self._render,
        )

    def run(self) -> None:
        try:
            while self._state.is_running:
                self._handle_events()
                self._loop.tick()
        finally:
            pygame.quit()

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._state.is_running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self._state.is_running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                if event.mod & pygame.KMOD_SHIFT:
                    self._state.should_reset = True
                else:
                    self._retry_attempt()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._handle_left_mouse_down(event.pos)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                self._handle_right_mouse_down(event.pos)
            elif event.type == pygame.MOUSEWHEEL:
                self._handle_mouse_wheel(event.y)
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self._state.dragging_speed_slider = False
                self._state.dragging_angle_slider = False
                self._finish_drag_or_click(event.pos)
            elif event.type == pygame.MOUSEMOTION:
                self._handle_mouse_motion(event)

    def _update(self, dt: float) -> None:
        if self._state.should_reset:
            self._state.accumulator = 0.0
            self._state.should_reset = False
            self._rebuild_world()

        assert self._state.physics_world is not None
        assert self._state.marble is not None
        if self._state.simulation_active:
            self._state.physics_world.step(dt)
            self._update_attempt_state(dt)
        self._record_attempt_result_if_needed()
        self._state.log_elapsed_ms += dt * 1000.0
        if self._state.log_elapsed_ms >= DIAGNOSTIC_LOG_INTERVAL_MS:
            self._write_runtime_log()
            self._state.log_elapsed_ms = 0.0

    def _render(self) -> None:
        self._screen.fill(BACKGROUND_COLOR)
        self._draw_playfield_background()
        self._draw_board()
        self._draw_receptacle()
        self._draw_reflectors()
        self._draw_marble()
        self._draw_palette()

        title_surface = self._font.render("Marble Run Prototype", True, TEXT_COLOR)
        self._screen.blit(title_surface, (24, 24))
        hint_surface = self._small_font.render("Use the Ball tool or click the ball to position it. Left click rotates selected rectangles; right click rotates the other way. R retries, Shift+R clears all.", True, MUTED_TEXT_COLOR)
        self._screen.blit(hint_surface, (24, 58))
        self._draw_launch_controls()
        self._draw_leaderboard_summary()

        pygame.display.flip()

    def _rebuild_world(self) -> None:
        physics_world = PhysicsWorld()
        self._state.physics_world = physics_world
        self._state.receptacle = Receptacle(physics_world)
        self._state.marble = Marble(physics_world)
        self._state.rect_reflectors = []
        self._state.circle_reflectors = []
        self._state.selected_rect_id = None
        self._state.selected_circle_id = None
        self._state.palette_selection = None
        self._state.simulation_active = False
        self._state.speed_value = MARBLE_DEFAULT_SPEED
        self._state.angle_value = MARBLE_DEFAULT_ANGLE_DEGREES
        self._state.dragging_speed_slider = False
        self._state.dragging_angle_slider = False
        self._state.attempt_result = None
        self._state.entered_receptacle = False
        self._state.settle_elapsed_seconds = 0.0
        self._state.safe_receptacle_frames = 0
        self._state.result_recorded = False
        self._state.ball_selected = False
        self._state.ball_support_normal = None
        self._state.last_launch_ball_position = None
        self._state.last_launch_ball_support_normal = None
        self._state.selected_receptacle = False
        self._state.drag_target_type = None
        self._state.drag_target_id = None
        self._state.drag_offset_x = 0.0
        self._state.drag_offset_y = 0.0
        self._state.drag_moved = False
        self._state.palette_scroll_y = 0.0
        self._write_runtime_log()

    def _draw_playfield_background(self) -> None:
        board_rect = pygame.Rect(
            PLAYFIELD_LEFT,
            PLAYFIELD_TOP,
            PLAYFIELD_RIGHT - PLAYFIELD_LEFT,
            PLAYFIELD_BOTTOM - PLAYFIELD_TOP,
        )
        pygame.draw.rect(self._screen, BOARD_FILL_COLOR, board_rect)

    def _draw_board(self) -> None:
        assert self._state.physics_world is not None
        for segment in self._state.physics_world.boundaries:
            start = (int(segment.a.x), int(segment.a.y))
            end = (int(segment.b.x), int(segment.b.y))
            pygame.draw.line(self._screen, BOARD_LINE_COLOR, start, end, max(1, int(segment.radius * 2)))

    def _draw_receptacle(self) -> None:
        assert self._state.receptacle is not None
        receptacle = self._state.receptacle
        line_color = (20, 40, 110) if self._state.selected_receptacle else BOARD_LINE_COLOR
        pygame.draw.line(
            self._screen,
            line_color,
            (int(receptacle.left_x), int(receptacle.bottom_y)),
            (int(receptacle.right_x), int(receptacle.bottom_y)),
            receptacle.wall_thickness,
        )
        pygame.draw.line(
            self._screen,
            line_color,
            (int(receptacle.left_x), int(receptacle.top_y)),
            (int(receptacle.left_x), int(receptacle.bottom_y)),
            receptacle.wall_thickness,
        )
        pygame.draw.line(
            self._screen,
            line_color,
            (int(receptacle.right_x), int(receptacle.top_y)),
            (int(receptacle.right_x), int(receptacle.bottom_y)),
            receptacle.wall_thickness,
        )

    def _draw_marble(self) -> None:
        assert self._state.marble is not None
        position = self._state.marble.position
        pygame.draw.circle(
            self._screen,
            MARBLE_COLOR,
            (int(position.x), int(position.y)),
            self._state.marble.shape.radius,
        )
        if self._state.ball_selected and not self._state.simulation_active:
            pygame.draw.circle(
                self._screen,
                BOARD_LINE_COLOR,
                (int(position.x), int(position.y)),
                self._state.marble.shape.radius + 5,
                2,
            )

    def _draw_reflectors(self) -> None:
        for reflector in self._state.rect_reflectors:
            vertices = [reflector.body.local_to_world(vertex) for vertex in reflector.shape.get_vertices()]
            points = [(int(vertex.x), int(vertex.y)) for vertex in vertices]
            color = (20, 40, 110) if reflector.id == self._state.selected_rect_id else REFLECTOR_COLOR
            pygame.draw.polygon(self._screen, color, points)

        for reflector in self._state.circle_reflectors:
            position = reflector.body.position
            color = (20, 40, 110) if reflector.id == self._state.selected_circle_id else REFLECTOR_COLOR
            pygame.draw.circle(
                self._screen,
                color,
                (int(position.x), int(position.y)),
                int(reflector.variant.radius),
            )

    def _draw_palette(self) -> None:
        panel_rect = self._palette_panel_rect()
        panel_left = panel_rect.x
        pygame.draw.rect(self._screen, PALETTE_FILL_COLOR, panel_rect)
        pygame.draw.rect(self._screen, PALETTE_BORDER_COLOR, panel_rect, 2)

        heading = self._font.render("Reflector Palette", True, TEXT_COLOR)
        self._screen.blit(heading, (panel_left + 16, PLAYFIELD_TOP + 16))

        content_clip = pygame.Rect(panel_rect.x + 4, panel_rect.y + 44, panel_rect.width - 8, panel_rect.height - 48)
        previous_clip = self._screen.get_clip()
        self._screen.set_clip(content_clip)

        y = PLAYFIELD_TOP + 56 - int(self._state.palette_scroll_y)
        ball_label = self._small_font.render("Ball", True, TEXT_COLOR)
        self._screen.blit(ball_label, (panel_left + 16, y))
        y += 24

        ball_selected = self._state.palette_selection == ("ball", "ball")
        ball_row_rect = pygame.Rect(panel_left + 10, y - 2, panel_rect.width - 20, 34)
        if ball_selected:
            pygame.draw.rect(self._screen, (217, 224, 240), ball_row_rect, border_radius=6)
        pygame.draw.circle(self._screen, MARBLE_COLOR, (panel_left + 32, y + 15), 11)
        ball_row_label = self._tiny_font.render("Place Ball", True, MUTED_TEXT_COLOR)
        self._screen.blit(ball_row_label, (panel_left + 58, y + 7))
        y += 44

        rect_label = self._small_font.render("Rectangles", True, TEXT_COLOR)
        self._screen.blit(rect_label, (panel_left + 16, y))
        y += 24

        for variant in RECT_VARIANTS:
            is_selected = self._state.palette_selection == ("rect", variant)
            preview_width = min(int(variant.width * 0.32), 110)
            row_rect = pygame.Rect(panel_left + 8, y - 6, panel_rect.width - 16, 38)
            if is_selected:
                pygame.draw.rect(self._screen, (217, 224, 240), row_rect, border_radius=6)
            preview_rect = pygame.Rect(panel_left + 16, y + 4, preview_width, max(6, int(variant.height)))
            pygame.draw.rect(self._screen, REFLECTOR_COLOR, preview_rect)
            label = self._tiny_font.render(f"{variant.name} {int(variant.width)}x{int(variant.height)}", True, MUTED_TEXT_COLOR)
            self._screen.blit(label, (panel_left + 16, y + 16))
            y += 42

        y += 4
        circle_label = self._small_font.render("Circles", True, TEXT_COLOR)
        self._screen.blit(circle_label, (panel_left + 16, y))
        y += 24

        for variant in CIRCLE_VARIANTS:
            is_selected = self._state.palette_selection == ("circle", variant)
            preview_radius = max(10, min(int(variant.radius * 0.45), 18))
            row_height = max(30, preview_radius * 2 + 4)
            row_rect = pygame.Rect(panel_left + 10, y - 2, panel_rect.width - 20, row_height)
            if is_selected:
                pygame.draw.rect(self._screen, (217, 224, 240), row_rect, border_radius=6)
            center = (panel_left + 32, y + row_height // 2)
            pygame.draw.circle(self._screen, REFLECTOR_COLOR, center, preview_radius)
            label = self._tiny_font.render(f"{variant.name} r={int(variant.radius)}", True, MUTED_TEXT_COLOR)
            self._screen.blit(label, (panel_left + 62, y + row_height // 2 - 8))
            y += row_height + 8

        y += 4
        receptacle_label = self._small_font.render("Receptacles", True, TEXT_COLOR)
        self._screen.blit(receptacle_label, (panel_left + 16, y))
        y += 22

        for variant in RECEPTACLE_VARIANTS:
            is_selected = self._state.receptacle is not None and self._state.receptacle.variant_name == variant.name
            row_rect = pygame.Rect(panel_left + 8, y - 4, panel_rect.width - 16, 28)
            if is_selected:
                pygame.draw.rect(self._screen, (217, 224, 240), row_rect, border_radius=6)
            preview_width = min(int(variant.width * 0.22), 90)
            preview_height = max(10, min(int(variant.height * 0.18), 18))
            preview_x = panel_left + 16
            preview_bottom_y = y + 18
            pygame.draw.line(self._screen, BOARD_LINE_COLOR, (preview_x, preview_bottom_y), (preview_x + preview_width, preview_bottom_y), 2)
            pygame.draw.line(self._screen, BOARD_LINE_COLOR, (preview_x, preview_bottom_y - preview_height), (preview_x, preview_bottom_y), 2)
            pygame.draw.line(self._screen, BOARD_LINE_COLOR, (preview_x + preview_width, preview_bottom_y - preview_height), (preview_x + preview_width, preview_bottom_y), 2)
            label = self._tiny_font.render(f"{variant.name} {int(variant.width)}x{int(variant.height)}", True, MUTED_TEXT_COLOR)
            self._screen.blit(label, (panel_left + 118, y + 4))
            y += 32

        self._screen.set_clip(previous_clip)
        self._draw_palette_scrollbar(panel_rect)

    def _draw_launch_controls(self) -> None:
        speed_rect = self._speed_slider_rect()
        angle_rect = self._angle_slider_rect()
        launch_rect = self._launch_button_rect()
        retry_rect = self._retry_button_rect()

        speed_label = self._small_font.render(f"Speed: {int(self._state.speed_value)}", True, TEXT_COLOR)
        angle_label = self._small_font.render(f"Angle: {int(self._state.angle_value)} deg", True, TEXT_COLOR)
        state_label = self._tiny_font.render(self._status_text(), True, MUTED_TEXT_COLOR)

        self._screen.blit(speed_label, (24, 96))
        self._screen.blit(angle_label, (24, 136))
        self._screen.blit(state_label, (24, 12))

        self._draw_slider(speed_rect, self._state.speed_value, MARBLE_MIN_SPEED, MARBLE_MAX_SPEED)
        self._draw_slider(angle_rect, self._state.angle_value, MARBLE_MIN_ANGLE_DEGREES, MARBLE_MAX_ANGLE_DEGREES)

        pygame.draw.rect(self._screen, (225, 231, 236), launch_rect, border_radius=8)
        pygame.draw.rect(self._screen, BOARD_LINE_COLOR, launch_rect, 2, border_radius=8)
        button_text = "Launch" if not self._state.simulation_active else "Running"
        text_surface = self._small_font.render(button_text, True, TEXT_COLOR)
        text_rect = text_surface.get_rect(center=launch_rect.center)
        self._screen.blit(text_surface, text_rect)

        pygame.draw.rect(self._screen, (235, 238, 242), retry_rect, border_radius=8)
        pygame.draw.rect(self._screen, BOARD_LINE_COLOR, retry_rect, 2, border_radius=8)
        retry_text = self._small_font.render("Try Again", True, TEXT_COLOR)
        retry_text_rect = retry_text.get_rect(center=retry_rect.center)
        self._screen.blit(retry_text, retry_text_rect)

    def _draw_leaderboard_summary(self) -> None:
        assert self._state.leaderboard is not None
        attempts = self._state.leaderboard.data.attempts
        successes = self._state.leaderboard.data.successes
        panel_rect = pygame.Rect(690, 84, 300, 74)
        pygame.draw.rect(self._screen, (236, 240, 245), panel_rect, border_radius=10)
        pygame.draw.rect(self._screen, BOARD_LINE_COLOR, panel_rect, 2, border_radius=10)

        title = self._tiny_font.render("Scoreboard", True, MUTED_TEXT_COLOR)
        self._screen.blit(title, (panel_rect.x + 14, panel_rect.y + 10))

        attempts_label = self._small_font.render("Attempts", True, MUTED_TEXT_COLOR)
        successes_label = self._small_font.render("Successes", True, MUTED_TEXT_COLOR)
        attempts_value = self._font.render(str(attempts), True, TEXT_COLOR)
        successes_value = self._font.render(str(successes), True, TEXT_COLOR)

        self._screen.blit(attempts_label, (panel_rect.x + 16, panel_rect.y + 30))
        self._screen.blit(successes_label, (panel_rect.x + 166, panel_rect.y + 30))
        self._screen.blit(attempts_value, (panel_rect.x + 92, panel_rect.y + 24))
        self._screen.blit(successes_value, (panel_rect.x + 256, panel_rect.y + 24))

        recent = self._state.leaderboard.data.recent_results[:4]
        recent_text = "Recent: " + "  ".join(f"#{item.attempt_number}:{item.result}" for item in recent) if recent else "Recent: none"
        recent_label = self._tiny_font.render(
            recent_text,
            True,
            MUTED_TEXT_COLOR,
        )
        self._screen.blit(recent_label, (panel_rect.x + 14, panel_rect.y + 54))

    def _draw_slider(self, rect: pygame.Rect, value: float, min_value: float, max_value: float) -> None:
        pygame.draw.rect(self._screen, (185, 190, 198), rect, border_radius=3)
        ratio = 0.0 if max_value == min_value else (value - min_value) / (max_value - min_value)
        knob_x = rect.left + int(ratio * rect.width)
        knob_y = rect.centery
        pygame.draw.circle(self._screen, BOARD_LINE_COLOR, (knob_x, knob_y), SLIDER_KNOB_RADIUS)

    def _handle_left_mouse_down(self, position: tuple[int, int]) -> None:
        if self._try_start_slider_drag(position):
            return

        if self._launch_button_rect().collidepoint(position):
            self._launch_marble()
            return

        if self._retry_button_rect().collidepoint(position):
            self._retry_attempt()
            return

        if self._try_select_palette_item(position):
            return

        if not self._is_in_playfield(position):
            return

        if not self._state.simulation_active and self._is_click_near_marble(position):
            self._state.ball_selected = True
            self._state.palette_selection = None
            self._clear_piece_selection()
            return

        if self._handle_receptacle_click(position):
            self._state.ball_selected = False
            return

        if self._handle_existing_piece_click(position):
            self._state.ball_selected = False
            return

        if self._move_selected_piece(position):
            self._state.ball_selected = False
            return

        if self._state.palette_selection is not None:
            if self._state.palette_selection[0] == "ball":
                self._place_marble(position)
                self._state.palette_selection = None
            else:
                self._create_piece_from_palette(position)
            self._state.ball_selected = False
            return

        if not self._state.simulation_active and self._state.ball_selected:
            self._place_marble(position)
            self._state.ball_selected = False

    def _handle_right_mouse_down(self, position: tuple[int, int]) -> None:
        if not self._is_in_playfield(position):
            return
        selected_rect = self._get_selected_rect()
        if selected_rect is not None and self._is_near_rect_reflector(position, selected_rect):
            selected_rect.rotate(-10)

    def _handle_mouse_wheel(self, delta_y: int) -> None:
        max_scroll = self._palette_max_scroll()
        if max_scroll <= 0:
            self._state.palette_scroll_y = 0.0
            return
        self._state.palette_scroll_y = max(0.0, min(self._state.palette_scroll_y - delta_y * 28.0, max_scroll))

    def _handle_mouse_motion(self, event: pygame.event.Event) -> None:
        position = event.pos
        if self._state.dragging_speed_slider:
            self._state.speed_value = self._slider_value_from_x(
                position[0],
                self._speed_slider_rect(),
                MARBLE_MIN_SPEED,
                MARBLE_MAX_SPEED,
            )
        elif self._state.dragging_angle_slider:
            self._state.angle_value = self._slider_value_from_x(
                position[0],
                self._angle_slider_rect(),
                MARBLE_MIN_ANGLE_DEGREES,
                MARBLE_MAX_ANGLE_DEGREES,
            )
        elif event.buttons[0] and self._state.drag_target_type is not None:
            self._drag_selected_object(position)

    def _try_select_palette_item(self, position: tuple[int, int]) -> bool:
        panel_rect = self._palette_panel_rect()
        panel_left = panel_rect.x
        if not panel_rect.collidepoint(position):
            return False

        content_top = panel_rect.y + 44
        if position[1] < content_top:
            return True

        y = PLAYFIELD_TOP + 80 - int(self._state.palette_scroll_y)
        ball_row_rect = pygame.Rect(panel_left + 8, y - 4, panel_rect.width - 16, 38)
        if ball_row_rect.collidepoint(position):
            self._state.palette_selection = ("ball", "ball")
            self._state.ball_selected = False
            self._clear_piece_selection()
            return True

        y += 48
        for variant in RECT_VARIANTS:
            row_rect = pygame.Rect(panel_left + 8, y - 6, panel_rect.width - 16, 38)
            if row_rect.collidepoint(position):
                self._state.palette_selection = ("rect", variant)
                self._state.ball_selected = False
                self._clear_piece_selection()
                return True
            y += 42

        y += 28
        for variant in CIRCLE_VARIANTS:
            preview_radius = max(10, min(int(variant.radius * 0.45), 18))
            row_height = max(30, preview_radius * 2 + 4)
            row_rect = pygame.Rect(panel_left + 8, y - 4, panel_rect.width - 16, row_height + 4)
            if row_rect.collidepoint(position):
                self._state.palette_selection = ("circle", variant)
                self._state.ball_selected = False
                self._clear_piece_selection()
                return True
            y += row_height + 8

        y += 4
        y += 22
        for variant in RECEPTACLE_VARIANTS:
            row_rect = pygame.Rect(panel_left + 8, y - 4, panel_rect.width - 16, 28)
            if row_rect.collidepoint(position):
                self._apply_receptacle_variant(variant)
                self._state.ball_selected = False
                self._clear_piece_selection()
                self._state.selected_receptacle = True
                return True
            y += 32

        return True

    def _handle_existing_piece_click(self, position: tuple[int, int]) -> bool:
        point = position
        for reflector in reversed(self._state.circle_reflectors):
            query_info = reflector.shape.point_query(point)
            if query_info.distance <= 20:
                if self._state.palette_selection == ("ball", "ball"):
                    self._place_marble_on_shape(reflector.shape, query_info)
                    self._state.palette_selection = None
                    return True
                if self._state.selected_circle_id == reflector.id:
                    self._begin_drag("circle", reflector.id, position, reflector.body.position)
                    return True
                self._state.selected_circle_id = reflector.id
                self._state.selected_rect_id = None
                self._state.selected_receptacle = False
                self._begin_drag("circle", reflector.id, position, reflector.body.position)
                return True

        for reflector in reversed(self._state.rect_reflectors):
            query_info = reflector.shape.point_query(point)
            if query_info.distance <= 20 or self._is_near_rect_reflector(position, reflector):
                if self._state.palette_selection == ("ball", "ball"):
                    self._place_marble_on_shape(reflector.shape, query_info)
                    self._state.palette_selection = None
                    return True
                if self._state.selected_rect_id == reflector.id:
                    self._begin_drag("rect", reflector.id, position, reflector.body.position)
                    return True
                self._state.selected_rect_id = reflector.id
                self._state.selected_circle_id = None
                self._state.selected_receptacle = False
                self._begin_drag("rect", reflector.id, position, reflector.body.position)
                return True

        self._clear_piece_selection()
        return False

    def _handle_receptacle_click(self, position: tuple[int, int]) -> bool:
        if self._state.simulation_active or self._state.receptacle is None:
            return False
        if not self._state.receptacle.hit_test(position[0], position[1]):
            return False
        self._clear_piece_selection()
        self._state.selected_receptacle = True
        self._begin_drag(
            "receptacle",
            None,
            position,
            (self._state.receptacle.center_x, self._state.receptacle.bottom_y),
        )
        return True

    def _create_piece_from_palette(self, position: tuple[int, int]) -> None:
        assert self._state.physics_world is not None
        piece_type, variant = self._state.palette_selection
        clamped_position = self._clamp_to_playfield(position)

        if piece_type == "rect":
            reflector = RectReflector(self._state.physics_world, variant, clamped_position, 0)
            self._state.rect_reflectors.append(reflector)
            self._state.selected_rect_id = reflector.id
            self._state.selected_circle_id = None
        else:
            reflector = CircleReflector(self._state.physics_world, variant, clamped_position)
            self._state.circle_reflectors.append(reflector)
            self._state.selected_circle_id = reflector.id
            self._state.selected_rect_id = None

        self._state.palette_selection = None

    def _move_selected_piece(self, position: tuple[int, int]) -> bool:
        if self._state.simulation_active:
            return False
        clamped_position = self._clamp_to_playfield(position)
        selected_rect = self._get_selected_rect()
        if selected_rect is not None:
            selected_rect.set_position(clamped_position)
            return True

        selected_circle = self._get_selected_circle()
        if selected_circle is not None:
            selected_circle.set_position(clamped_position)
            return True

        return False

    def _get_selected_rect(self) -> RectReflector | None:
        for reflector in self._state.rect_reflectors:
            if reflector.id == self._state.selected_rect_id:
                return reflector
        return None

    def _get_selected_circle(self) -> CircleReflector | None:
        for reflector in self._state.circle_reflectors:
            if reflector.id == self._state.selected_circle_id:
                return reflector
        return None

    def _clear_piece_selection(self) -> None:
        self._state.selected_rect_id = None
        self._state.selected_circle_id = None
        self._state.selected_receptacle = False

    def _begin_drag(
        self,
        target_type: str,
        target_id: int | None,
        mouse_position: tuple[int, int],
        object_position: tuple[float, float] | pymunk.Vec2d,
    ) -> None:
        self._state.drag_target_type = target_type
        self._state.drag_target_id = target_id
        self._state.drag_offset_x = mouse_position[0] - float(object_position[0])
        self._state.drag_offset_y = mouse_position[1] - float(object_position[1])
        self._state.drag_moved = False
        self._state.drag_start_mouse_x = mouse_position[0]
        self._state.drag_start_mouse_y = mouse_position[1]

    def _drag_selected_object(self, position: tuple[int, int]) -> None:
        if self._state.simulation_active:
            return
        target_x = position[0] - self._state.drag_offset_x
        target_y = position[1] - self._state.drag_offset_y
        dx = position[0] - self._state.drag_start_mouse_x
        dy = position[1] - self._state.drag_start_mouse_y
        if (dx * dx + dy * dy) >= 36:
            self._state.drag_moved = True
        if not self._state.drag_moved:
            return

        if self._state.drag_target_type == "rect":
            selected_rect = self._get_selected_rect()
            if selected_rect is not None:
                selected_rect.set_position(self._clamp_to_playfield((target_x, target_y)))
            return

        if self._state.drag_target_type == "circle":
            selected_circle = self._get_selected_circle()
            if selected_circle is not None:
                selected_circle.set_position(self._clamp_to_playfield((target_x, target_y)))
            return

        if self._state.drag_target_type == "receptacle" and self._state.receptacle is not None:
            clamped_x, clamped_bottom_y = self._clamp_receptacle_position(target_x, target_y)
            self._state.receptacle.set_position(clamped_x, clamped_bottom_y)

    def _finish_drag_or_click(self, mouse_position: tuple[int, int]) -> None:
        if self._state.drag_target_type is not None and not self._state.drag_moved:
            dx = mouse_position[0] - self._state.drag_start_mouse_x
            dy = mouse_position[1] - self._state.drag_start_mouse_y
            if (dx * dx + dy * dy) >= 36:
                self._drag_selected_object(mouse_position)
        if (
            self._state.drag_target_type == "rect"
            and not self._state.drag_moved
            and self._state.selected_rect_id == self._state.drag_target_id
        ):
            selected_rect = self._get_selected_rect()
            if selected_rect is not None:
                selected_rect.rotate(10)
        self._state.drag_target_type = None
        self._state.drag_target_id = None
        self._state.drag_offset_x = 0.0
        self._state.drag_offset_y = 0.0
        self._state.drag_moved = False
        self._state.drag_start_mouse_x = 0.0
        self._state.drag_start_mouse_y = 0.0

    def _place_marble(self, position: tuple[int, int]) -> None:
        assert self._state.marble is not None
        self._state.marble.set_position(self._clamp_to_playfield(position))
        self._state.ball_support_normal = None

    def _is_near_rect_reflector(self, position: tuple[int, int], reflector: RectReflector) -> bool:
        dx = position[0] - float(reflector.body.position.x)
        dy = position[1] - float(reflector.body.position.y)
        radius = max(reflector.variant.width, reflector.variant.height) * 0.5 + 24.0
        return (dx * dx + dy * dy) <= radius * radius

    def _place_marble_on_shape(
        self,
        shape: pymunk.Shape,
        query_info: pymunk.PointQueryInfo,
    ) -> None:
        assert self._state.marble is not None
        gradient = query_info.gradient
        if gradient.length < 1e-6:
            gradient = pymunk.Vec2d(0.0, -1.0)
        else:
            gradient = gradient.normalized()
        target = query_info.point + gradient * (
            float(self._state.marble.shape.radius) + BALL_ON_REFLECTOR_CLEARANCE
        )
        clamped_target = self._clamp_to_playfield((float(target.x), float(target.y)))
        self._state.marble.set_position(clamped_target)
        self._state.ball_support_normal = (float(gradient.x), float(gradient.y))

    def _launch_marble(self) -> None:
        if self._state.simulation_active:
            return
        assert self._state.marble is not None
        self._state.last_launch_ball_position = (
            float(self._state.marble.position.x),
            float(self._state.marble.position.y),
        )
        self._state.last_launch_ball_support_normal = self._state.ball_support_normal
        self._state.marble.set_velocity(self._compute_launch_velocity())
        self._state.simulation_active = True
        self._state.attempt_result = None
        self._state.entered_receptacle = False
        self._state.settle_elapsed_seconds = 0.0
        self._state.safe_receptacle_frames = 0
        self._state.result_recorded = False

    def _is_click_near_marble(self, position: tuple[int, int]) -> bool:
        assert self._state.marble is not None
        dx = position[0] - float(self._state.marble.position.x)
        dy = position[1] - float(self._state.marble.position.y)
        return (dx * dx + dy * dy) <= 28 * 28

    def _is_in_playfield(self, position: tuple[int, int]) -> bool:
        return PLAYFIELD_LEFT <= position[0] <= PLAYFIELD_RIGHT and PLAYFIELD_TOP <= position[1] <= PLAYFIELD_BOTTOM

    def _clamp_to_playfield(self, position: tuple[float, float]) -> tuple[float, float]:
        x = max(PLAYFIELD_LEFT + 20, min(position[0], PLAYFIELD_RIGHT - 20))
        y = max(PLAYFIELD_TOP + 20, min(position[1], PLAYFIELD_BOTTOM - 20))
        return (x, y)

    def _clamp_receptacle_position(self, center_x: float, bottom_y: float) -> tuple[float, float]:
        assert self._state.receptacle is not None
        half_width = self._state.receptacle.width * 0.5
        x = max(PLAYFIELD_LEFT + half_width + 6, min(center_x, PLAYFIELD_RIGHT - half_width - 6))
        y = max(
            PLAYFIELD_TOP + self._state.receptacle.height + 12,
            min(bottom_y, PLAYFIELD_BOTTOM - 6),
        )
        return (x, y)

    def _try_start_slider_drag(self, position: tuple[int, int]) -> bool:
        speed_rect = self._speed_slider_rect()
        angle_rect = self._angle_slider_rect()
        if speed_rect.inflate(0, 20).collidepoint(position):
            self._state.dragging_speed_slider = True
            self._state.dragging_angle_slider = False
            self._state.speed_value = self._slider_value_from_x(
                position[0], speed_rect, MARBLE_MIN_SPEED, MARBLE_MAX_SPEED
            )
            return True
        if angle_rect.inflate(0, 20).collidepoint(position):
            self._state.dragging_angle_slider = True
            self._state.dragging_speed_slider = False
            self._state.angle_value = self._slider_value_from_x(
                position[0], angle_rect, MARBLE_MIN_ANGLE_DEGREES, MARBLE_MAX_ANGLE_DEGREES
            )
            return True
        return False

    def _slider_value_from_x(self, x: int, rect: pygame.Rect, min_value: float, max_value: float) -> float:
        ratio = (max(rect.left, min(x, rect.right)) - rect.left) / rect.width
        return min_value + ratio * (max_value - min_value)

    def _speed_slider_rect(self) -> pygame.Rect:
        return pygame.Rect(150, 104, SLIDER_WIDTH, SLIDER_HEIGHT)

    def _angle_slider_rect(self) -> pygame.Rect:
        return pygame.Rect(150, 144, SLIDER_WIDTH, SLIDER_HEIGHT)

    def _launch_button_rect(self) -> pygame.Rect:
        return pygame.Rect(410, 92, LAUNCH_BUTTON_WIDTH, LAUNCH_BUTTON_HEIGHT)

    def _retry_button_rect(self) -> pygame.Rect:
        return pygame.Rect(545, 92, LAUNCH_BUTTON_WIDTH + 20, LAUNCH_BUTTON_HEIGHT)

    def _retry_attempt(self) -> None:
        assert self._state.marble is not None
        if self._state.last_launch_ball_position is not None:
            self._state.marble.set_position(self._state.last_launch_ball_position)
            self._state.ball_support_normal = self._state.last_launch_ball_support_normal
        self._state.simulation_active = False
        self._state.attempt_result = None
        self._state.entered_receptacle = False
        self._state.settle_elapsed_seconds = 0.0
        self._state.result_recorded = False
        self._state.ball_selected = False

    def _palette_panel_rect(self) -> pygame.Rect:
        return pygame.Rect(PLAYFIELD_RIGHT + 24, PLAYFIELD_TOP, PALETTE_WIDTH - 48, PLAYFIELD_BOTTOM - PLAYFIELD_TOP)

    def _palette_content_height(self) -> int:
        height = 0
        height += 24 + 44
        height += 24 + len(RECT_VARIANTS) * 42
        height += 4 + 24 + sum(max(30, max(10, min(int(v.radius * 0.45), 18)) * 2 + 4) + 8 for v in CIRCLE_VARIANTS)
        height += 4 + 22 + len(RECEPTACLE_VARIANTS) * 32
        return height + 16

    def _palette_max_scroll(self) -> float:
        panel_rect = self._palette_panel_rect()
        visible_height = panel_rect.height - 48
        return max(0.0, float(self._palette_content_height() - visible_height))

    def _draw_palette_scrollbar(self, panel_rect: pygame.Rect) -> None:
        max_scroll = self._palette_max_scroll()
        if max_scroll <= 0:
            return
        track_rect = pygame.Rect(panel_rect.right - 10, panel_rect.y + 46, 4, panel_rect.height - 52)
        pygame.draw.rect(self._screen, (210, 214, 222), track_rect, border_radius=3)
        visible_height = panel_rect.height - 48
        thumb_height = max(28, int((visible_height / self._palette_content_height()) * track_rect.height))
        travel = max(1, track_rect.height - thumb_height)
        thumb_y = track_rect.y + int((self._state.palette_scroll_y / max_scroll) * travel)
        thumb_rect = pygame.Rect(track_rect.x, thumb_y, track_rect.width, thumb_height)
        pygame.draw.rect(self._screen, BOARD_LINE_COLOR, thumb_rect, border_radius=3)

    def _apply_receptacle_variant(self, variant) -> None:
        assert self._state.receptacle is not None
        current_x = self._state.receptacle.center_x
        current_y = self._state.receptacle.bottom_y
        self._state.receptacle.apply_variant(variant)
        clamped_x, clamped_y = self._clamp_receptacle_position(current_x, current_y)
        self._state.receptacle.set_position(clamped_x, clamped_y)

    def _update_attempt_state(self, dt: float) -> None:
        assert self._state.marble is not None
        assert self._state.receptacle is not None

        marble_x = float(self._state.marble.position.x)
        marble_y = float(self._state.marble.position.y)
        marble_radius = float(self._state.marble.shape.radius)
        speed = float(self._state.marble.body.velocity.length)
        vertical_speed = abs(float(self._state.marble.body.velocity.y))
        inside_receptacle = self._state.receptacle.contains_marble_center(
            marble_x,
            marble_y,
            marble_radius,
        )

        if marble_y - marble_radius > PLAYFIELD_BOTTOM:
            self._state.attempt_result = 0
            self._state.simulation_active = False
            return

        if inside_receptacle:
            self._state.entered_receptacle = True
            if vertical_speed <= RECEPTACLE_VERTICAL_STOP_THRESHOLD:
                self._state.marble.set_velocity((0.0, 0.0))
                self._state.marble.body.angular_velocity = 0.0
                speed = 0.0
            if speed <= RECEPTACLE_SETTLE_SPEED_THRESHOLD:
                self._state.settle_elapsed_seconds += dt
                self._state.safe_receptacle_frames += 1
                if (
                    self._state.settle_elapsed_seconds >= RECEPTACLE_SETTLE_TIME_SECONDS
                    and self._state.safe_receptacle_frames >= RECEPTACLE_SAFE_FRAMES_REQUIRED
                ):
                    self._state.attempt_result = 1
                    self._state.simulation_active = False
            else:
                self._state.settle_elapsed_seconds = 0.0
                self._state.safe_receptacle_frames = 0
            return

        self._state.settle_elapsed_seconds = 0.0
        self._state.safe_receptacle_frames = 0

    def _status_text(self) -> str:
        if self._state.attempt_result == 1:
            return "State: success (1 point)"
        if self._state.attempt_result == 0:
            return "State: failed (0 points)"
        if self._state.simulation_active:
            return "State: running"
        return "State: setup"

    def _compute_launch_velocity(self) -> tuple[float, float]:
        if self._state.ball_support_normal is None:
            angle_radians = radians(self._state.angle_value)
            requested = pymunk.Vec2d(
                self._state.speed_value * cos(angle_radians),
                -self._state.speed_value * sin(angle_radians),
            )
            return (float(requested.x), float(requested.y))
        return (0.0, 0.0)

    def _record_attempt_result_if_needed(self) -> None:
        if self._state.attempt_result is None or self._state.result_recorded:
            return
        assert self._state.leaderboard is not None
        self._state.leaderboard.record_attempt(self._state.attempt_result)
        self._state.result_recorded = True

    def _write_runtime_log(self) -> None:
        assert self._state.marble is not None
        leaderboard_payload = None
        if self._state.leaderboard is not None:
            leaderboard_payload = {
                "attempts": self._state.leaderboard.data.attempts,
                "successes": self._state.leaderboard.data.successes,
            }
        payload = {
            "frame": self._state.frame_count,
            "ball_position": {
                "x": round(float(self._state.marble.position.x), 3),
                "y": round(float(self._state.marble.position.y), 3),
            },
            "ball_velocity": {
                "x": round(float(self._state.marble.velocity.x), 3),
                "y": round(float(self._state.marble.velocity.y), 3),
            },
            "launch": {
                "speed": round(self._state.speed_value, 3),
                "angle_degrees": round(self._state.angle_value, 3),
                "simulation_active": self._state.simulation_active,
            },
            "attempt": {
                "result": self._state.attempt_result,
                "entered_receptacle": self._state.entered_receptacle,
                "settle_elapsed_seconds": round(self._state.settle_elapsed_seconds, 3),
                "safe_receptacle_frames": self._state.safe_receptacle_frames,
            },
            "leaderboard": leaderboard_payload,
        }
        DIAGNOSTIC_LOG_PATH.write_text(json.dumps(payload, indent=2))


def run() -> None:
    MarbleRunApp().run()
