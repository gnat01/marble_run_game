# Order Of Implementation

1. Set up the project skeleton, window, and fixed timestep loop.
2. Add the 2D physics world with gravity, zero friction, no damping, and global restitution.
3. Add the marble, world bounds, and receptacle.
4. Implement reflector variants: 5 rectangles and 2-3 circles.
5. Build the palette plus drag-drop, reposition, and rotation controls.
6. Add initial velocity controls and run/reset flow.
7. Implement win detection: ball enters receptacle and stays settled.
8. Add the simple local leaderboard with `1` for success and `0` otherwise.
9. Tune bounce feel, receptacle behavior, and UI clarity.
