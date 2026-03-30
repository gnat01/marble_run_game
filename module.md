# Module Layout

## Goal

Keep the codebase small, readable, and easy to extend while the game is still in early development.

## Proposed Structure

```text
marble_run_game/
  Notes.txt
  CODEBASE_DESIGN_TODO.md
  module.md
  implementation.md
  tech_stack.md
  src/
    main.py
    config.py
    game/
      app.py
      loop.py
      state.py
      constants.py
    physics/
      world.py
      marble.py
      pieces.py
      receptacle.py
      collisions.py
      win_check.py
    levels/
      loader.py
      schema.py
      level_001.json
    ui/
      hud.py
      palette.py
      controls.py
      leaderboard_view.py
    data/
      leaderboard.py
      storage.py
    render/
      board.py
      pieces.py
      marble.py
      effects.py
    input/
      mouse.py
      keyboard.py
      placement.py
    utils/
      math2d.py
      timers.py
      ids.py
  tests/
    test_win_check.py
    test_level_loader.py
    test_piece_rotation.py
```

## Module Responsibilities

### `src/main.py`

- Entry point
- Initializes the app
- Starts the main game loop

### `src/config.py`

- Global configuration
- Screen size
- Physics tuning defaults
- Global restitution value for V1
- File paths

### `src/game/`

- High-level app orchestration
- Scene state
- Run/reset lifecycle
- Fixed timestep update flow

### `src/physics/`

- `world.py`: builds and steps the physics simulation
- `marble.py`: marble body creation and tuning
- `pieces.py`: placeable collider definitions
- `receptacle.py`: receptacle geometry and containment helpers
- `collisions.py`: collision categories and handlers
- `win_check.py`: settle detection and success logic

V1 physics defaults should assume:

- `friction = 0`
- no damping
- one global restitution coefficient shared across bounce surfaces

### `src/levels/`

- Level data format
- Level loading and validation
- Starter hand-authored levels

### `src/ui/`

- On-screen controls
- Piece palette
- Drag-and-drop affordances
- Launch velocity controls
- Score and leaderboard display

### `src/data/`

- Leaderboard persistence
- Local file storage helpers

### `src/render/`

- Whiteboard scene drawing
- Piece rendering
- Marble rendering
- Simple visual polish

### `src/input/`

- Mouse interaction
- Keyboard shortcuts
- Drag and drop behavior
- Placement and rotation behavior

### `src/utils/`

- Shared math helpers
- Small timing utilities
- Id generation helpers

## Design Notes

- Keep physics separate from rendering.
- Keep level definitions data-driven.
- Keep leaderboard logic out of gameplay logic.
- Avoid premature abstractions until V1 is playable.

## V1 Focus

For the first version, only fully implement:

- one level
- up to 5 rectangular reflector variants with different lengths and widths
- 2 to 3 circular bumper variants with different radii
- palette-based selection between those piece variants
- drag-and-drop piece placement
- marble launch
- fixed global restitution tuning in config
- receptacle settle detection
- local leaderboard save/load
