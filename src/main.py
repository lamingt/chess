from renderer import Renderer
from board import Board
from move_generator import MoveGenerator
import pygame

if __name__ == "__main__":
    board = Board()
    move_generator = MoveGenerator()
    game = Renderer(board, move_generator)
    game.run()

    