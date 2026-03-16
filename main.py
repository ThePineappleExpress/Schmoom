"""
main.py — Entry point for the Doom-style raycaster.

This file does ONE thing: create a Game and run it.
All logic lives in the game/ and engine/ packages.
"""

from game.game import Game

if __name__ == "__main__":
    Game().run()