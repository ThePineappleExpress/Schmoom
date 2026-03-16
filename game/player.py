import math
import pygame as pg
from engine.settings import LOOK_SENSIVITY, COLLISION_MARGIN, BOB_OFFSET


class Player:
    def __init__(self, x, y, angle):
        self.x = x
        self.y = y
        self.angle = angle
        self.vel_x = 0.0              # current velocity 
        self.vel_y = 0.0              # current velocity
        self.speed = 5.0             # max movement speed
        self.accel = 10.0             # acceleration rate
        self.friction = 0.15           # deceleration multiplier (0.0-1.0, like 0.85)
        self.rot_speed = 40.0         # rotation speed for mouse look
        self.bob_timer = 0.0        # accumulates over time while moving
        self.bob_amount = 0.0       # current vertical offset (pixels)
        self.bob_speed = 8.0        # how fast the bob cycles
        self.bob_intensity = BOB_OFFSET   # maximum pixel offset
        pg.mouse.set_visible(False)              # hide the cursor
        pg.event.set_grab(True)                  # trap mouse inside window
        pg.mouse.get_rel()                       # returns (dx, dy) since last call
    def update(self, dt, game):
        """Update player position and angle based on input and physics."""
        keys = pg.key.get_pressed()
        move_dir_x = 0
        move_dir_y = 0
        current_speed = math.hypot(self.vel_x, self.vel_y)
        # Determine movement direction based on WASD input
        if keys[pg.K_w]:
            move_dir_x += math.cos(self.angle) * dt
            move_dir_y += math.sin(self.angle) * dt
        if keys[pg.K_s]:
            move_dir_x -= math.cos(self.angle) * dt
            move_dir_y -= math.sin(self.angle) * dt
        if keys[pg.K_a]:
            move_dir_x += math.cos(self.angle - math.pi / 2) * dt
            move_dir_y += math.sin(self.angle - math.pi / 2) * dt
        if keys[pg.K_d]:
            move_dir_x += math.cos(self.angle + math.pi / 2) * dt
            move_dir_y += math.sin(self.angle + math.pi / 2) * dt

        # Update bobbing effect
        if current_speed > 0.1:    # small threshold, not 0
            self.bob_timer += dt * self.bob_speed
            self.bob_amount = math.sin(self.bob_timer) * self.bob_intensity * min(current_speed / self.speed, 1.0)
        else:
            self.bob_amount *= 0.9 ** (dt * 60)
            if abs(self.bob_amount) < 0.5:    # close enough to center, snap to 0
                self.bob_amount = 0
                self.bob_timer = 0

        # Normalize movement direction
        length = math.hypot(move_dir_x, move_dir_y)
        if length > 0:
            move_dir_x /= length
            move_dir_y /= length

        mouse_dx, mouse_dy = pg.mouse.get_rel()
        self.angle += mouse_dx * LOOK_SENSIVITY

        # Apply acceleration to velocity
        self.vel_x += move_dir_x * self.accel * dt
        self.vel_y += move_dir_y * self.accel * dt

        # Clamp velocity to max speed
        vel_length = math.hypot(self.vel_x, self.vel_y)
        if vel_length > self.speed:
            self.vel_x = (self.vel_x / vel_length) * self.speed
            self.vel_y = (self.vel_y / vel_length) * self.speed

        # Apply friction to velocity
        self.vel_x *= self.friction ** dt
        self.vel_y *= self.friction ** dt

        # Update position based on velocity
        new_x = self.x + self.vel_x * dt
        new_y = self.y + self.vel_y * dt

        # Check with margin in the direction of movement
        check_x = new_x + COLLISION_MARGIN if self.vel_x > 0 else new_x - COLLISION_MARGIN
        check_y = new_y + COLLISION_MARGIN if self.vel_y > 0 else new_y - COLLISION_MARGIN

        if not game.game_map.is_wall(int(check_x), int(self.y)):
            self.x = new_x
        else:
            self.vel_x = 0

        if not game.game_map.is_wall(int(self.x), int(check_y)):
            self.y = new_y
        else:
            self.vel_y = 0
