import numpy as np
from constants import Colour, Piece, Rank, File, Direction, Castling
from bitboard_helper import get_lsb_index, get_msb_index

from typing import TYPE_CHECKING # Import this helper

# Only import Board if we are just checking types (not running code)
if TYPE_CHECKING:
    from board import Board
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
RANK_MASK = np.array(
    [np.uint64(0x00000000000000FF) << np.uint64(i * 8) for i in range(8)], 
    dtype=np.uint64
    )

FILE_MASK = np.array(
    [np.uint64(0x0101010101010101) << np.uint64(i) for i in range(8)],
    dtype=np.uint64
)

class MoveGenerator:
    def __init__(self):
        self.knight_moves = [np.uint64(0)] * 64
        self.king_moves = [np.uint64(0)] * 64
        self.rays = [[np.uint64(0)] * 8 for _ in range(64)] 
        
        self.not_a_file = ~FILE_MASK[File.A]
        self.not_h_file = ~FILE_MASK[File.H]
        self.not_ab_file = ~(FILE_MASK[File.A] | FILE_MASK[File.B])
        self.not_gh_file = ~(FILE_MASK[File.G] | FILE_MASK[File.H])
        
        self._init_king_moves()
        self._init_knight_moves()
        self._init_rays()
        
    
    def _init_rays(self):
        for square in range(64):
            row = square // 8
            col = square % 8
            
            # North
            for i in range(row + 1, 8):
                self.rays[square][Direction.N] |= np.uint64(1) << (i * 8 + col)
            
            # East
            for i in range(col + 1, 8):
                self.rays[square][Direction.E] |= np.uint64(1) << (row * 8 + i)
                
            # South
            for i in range(row - 1, -1, -1):
                self.rays[square][Direction.S] |= np.uint64(1) << (i * 8 + col)
            
            # West
            for i in range(col - 1, -1, -1):
                self.rays[square][Direction.W] |= np.uint64(1) << (row * 8 + i)
                
            # North East
            for i in range(1, 8):
                new_row = row + i
                new_col = col + i
                if new_row < 8 and new_col < 8:
                    self.rays[square][Direction.NE] |= np.uint64(1) << (new_row * 8 + new_col)
                    
            # South East
            for i in range(1, 8):
                new_row = row - i
                new_col = col + i
                if new_row >= 0 and new_col < 8:
                    self.rays[square][Direction.SE] |= np.uint64(1) << (new_row * 8 + new_col)
                    
            # South West
            for i in range(1, 8):
                new_row = row - i
                new_col = col - i
                if new_row >= 0 and new_col >= 0:
                    self.rays[square][Direction.SW] |= np.uint64(1) << (new_row * 8 + new_col)
                    
            # North West
            for i in range(1, 8):
                new_row = row + i
                new_col = col - i
                if new_row < 8 and new_col >= 0:
                    self.rays[square][Direction.NW] |= np.uint64(1) << (new_row * 8 + new_col)
           
    
    def _init_knight_moves(self):
        for square in range(64):
            pos = np.uint64(1) << square
            moves = np.uint64(0)
            
            # South Movements
            moves |= (pos & self.not_a_file) >> 17
            moves |= (pos & self.not_ab_file) >> 10
            moves |= (pos & self.not_h_file) >> 15
            moves |= (pos & self.not_gh_file) >> 6
            
            # North Movements
            moves |= (pos & self.not_h_file) << 17
            moves |= (pos & self.not_gh_file) << 10
            moves |= (pos & self.not_a_file) << 15
            moves |= (pos & self.not_ab_file) << 6
            
            self.knight_moves[square] = moves
    
    
    def _init_king_moves(self):
        for square in range(64):
            pos = np.uint64(1) << square
            moves = np.uint64(0)
            
            # Vertical and Horizontal Movements
            moves |= pos >> 8
            moves |= pos << 8 
            moves |= (pos & self.not_h_file) << 1
            moves |= (pos & self.not_a_file) >> 1
            
            # Diagonal Movements
            moves |= (pos & self.not_a_file) << 7
            moves |= (pos & self.not_a_file) >> 9
            moves |= (pos & self.not_h_file) << 9 
            moves |= (pos & self.not_h_file) >> 7 
            
            self.king_moves[square] = moves
            
    
    def _get_sliding_moves(self, board: "Board", piece: Piece, squareIndex: int) -> np.uint64:
        '''
            Plan:
            Iterate through the directions
            I use self.rays along with the direction to figure out possible moves
            If direction is NW, N, NE, E, then I use MSB on occupancy & ray to find
            the first square in that direction that is blocked
            If direction is W, Sw, S, SE, then I use LSB. 
            
            Using the blocked index, we take the ray in the same direction, then xor this
            with the original to find the valid moves.
            
            We leave in the blocked index as this may be a capturable piece. When retrieving moves,
            we remove all moves that capture our own piece
        '''
        moves = np.uint64(0)
        
        match piece:
            case Piece.BISHOP:
                dirs = [Direction.NE, Direction.SE, Direction.SW, Direction.NW]
            case Piece.ROOK:
                dirs = [Direction.N, Direction.S, Direction.W, Direction.E]
            case Piece.QUEEN:
                dirs = [Direction.NE, Direction.SE, Direction.SW, Direction.NW, Direction.N, Direction.S, Direction.W, Direction.E]
            case _:
                return np.uint64(0)
        
        POS_DIR = [Direction.NW, Direction.N, Direction.NE, Direction.E]
        for dir in dirs:
            blocked_bits = board.get_occupancy() & self.rays[squareIndex][dir]
            if blocked_bits == 0:
                moves |= self.rays[squareIndex][dir]
                continue
            blocker_bit = get_lsb_index(blocked_bits) if dir in POS_DIR else get_msb_index(blocked_bits)
            
            blocked_moves = self.rays[blocker_bit][dir]
            moves |= self.rays[squareIndex][dir] ^ blocked_moves
            
        return moves 
            

    def generate_pawn_moves(self, board: "Board", piece: Piece, colour: Colour, squareIndex: int) -> np.uint64:
        '''
            We need to handle
            1. Moving pawn forward by one square if the square infront is empty
            2. Moving two squares forward if the pawn is white and on rank 2, or black and on rank 7
            3. Capturing diagonally if an enemy piece is on those squares
            4. En passant. We need to maintain a square which can be en passanted through history in the board when
            a pawn is pushed two squares. Maintaining the ep target variable is done entirely in the make move function
            5. Promotion. After the move, we check if it is white on rank 8, or black on rank 7. I need to construct
            a UI for promotion so that the user can select which piece to promote with. This will also be done in make move.
        '''
        moves = np.uint64(0)
        pos = np.uint64(1) << squareIndex
        occupancy = board.get_occupancy()
        opponent_occupancy = board.get_colour_occupancy(Colour.WHITE) if colour == Colour.BLACK else board.get_colour_occupancy(Colour.BLACK)
        if colour == Colour.WHITE:
            infront = pos << 8
            two_infront = infront << 8
            left_diagonal = pos << 7
            right_diagonal = pos << 9
            # Moving one square forward
            if occupancy & infront == 0:
                moves |= infront
            # Moving two squares forward
            if (occupancy & two_infront == 0) and (pos & RANK_MASK[Rank.TWO] != 0):
                moves |= two_infront
                
            # Including en passant in captures
            if board.ep_target != -1:
                opponent_occupancy |= np.uint64(1) << board.ep_target
            # Capturing left diagonal
            if (pos & self.not_a_file) and (opponent_occupancy & left_diagonal):
                moves |= left_diagonal
            # Capturing right diagonal
            if (pos & self.not_h_file) and (opponent_occupancy & right_diagonal):
                moves |= right_diagonal 
        elif colour == Colour.BLACK:
            infront = pos >> 8
            two_infront = infront >> 8
            left_diagonal = pos >> 9
            right_diagonal = pos >> 7
            # Moving one square forward
            if occupancy & infront == 0:
                moves |= infront
            # Moving two squares forward
            if (occupancy & two_infront == 0) and (pos & RANK_MASK[Rank.SEVEN] != 0):
                moves |= two_infront
                
            # Including en passant in captures
            if board.ep_target != -1:
                opponent_occupancy |= np.uint64(1) << board.ep_target
            # Capturing left diagonal
            if (pos & self.not_a_file) and (opponent_occupancy & left_diagonal):
                moves |= left_diagonal
            # Capturing right diagonal
            if (pos & self.not_h_file) and (opponent_occupancy & right_diagonal):
                moves |= right_diagonal
 
        return moves
 
 
    def generate_castling_moves(self, board: "Board", colour: Colour) -> np.uint64:
        castling_rights = board.castling_rights
        moves = np.uint64(0)
        occupancy = board.get_occupancy()
        
        if colour == Colour.WHITE:
            # Check white king side
            if (Castling.WK & castling_rights) and (occupancy & np.uint64(0b01100000) == 0):
                moves |= np.uint64(1) << 6
            # Check white queen side
            if (Castling.WQ & castling_rights) and (occupancy & np.uint64(0b00001110) == 0):
                moves |= np.uint64(1) << 2
        elif colour == Colour.BLACK:
            # Check black king side
            if (Castling.BK & castling_rights) and (occupancy & (np.uint64(0b01100000) << 56) == 0):
                moves |= np.uint64(1) << 62
            # Check black queen side
            if (Castling.BQ & castling_rights) and (occupancy & (np.uint64(0b00001110) << 56) == 0):
                moves |= np.uint64(1) << 58
                
        return moves
    
 
    def get_pseudo_legal_moves(self, board: "Board", piece: Piece, colour: Colour, squareIndex: int) -> np.uint64:
        match piece:
            case Piece.PAWN:
                moves = self.generate_pawn_moves(board, piece, colour, squareIndex)
            case Piece.KNIGHT:
                moves = self.knight_moves[squareIndex]
            case Piece.BISHOP:
                moves = self._get_sliding_moves(board, piece, squareIndex)
            case Piece.ROOK:
                moves = self._get_sliding_moves(board, piece, squareIndex)
            case Piece.QUEEN:
                moves = self._get_sliding_moves(board, piece, squareIndex)
            case Piece.KING:
                moves = self.king_moves[squareIndex] | self.generate_castling_moves(board, colour)
        
        colour_occupancy = board.get_colour_occupancy(colour)
        return moves & ~colour_occupancy
        