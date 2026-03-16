"""
engine/renderer.py — OpenGL setup and low-level drawing helpers.

WHAT THIS DOES:
- Creates the OpenGL-capable Pygame window
- Sets up an ORTHOGRAPHIC projection (not perspective!)
- Provides begin_frame() / end_frame() for the game loop
- Will grow to include draw_rect, draw_textured_quad, etc. in later sessions

WHY ORTHOGRAPHIC?
A raycaster doesn't use OpenGL's 3D perspective at all. We compute our own
projection (wall strip heights from ray distances) and draw everything as
2D rectangles in screen space. So we set up glOrtho with coordinates that
map 1:1 to pixels: (0,0) at top-left, (WIDTH, HEIGHT) at bottom-right.
"""

import array

import ctypes
import pygame as pg
from pygame.locals import DOUBLEBUF, OPENGL
from OpenGL.GL import *
from OpenGL.GLU import *

from engine.settings import WIDTH, HEIGHT, COLOR_CLEAR




class Renderer:
    def __init__(self):
        pg.init()
        pg.display.set_mode((WIDTH, HEIGHT), OPENGL | DOUBLEBUF)
        pg.display.init()
        info = pg.display.Info()    
        vertices = array.array('f', [
            -1, 1, 0, 1,   1, -1, 1, 0,   -1, -1, 0, 0,  # T1
            -1, 1, 0, 1,   1,  1, 1, 1,    1, -1, 1, 0,   # T2
        ])
        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)
        self.vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, vertices.tobytes(), GL_STATIC_DRAW)
        glClearColor(*COLOR_CLEAR)

        # Attribute 0: position (x, y) — starts at byte 0
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 16, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)

        # Attribute 1: UV (u, v) — starts at byte 8
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 16, ctypes.c_void_p(8))
        glEnableVertexAttribArray(1)

    def begin_frame(self):
        glClear(GL_COLOR_BUFFER_BIT)
    
    def end_frame(self):
        pg.display.flip()

    def draw_fullscreen(self):
        glBindVertexArray(self.vao)
        glDrawArrays(GL_TRIANGLES, 0, 6)

    def generate_map_texture(self, game_map):
        """Generate a texture from the map grid for debugging purposes."""
        data = bytes([tile for row in game_map.grid for tile in row])
        texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture_id)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_R8, game_map.width, game_map.height, 0, GL_RED, GL_UNSIGNED_BYTE, data)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        self.map_tex = texture_id