

COLOR_TO_TILE ={
    (0, 0, 0): 0,           # Black = walkable space
    (255, 0, 0): 1,         # Red = brick wall
    (128, 128, 128): 2,     # Gray = stone wall
    (0, 0, 255): 3,         # Blue = metal wall
    (0, 255, 0): 4,         # Green = door
    (0, 128, 0): 5,         # Dark Green = locked door
    (255, 255, 0): "P",     # Yellow = player spwn
    (255, 0, 255): "E",     # Magenta = enemy spwn
    (0, 255, 255): "K",     # Cyan = key item
    (255, 255, 255): "H",   # White = health pack
    (255, 128, 0): "A",     # Orange = ammo
    (128, 0, 0): "X",        # Dark Red = exit
    (136, 255, 255): "L"    # Ceiling light
}
TILE_TO_COLOR = {v: k for k, v in COLOR_TO_TILE.items()}
WALL_TILES = {1, 2, 3, 4, 5}

TILE_NAMES = {
    0: "floor",
    1: "brick",
    2: "stone",
    3: "metal",
    4: "door",
    5: "door"
}

TEXTURE_ID_TO_TILE = {
    0: ("floor", "assets/textures/floor.png"),
    1: ("brick", "assets/textures/brickwall.png"),
    2: ("stone", "assets/textures/stone.png"),
    3: ("metal", "assets/textures/metal.png"),
    4: ("door", "assets/textures/door.png"),
    
}