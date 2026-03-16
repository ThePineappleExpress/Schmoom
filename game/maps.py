import pygame as pg
from engine.helpers import COLOR_TO_TILE, TILE_TO_COLOR, WALL_TILES, TILE_NAMES

class Map:
    """Loads map, spawns player and geometry from a png file."""
    def __init__(self, filepath):
        self.player_spawn = None
        self.enemy_spawns = []
        self.pickups = []
        self.grid=[]
        self._load(filepath)

    def _load(self, filepath):
        """Load map data from a png file."""
        image = pg.image.load(filepath)
        width, height = image.get_size()
        self.width = width
        self.height = height
        self.lights = []
        for y in range(height):
            row = []
            for x in range(width):
                color = image.get_at((x, y))[:3]
                if color in COLOR_TO_TILE:
                    if isinstance(COLOR_TO_TILE[color], str):
                        tile_type = COLOR_TO_TILE[color]
                        if tile_type == "P":
                            self.player_spawn = (x, y)
                            row.append(0)  # treat player spawn as floor tile
                        elif tile_type == "E":
                            self.enemy_spawns.append((x, y))
                            row.append(0)  # treat enemy spawn as floor tile
                        elif tile_type == "L":
                            self.lights.append((x, y))
                            row.append(0)  # treat light as floor tile
                        else:
                            self.pickups.append((tile_type, (x, y)))
                            row.append(0)  # treat pickups as floor tile
                    else:
                        row.append(COLOR_TO_TILE[color])
                else:
                    row.append(0)  # default to floor if color not recognized
            self.grid.append(row)
    
    def get_tile(self, x, y):
        """Return the tile type at the given grid coordinates."""
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.grid[y][x]
        else:
            return 1  # out of bounds
        
    def is_wall(self, x, y):
        """Return True if the tile at the given coordinates is a wall."""
        tile = self.get_tile(x, y)
        return tile in WALL_TILES
    
    def get_spawn(self, marker):
        """Return the spawn coordinates for the given marker ('P' or 'E')."""
        if marker == "P":
            return self.player_spawn
        elif marker == "E":
            return self.enemy_spawns
        else:
            return None