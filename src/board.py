import numpy as np
from constants import Piece, Colour

"""
56 57 58 59 60 61 62 63         A8 B8 C8 D8 E8 F8 G8 H8
48 49 50 51 52 53 54 55         A7 B7 C7 D7 E7 F7 G7 H7
40 41 42 43 44 45 46 47         A6 B6 C6 D6 E6 F6 G6 H6
32 33 34 35 36 37 38 39    =    A5 B5 C5 D5 E5 F5 G5 H5
24 25 26 27 28 29 30 31         A4 B4 C4 D4 E4 F4 G4 H4
16 17 18 19 20 21 22 23         A3 B3 C3 D3 E3 F3 G3 H3
 8  9 10 11 12 13 14 15         A2 B2 C2 D2 E2 F2 G2 H2
 0  1  2  3  4  5  6  7         A1 B1 C1 D1 E1 F1 G1 H1
"""

class Board:
    def __init__(self):
        # Index 0 for white piece, index 1 for black Piece. Each colour has 6 bitboards 
        self.bitboards = np.zeros((2,6), dtype=np.uint64) 
        
        self.reset_board()
        
    def reset_board(self):
        self.bitboards.fill(0)
        
        self.bitboards[Colour.WHITE][Piece.PAWN] = np.uint64(0b11111111) << np.uint64(8)
        self.bitboards[Colour.BLACK][Piece.PAWN] = np.uint64(0b11111111) << np.uint64(48)
        
        self.bitboards[Colour.WHITE][Piece.KNIGHT] = np.uint64(0b01000010)
        self.bitboards[Colour.BLACK][Piece.KNIGHT] = np.uint64(0b01000010) << np.uint64(56)
        
        self.bitboards[Colour.WHITE][Piece.BISHOP] = np.uint64(0b00100100)
        self.bitboards[Colour.BLACK][Piece.BISHOP] = np.uint64(0b00100100) << np.uint64(56)
       
        self.bitboards[Colour.WHITE][Piece.ROOK] = np.uint64(0b10000001)
        self.bitboards[Colour.BLACK][Piece.ROOK] = np.uint64(0b10000001) << np.uint64(56)
         
        self.bitboards[Colour.WHITE][Piece.QUEEN] = np.uint64(0b00010000)
        self.bitboards[Colour.BLACK][Piece.QUEEN] = np.uint64(0b00010000) << np.uint64(56)
        
        self.bitboards[Colour.WHITE][Piece.KING] = np.uint64(0b00001000)
        self.bitboards[Colour.BLACK][Piece.KING] = np.uint64(0b00001000) << np.uint64(56)
        
    def get_occupancy(self) -> np.uint64:
        return np.bitwise_or.reduce(self.bitboards, axis=None)