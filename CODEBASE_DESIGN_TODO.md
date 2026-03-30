# Codebase Design TODO

## Game Definition

This game is a 2D physics puzzle, not a traditional track-building marble run.

The player sees a whiteboard-like playfield, places reflective/deflecting pieces onto it, chooses their angles, optionally chooses the marble's initial velocity, and then releases the marble from the top of the board.

The marble must obey physics throughout and must end by falling into the receptacle at the bottom and staying inside it.

## Core Goal

- Launch a marble from the top of the board.
- Let the marble bounce or deflect off placed pieces.
- Get the marble into the bottom receptacle.
- The marble only counts as a success if it remains in the receptacle.

## Current Product Decisions

- Single-player only
- No multiplayer for now
- Binary scoring per attempt:
  - `1` if the ball ends in the receptacle and stays there
  - `0` otherwise
- Players must be able to:
  - Choose which piece to place
  - Position the piece
  - Drag and drop the piece easily
  - Rotate the piece
  - Set the marble's initial velocity

## Recommended First Version

Build this as a 2D desktop game in Python with:

- `pygame-ce` for rendering, input, and the game loop
- `pymunk` for 2D rigid-body physics and collision handling

Why:

- Fastest path to a good Python prototype
- Strong enough 2D collision support for circles, segments, and polygons
- Easy to tune bounce, friction, damping, and receptacle behavior
- Good fit for a clean whiteboard visual style

## Core Gameplay Loop

1. Player selects one or more pieces from a palette.
2. Player places pieces on the whiteboard.
3. Player rotates pieces to desired angles.
4. Player sets the marble's initial launch velocity.
5. Player starts the simulation.
6. Physics runs in real time.
7. Game checks whether the marble settles inside the receptacle.
8. Attempt is scored as `1` or `0`.

## Piece Types For V1

- Straight rectangular reflector
- Circular bumper
- Curved reflector arc
- Sinusoidal reflector

Notes:

- Start with rectangle and circle first.
- Add sinusoidal and arc shapes only after core collision behavior feels right.
- All pieces should support rotation.

## Physics Requirements

- Gravity always applies
- Marble is a circle rigid body
- Reflectors behave as static colliders
- Bounce must feel consistent and predictable
- Use a global restitution coefficient for V1
- Friction and restitution must be tunable
- Use no friction and no damping for the initial V1 feel pass
- Receptacle must be shaped so a marble can enter and remain trapped when deserved
- Win condition should require the marble to settle, not merely touch the receptacle

V1 physics tuning notes:

- Keep friction at `0`
- Keep damping off
- Use one global restitution value
- Keep restitution in code/config, not player-facing UI
- Start with a high restitution target such as `0.95` to `0.99`
- Accept near-specular behavior rather than trying to force mathematically exact reflection

## Win Detection

A run is successful only if:

- The marble enters the receptacle area
- The marble remains inside for a short settle window
- The marble's speed drops below a threshold, or it stays contained long enough to count as stable

This avoids false wins where the ball clips the receptacle and bounces out.

## Leaderboard Scope

Keep it simple.

- Local leaderboard only
- No accounts
- No networking
- Each attempt stores:
  - player name or initials
  - level id
  - score: `1` or `0`
  - maybe attempt timestamp

Possible views:

- Best successful attempts
- Recent attempts
- Per-level completion count

## Level Model

Each level should define:

- Board dimensions
- Marble spawn position
- Default initial velocity
- Receptacle position and shape
- Available piece inventory
- Static obstacles, if any
- Success rules

## UI Requirements

- Whiteboard play area
- Piece palette
- Drag-and-drop piece placement
- Drag-to-reposition placed pieces
- Rotation controls
- Velocity controls
- Start/reset controls
- Clear visual feedback for success or failure
- Simple leaderboard panel

## Technical TODO

- Lock the stack: `pygame-ce` + `pymunk`
- Define the package/module structure
- Define the fixed-timestep simulation loop
- Define the piece data model and transform model
- Define drag-and-drop interaction behavior and snapping rules
- Define the global restitution config and default tuning value
- Define level JSON or YAML format
- Define local persistence format for leaderboard data
- Implement rectangle and circle pieces first
- Implement receptacle collision and settle detection
- Implement launch velocity UI
- Implement restart/reset flow
- Add deterministic-ish test scenes for collision tuning

## Suggested Vertical Slice

The first playable version should include:

- One level
- One marble
- One receptacle
- Two placeable piece types: rectangle and circle
- Piece placement and rotation
- Configurable initial velocity
- Run/reset loop
- Binary score result
- Local leaderboard

## Practical Recommendation

Yes, this sounds worth building.

The important constraint is to keep V1 narrow:

- 2D only
- few piece types
- local leaderboard only
- strong feel and reliable win detection before adding more content
