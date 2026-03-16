"""
engine/settings.py — All game constants in one place.

WHY THIS FILE EXISTS:
Instead of scattering numbers like 1920, 60, 0.05 throughout the code,
we define them here with descriptive names. Any module can do:

    from engine.settings import *

and get access to every constant. When you want to tweak something —
resolution, FOV, movement speed — you change ONE file.
"""

import math

# ─── Display ──────────────────────────────────────────────────────────
WIDTH = 1920                    # Window width in pixels
HEIGHT = 1080                   # Window height in pixels
HALF_WIDTH = WIDTH // 2
HALF_HEIGHT = HEIGHT // 2
FPS = 144                      # Target frames per second
DT = 1.0 / FPS                 # Fixed timestep for physics (seconds per tick)

# ─── Raycasting ───────────────────────────────────────────────────────
FOV = math.radians(60)          # Field of view in radians (60° is classic Doom)
HALF_FOV = FOV / 2
NUM_RAYS = WIDTH                # One ray per screen column = smooth walls
                                # (lower this for pixelated retro look, e.g. WIDTH // 2)
MAX_DEPTH = 20                  # Max ray travel distance in tiles
DELTA_ANGLE = FOV / NUM_RAYS    # Angle step between adjacent rays
TILE_SIZE = 1                   # Each map tile = 1 world unit (float math, not pixels)

# ─── Screen geometry derived from FOV ─────────────────────────────────
# Distance from the player to the "projection plane" (virtual screen).
# This converts perpendicular ray distance → wall strip height:
#   strip_height = SCREEN_DIST / perp_distance
SCREEN_DIST = HALF_WIDTH / math.tan(HALF_FOV)

# ─── Player ──────────────────────────────────────────────────────────
PLAYER_SPEED = 3.0              # Tiles per second
PLAYER_SIZE_SCALE = 0.2         # Collision radius in tiles
MOUSE_SENSITIVITY = 0.0003      # Radians per pixel of mouse movement
MOUSE_MAX_REL = 40              # Cap mouse delta to prevent spin on alt-tab
PLAYER_MAX_HEALTH = 100
LOOK_SENSIVITY = 0.002
COLLISION_MARGIN = 0.2
BOB_OFFSET = 15
# ─── Colors (R, G, B) normalized 0.0–1.0 for OpenGL ──────────────────
COLOR_SKY = (0.1, 0.1, 0.3)    # Dark blue-gray sky
COLOR_FLOOR = (0.15, 0.15, 0.15)  # Dark gray floor
COLOR_CLEAR = (0.0, 0.0, 0.0, 1.0)  # glClearColor — black
