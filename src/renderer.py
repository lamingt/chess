import pygame
import numpy as np
from pathlib import Path
from board import Board
from constants import GAME_HEIGHT, GAME_WIDTH, GAME_SQUARE_SIZE, Piece, Colour

class Renderer:
    def __init__(self, board: Board):
        self.board = board

        pygame.init()
        self.screen = pygame.display.set_mode((GAME_WIDTH, GAME_HEIGHT))
        pygame.display.set_caption("Chess")
        self.clock = pygame.time.Clock()
        
        self.images = {}
        self.pieces = {}
        self.active_piece_index = None
        self.load_assets()
        
    def load_assets(self):
        for colour in Colour:
            for piece in Piece:
                key = (colour, piece)
                script_dir = Path(__file__).resolve().parent
                asset_path = script_dir / "./assets"
                try:
                    img = pygame.image.load(f"{asset_path}/{colour.to_char()}{piece.to_char().upper()}.png").convert_alpha()
                    self.images[key] = pygame.transform.scale(img, (GAME_SQUARE_SIZE, GAME_SQUARE_SIZE));
                except:
                    print(f"Failed to load image from path: {asset_path}");
                    self.images[key] = None
                
    
    def draw_squares(self):
        colours = [pygame.Color(238, 238, 210), pygame.Color(118, 150, 86)]
        
        for row in range(8):
            for col in range(8):
                colour = colours[(row + col) % 2]
                pygame.draw.rect(self.screen, colour, (row * GAME_SQUARE_SIZE, col * GAME_SQUARE_SIZE, GAME_SQUARE_SIZE, GAME_SQUARE_SIZE))
    
    def draw_pieces(self):
        active_piece_data = None
        for colour in Colour:
            for piece in Piece:
                bitboard = self.board.bitboards[colour][piece]
                if bitboard == 0: continue
                
                for square in range(64):
                    if (bitboard >> np.uint64(square)) & np.uint64(1) == 1:
                        if square == self.active_piece_index:
                            # Saving information so the active piece has a higher z-index than other pieces
                            # when it is drawn last
                            active_piece_data = (colour, piece)
                        else:
                            self.draw_single_piece(square, colour, piece)
        
        if active_piece_data is not None and self.active_piece_index is not None:
            colour, piece = active_piece_data
            self.draw_single_piece(self.active_piece_index, colour, piece)
                        
    def draw_single_piece(self, square: int, colour: Colour, piece: Piece):
        if square == self.active_piece_index:
            img = self.images[(colour, piece)]
            self.screen.blit(img, self.pieces[square])
        else:
            col = square % 8
            row = 7 - (square // 8)
            x = col * GAME_SQUARE_SIZE
            y = row * GAME_SQUARE_SIZE

            img = self.images[(colour, piece)]
            if img:
                self.pieces[square] = pygame.Rect(x, y, GAME_SQUARE_SIZE, GAME_SQUARE_SIZE)
                self.screen.blit(img, (x, y))
    
    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for square in range(64):
                        if ((self.board.get_occupancy() >> np.uint64(square)) & np.uint64(1)) and self.pieces[square].collidepoint(event.pos):
                            self.active_piece_index = square
                            break
                elif event.type == pygame.MOUSEMOTION:
                    if self.active_piece_index is not None:
                        self.pieces[self.active_piece_index].move_ip(event.rel)
                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    if self.active_piece_index is None:
                        continue
                    
                    x, y = event.pos
                    col = x // GAME_SQUARE_SIZE
                    row = y // GAME_SQUARE_SIZE
                    if 0 <= col < 8 and 0 <= row < 8:
                        rank = 7 - row
                        new_square_index = rank * 8 + col
                        if new_square_index != self.active_piece_index:
                            self.board.make_move(self.active_piece_index, new_square_index)
                    
                    self.active_piece_index = None
                    
                
            self.draw_squares()
            self.draw_pieces()
            
            pygame.display.flip()
            self.clock.tick(60)
            
        
        

