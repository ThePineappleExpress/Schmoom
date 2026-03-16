from engine.settings import WIDTH, HEIGHT
from engine.helpers import TILE_TO_COLOR
from game.maps import Map

class DebugView:
    def __init__(self, game_map, renderer):
        self.game_map = game_map
        self.renderer = renderer
        scale_x = WIDTH / game_map.width
        scale_y = HEIGHT / game_map.height
        self.tile_size = min(scale_x, scale_y)
    
    def render(self):
        """Render a top-down view of the map for debugging purposes.
        
        This will draw a simple overhead map showing walls, player spawn, and enemy spawns.
        It will be rendered in the corner of the screen on top of the main view.
        
        Steps:
        1. Draw a background rectangle for the map area
        2. Loop through the map grid and draw a small rectangle for each wall tile
        3. Draw a different colored rectangle for the player spawn point
        4. Draw different colored rectangles for each enemy spawn point"""
        for y in range(self.game_map.height):
            for x in range(self.game_map.width):
                tile = self.game_map.get_tile(x, y)
                if tile == 0:
                    gl_color = (0.25, 0.15, 0.51)
                else:
                    color = TILE_TO_COLOR[tile]
                    r, g, b = color 
                    gl_color = (r/255, g/255, b/255)
                px = x * self.tile_size
                py = y * self.tile_size
                self.renderer.draw_rect(px, py, self.tile_size, self.tile_size, gl_color)