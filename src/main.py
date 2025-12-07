from renderer import Renderer
from board import Board
import pygame

if __name__ == "__main__":
    board = Board()
    game = Renderer(board)
    game.run()

    