# Implementation Plan

## Goal

Ship a small playable V1 as quickly as possible without compromising the core feel of the game.

## Phase 1: Foundation

- Create the `src/` and `tests/` structure
- Set up the Python project and dependencies
- Open a game window
- Add a fixed timestep game loop
- Add a clean whiteboard background and world bounds

## Phase 2: Core Physics

- Integrate `pymunk`
- Add gravity
- Add the marble rigid body
- Add static boundaries
- Set `friction = 0` for V1
- Disable damping for V1
- Add one global restitution coefficient in config
- Make the marble simulate consistently at stable framerate

Exit criteria:

- A marble falls and collides correctly with simple surfaces using near-specular bounce behavior.

## Phase 3: Placeable Pieces

- Implement multiple rectangular reflector variants with different lengths and widths
- Implement multiple circular bumper variants with different radii
- Add piece palette UI
- Add drag-and-drop placement from the palette
- Add drag-to-reposition for already placed pieces
- Add rotation controls
- Support deleting or resetting placed pieces

Exit criteria:

- Player can easily drag, place, reposition, and rotate pieces before running the simulation.

## Phase 4: Launch Controls

- Add spawn point at top of board
- Add configurable initial velocity controls
- Show current velocity settings in UI
- Apply velocity on simulation start

Exit criteria:

- Player can reliably change how the marble starts.

## Phase 5: Receptacle And Win Logic

- Implement receptacle geometry
- Detect marble entry into receptacle
- Detect whether marble remains contained
- Add settle timer and low-velocity threshold
- Produce binary score result: `1` or `0`

Exit criteria:

- A run only succeeds if the marble ends stable inside the receptacle.

## Phase 6: Leaderboard

- Add simple name or initials input
- Save attempt results locally
- Display recent results
- Display successful runs clearly

Exit criteria:

- Local leaderboard works with no network or account system.

## Phase 7: First Playable Polish

- Improve colors and clarity
- Add clear success/failure feedback
- Add reset/retry flow
- Tune bounce, friction, and receptacle behavior
- Tune the global restitution value for feel and puzzle quality
- Remove obvious UI friction

Exit criteria:

- The game is understandable and pleasant to play without explanation.

## Testing Priorities

- Win detection edge cases
- Piece rotation correctness
- Level loading correctness
- Receptacle containment false positives
- Restitution tuning edge cases
- Stable reset behavior across many attempts

## V1 Non-Goals

- Multiplayer
- Online leaderboard
- Procedural levels
- Many advanced piece types
- Mobile support
- Full level editor

## Suggested Build Order

1. Window and loop
2. Physics world
3. Marble
4. Receptacle
5. Global restitution tuning
6. Rectangular reflector variants
7. Circular bumper variants
8. Placement and rotation UI
9. Drag-and-drop polish
10. Velocity controls
11. Win detection
12. Local leaderboard
13. Visual polish

## Definition Of Done For V1

V1 is done when a player can:

- launch the game
- choose from multiple rectangular and circular reflector variants
- drag and reposition pieces easily
- rotate pieces
- set initial ball velocity
- experience stable near-specular bounce behavior with fixed V1 restitution
- run and reset the simulation
- get a correct `1` or `0` result
- see that result stored in a simple local leaderboard
