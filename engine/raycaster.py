
import math
from engine.settings import *

def cast_single_ray(game, ray_angle):
    """Cast a single ray and return the distance to the first wall hit."""
    # This is where the DDA algorithm will go in later sessions.
    ray_dir_x = math.cos(ray_angle)
    ray_dir_y = math.sin(ray_angle)

    game_map_x = int(game.player.x)
    game_map_y = int(game.player.y)

    delta_dist_x = abs(1/ ray_dir_x) if ray_dir_x != 0 else float('inf')
    delta_dist_y = abs(1/ ray_dir_y) if ray_dir_y != 0 else float('inf')

    # Determine step direction and initial side distances
    if ray_dir_x < 0:
        step_x = -1
        side_dist_x = (game.player.x - game_map_x) * delta_dist_x
    else:
        step_x = 1
        side_dist_x = (game_map_x + 1.0 - game.player.x) * delta_dist_x
    
    if ray_dir_y < 0:
        step_y = -1
        side_dist_y = (game.player.y - game_map_y) * delta_dist_y
    else:
        step_y = 1
        side_dist_y = (game_map_y + 1.0 - game.player.y) * delta_dist_y
    
    # DDA loop
    while True:
        if side_dist_x < side_dist_y:
            side_dist_x += delta_dist_x
            game_map_x += step_x
            hit_side = 0 # vertical wall
        else:
            side_dist_y += delta_dist_y
            game_map_y += step_y
            hit_side = 1 # horizontal wall

        if game.game_map.is_wall(game_map_x, game_map_y):
            break

    # Calculate distance to the wall hit
    if hit_side == 0:
        perp_dist = side_dist_x - delta_dist_x
    else:
        perp_dist = side_dist_y - delta_dist_y

    wall_type = game.game_map.get_tile(game_map_x, game_map_y)

    if hit_side == 0:
        hit_point = game.player.y + perp_dist * ray_dir_y
    else:
        hit_point = game.player.x + perp_dist * ray_dir_x
    texture_x_offset =  hit_point - int(hit_point)  # Fractional part for texture game_mapping

    return (perp_dist, hit_side, wall_type, texture_x_offset)
