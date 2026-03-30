# Tech Stack Decision

## Recommendation

Use:

- Python `3.11+`
- `pygame-ce` for windowing, rendering, input, audio, and the main loop
- `pymunk` for 2D physics
- JSON for level and leaderboard data

## Why This Stack

### `pygame-ce`

- Mature and straightforward for desktop 2D games
- Good enough rendering for a whiteboard-style interface
- Fast iteration speed
- Simple input handling for drag-and-drop, rotate, and launch controls

### `pymunk`

- Good 2D rigid body physics for circles, segments, and polygons
- Suitable for bounce-heavy gameplay
- Easier than writing collision/response logic from scratch
- Good fit for deterministic-ish puzzle simulation

### Python

- Fastest route to a playable prototype in this workspace
- Easy to read and refactor
- Good for iteration while rules and feel are still changing

## Why Not Other Options Right Now

### Custom Physics

- Too expensive early
- High bug risk
- Unnecessary when the game depends on reliable collision response

### Full 3D Engine

- Wrong scope for V1
- Adds camera, lighting, and asset complexity
- The game design is fundamentally readable in 2D

### Browser Stack

- Viable later, but not ideal for the fastest first build in this repo
- Would force extra decisions around packaging and deployment too early

## Technical Direction

- Target desktop first
- Keep the simulation 2D
- Use a fixed timestep for physics
- Use `friction = 0` and no damping for the initial V1 physics profile
- Tune one global restitution coefficient in config rather than exposing it in the player UI
- Keep rendering intentionally simple and crisp
- Store data locally in plain JSON

## Initial Dependencies

Suggested packages:

- `pygame-ce`
- `pymunk`

Optional later:

- `pytest`
- `ruff`
- `black`

## Performance Expectations

This stack should comfortably support:

- one active marble
- several placed colliders
- real-time interaction
- responsive reset/retry loops

For V1, performance risk is low if we avoid overbuilding the renderer.

## Conclusion

For this game, `pygame-ce` plus `pymunk` is the correct first choice.

It is the shortest path to good physics, clear controls, and a playable single-player prototype.
