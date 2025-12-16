import numpy as np
from constants import Piece, Colour
from move_generator import MoveGenerator

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
        # Square index which a pawn can move to in order to en passant
        self.ep_target = -1
        
        # Castling is representing as four bits, starting at 0b1111
        # 0001 = White King Side
        # 0010 = White Queen Side
        # 0100 = Black King Side
        # 1000 = Black Queen Side
        self.castling_rights = 0b1111
        
        self.castling_masks = [0b1111] * 64
        # A1, remove white queen side castling
        self.castling_masks[0] = 0b1101
        # E1, remove all white castling
        self.castling_masks[4] = 0b1100
        # H1, remove white king side castling
        self.castling_masks[7] = 0b1110
        # A8, remove black queen side castling
        self.castling_masks[56] = 0b1011
        # E8, remove all black castling
        self.castling_masks[60] = 0b0011
        # H8, remove black king side castling
        self.castling_masks[63] = 0b1011
        
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
         
        self.bitboards[Colour.WHITE][Piece.QUEEN] = np.uint64(0b00001000)
        self.bitboards[Colour.BLACK][Piece.QUEEN] = np.uint64(0b00001000) << np.uint64(56)
        
        self.bitboards[Colour.WHITE][Piece.KING] = np.uint64(0b00010000)
        self.bitboards[Colour.BLACK][Piece.KING] = np.uint64(0b00010000) << np.uint64(56)
        
    def get_occupancy(self) -> np.uint64:
        return np.bitwise_or.reduce(self.bitboards, axis=None)
    
    def get_colour_occupancy(self, colour: Colour) -> np.uint64:
        return np.bitwise_or.reduce(self.bitboards[colour], axis=None)
    
    def make_move(self, source: int, dest: int) -> None:
        moved_piece_type = None
        moved_piece_colour = None
        found = False
        
        # Finding piece and colour of source square
        for colour in Colour:
            for piece in Piece:
                if (self.bitboards[colour][piece] >> np.uint64(source)) & np.uint64(1):
                    found = True
                    moved_piece_type = piece
                    moved_piece_colour = colour
                    break
            if found:
                break
            
        if found is None or moved_piece_type is None or moved_piece_colour is None:
            return
        
        move_generator = MoveGenerator()
        legal_moves = move_generator.get_pseudo_legal_moves(self, moved_piece_type, moved_piece_colour, source)
        if not (legal_moves & (np.uint64(1) << dest)):
            return
        
        # Checking capture of own pieces
        for piece in Piece:
            if (self.bitboards[moved_piece_colour][piece] >> np.uint64(dest)) & np.uint64(1):
                return
        
        # Capturing opponent pieces
        opponent_colour = Colour.WHITE if moved_piece_colour == Colour.BLACK else Colour.BLACK
        for piece in Piece:
            if (self.bitboards[opponent_colour][piece] >> np.uint64(dest)) & np.uint64(1):
                self.bitboards[opponent_colour][piece] ^= (np.uint64(1) << np.uint64(dest))
                
        # Taking en passant
        if moved_piece_type == Piece.PAWN and dest == self.ep_target:
            opposite_pawn_index = self.ep_target - 8 if moved_piece_colour == Colour.WHITE else self.ep_target + 8
            self.bitboards[opponent_colour][Piece.PAWN] ^= np.uint64(1) << opposite_pawn_index

        # Maintaing en passant data
        self.ep_target = -1
        if moved_piece_type == Piece.PAWN and moved_piece_colour == Colour.WHITE and dest - source == 16:
            self.ep_target = source + 8
        elif moved_piece_type == Piece.PAWN and moved_piece_colour == Colour.BLACK and source - dest == 16:
            self.ep_target = source - 8
        
        # Updates castling rights. Checking source handles movements of king/rook, and checking dest
        # handles capture of rooks
        self.castling_rights &= self.castling_masks[source] & self.castling_masks[dest] 
        
        # If move is a castle, we move the rook too
        if moved_piece_type == Piece.KING and moved_piece_colour == Colour.WHITE:
            # White king side castle
            if source == 4 and dest == 6:
                self.bitboards[moved_piece_colour][Piece.ROOK] ^= (np.uint64(1) << 5) | (np.uint64(1) << 7)
            # White queen side castle
            elif source == 4 and dest == 2:
                self.bitboards[moved_piece_colour][Piece.ROOK] ^= (np.uint64(1) << 3) | np.uint64(1)
        elif moved_piece_type == Piece.KING and moved_piece_colour == Colour.BLACK:
            # Black king side castle
            if source == 60 and dest == 62:
                self.bitboards[moved_piece_colour][Piece.ROOK] ^= (np.uint64(1) << 61) | (np.uint64(1) << 63)
            # Black queen side castle
            elif source == 60 and dest == 58:
                self.bitboards[moved_piece_colour][Piece.ROOK] ^= (np.uint64(1) << 59) | (np.uint64(1) << 56)
        
        
        # Promotion of a pawn. We autoqueen for now
        if moved_piece_type == Piece.PAWN and ((moved_piece_colour == Colour.WHITE and 56 <= dest <= 64) or (moved_piece_colour == Colour.BLACK and 0 <= dest <= 7)):
            self.bitboards[moved_piece_colour][moved_piece_type] ^= (np.uint64(1)) << np.uint64(source)
            self.bitboards[moved_piece_colour][Piece.QUEEN] ^= np.uint64(1) << np.uint64(dest)
        # Moving the piece
        else:
            self.bitboards[moved_piece_colour][moved_piece_type] ^= ((np.uint64(1)) << np.uint64(source)) | (np.uint64(1) << np.uint64(dest))