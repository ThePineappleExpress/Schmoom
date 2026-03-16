"""
game/game.py — Main Game class with a fixed-timestep game loop.

THE FIXED-TIMESTEP LOOP:
========================
Most tutorials use a simple loop:

    while running:
        dt = clock.tick(60) / 1000
        update(dt)
        render()

This ties physics to frame rate. If a frame takes longer (lag spike),
dt is huge and objects teleport. If the machine is fast, physics runs
too often and wastes CPU.

The FIXED-TIMESTEP pattern decouples physics from rendering:

    accumulator = 0.0
    while running:
        frame_time = clock.tick() / 1000    # real elapsed time
        accumulator += frame_time

        while accumulator >= DT:            # drain in fixed-size chunks
            update(DT)                      # physics always sees DT = 1/60
            accumulator -= DT

        render()                            # render at whatever FPS we get

Benefits:
- Physics is deterministic (always same DT)
- Works identically on fast and slow machines
- No tunneling through walls on lag spikes
- Render can run faster than physics for smooth visuals

The accumulator holds "leftover" time that hasn't been simulated yet.
If the machine can't keep up, we cap frame_time to prevent a death spiral
(where each frame takes longer → more physics ticks → even longer frames).
"""

import sys
import pygame

from OpenGL.GL import *
from engine.settings import *
from engine.shader import ShaderLoader
from engine.renderer import Renderer
from engine.framebuffer import Framebuffer
from game.maps import Map
from game.player import Player

class Game:
    """Top-level game object. Owns the loop, renderer, and all game state."""

    def __init__(self):
        pygame.init()
        self.renderer = Renderer()
        self.clock = pygame.time.Clock()
        self.running = True
        self.dt = DT
        self.game_map = Map("assets/maps/map.png")
        self.renderer.generate_map_texture(self.game_map) 
        #self.debug_view = DebugView(self.game_map, self.renderer)
        #self.debug_view_state = False
        spawn = self.game_map.player_spawn
        self.player = Player(spawn[0] + 0.5, spawn[1] + 0.5, 0)
        self.shader = ShaderLoader("assets/shaders/fullscreen.vert", "assets/shaders/raycaster.frag")
        self.shader_post = ShaderLoader("assets/shaders/fullscreen.vert", "assets/shaders/postprocess.frag")

        self.framebuffer = Framebuffer(WIDTH, HEIGHT)

    def handle_events(self):
        """Process all pending Pygame events.

        Called once per frame (not per physics tick) because input events
        are a per-frame concern, not a physics concern.
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F5:
                    self.shader = ShaderLoader("assets/shaders/fullscreen.vert", "assets/shaders/raycaster.frag")
                    self.shader_post = ShaderLoader("assets/shaders/fullscreen.vert", "assets/shaders/postprocess.frag")
                if event.key == pygame.K_ESCAPE:
                    self.running = False
               # if event.key == pygame.K_TAB:
                #    self.debug_view_state = not self.debug_view_state

    def update(self, dt: float):
        """Update game logic. Called at a fixed rate (60 Hz).

        Args:
            dt: Fixed timestep in seconds (1/60 ≈ 0.01667).
                Always the same value — that's the point of fixed timestep.

        This is where player movement, enemy AI, physics, etc. will go.
        For now it's empty — we'll add systems in later sessions.
        """
        self.player.update(dt, self)

    def render(self):
        """Draw everything to the screen. Called once per frame.

        Render order (back to front):
        1. Clear screen
        2. Sky / ceiling        (Session 6)
        3. Walls via raycasting (Session 4)
        4. Floor                (Session 6)
        5. Sprites / enemies    (Session 7)
        6. Weapon overlay       (Session 9)
        7. HUD                  (Session 9)
        8. Swap buffers
        """
        self.framebuffer.bind()
        self.renderer.begin_frame()
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.renderer.map_tex)
        self.shader.use()
        self.shader.set_uniform("u_map_tex", 0)
        self.shader.set_uniform("u_player_pos", (self.player.x, self.player.y))
        self.shader.set_uniform("u_player_angle", float(self.player.angle))
        self.shader.set_uniform("u_resolution", (float(WIDTH), float(HEIGHT)))
        self.shader.set_uniform("u_map_size", (float(self.game_map.width), float(self.game_map.height)))
        self.shader.set_uniform("u_fov", float(FOV))
        self.shader.set_uniform("u_bob_offset", float(self.player.bob_amount))
        self.shader.set_uniform("u_time", pygame.time.get_ticks() / 1000.0)
        for i, light in enumerate(self.game_map.lights):
            self.shader.set_uniform(f"u_lights[{i}]", (light[0] + 0.5, light[1] + 0.5, 1.0))
        self.shader.set_uniform("u_num_lights", len(self.game_map.lights))
        self.renderer.draw_fullscreen()
        self.framebuffer.unbind()
        self.renderer.begin_frame()
        self.shader_post.use()
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.framebuffer.texture)
        self.shader_post.set_uniform("u_scene", 0)
        self.renderer.draw_fullscreen()

        self.renderer.end_frame()

    def run(self):
        """Main game loop using fixed-timestep accumulator.

        This is the heart of the engine. Study the flow:

        1. Measure real elapsed time since last frame (frame_time)
        2. Add it to the accumulator
        3. While accumulator has enough time for a physics tick:
             - Run update(DT) with the fixed timestep
             - Subtract DT from accumulator
        4. Render once
        5. Repeat

        The clock.tick(FPS) call also caps frame rate to prevent
        wasting CPU/GPU when rendering faster than the monitor.
        """
        accumulator = 0.0

        while self.running:
            # ── Measure real time since last frame ───────────────────
            # clock.tick(FPS) returns milliseconds; convert to seconds.
            # It also sleeps to cap at FPS if we're rendering too fast.
            frame_time = self.clock.tick(FPS) / 1000.0

            # Cap frame_time to prevent "death spiral":
            # If a frame takes 2 seconds (alt-tab, breakpoint, etc.),
            # without this cap we'd run 120 physics ticks to catch up,
            # which takes even longer, which means more catching up...
            if frame_time > 0.25:
                frame_time = 0.25

            # ── Accumulate real time ─────────────────────────────────
            accumulator += frame_time

            # ── Process input (once per frame) ───────────────────────
            self.handle_events()

            # ── Fixed-timestep physics updates ───────────────────────
            while accumulator >= self.dt:
                self.update(self.dt)
                accumulator -= self.dt

            # ── Render (once per frame) ──────────────────────────────
            self.render()

        # ── Cleanup ──────────────────────────────────────────────────
        pygame.quit()
        sys.exit()
