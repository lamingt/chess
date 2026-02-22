from enum import IntEnum

GAME_WIDTH = 640
GAME_HEIGHT = 640
GAME_SQUARE_SIZE = GAME_WIDTH // 8

class Piece(IntEnum):
    PAWN = 0
    KNIGHT = 1
    BISHOP = 2
    ROOK = 3
    QUEEN = 4
    KING = 5
    
    def to_char(self) -> str:
        if self == Piece.PAWN:
            return "p"
        elif self == Piece.KNIGHT:
            return "n"
        elif self == Piece.BISHOP:
            return "b"
        elif self == Piece.ROOK:
            return "r"
        elif self == Piece.QUEEN:
            return "q"
        elif self == Piece.KING:
            return "k"
        else:
            return ""
        
        
class Colour(IntEnum):
    WHITE = 0
    BLACK = 1

    def to_char(self) -> str:
        if self == Colour.WHITE:
            return "w"
        elif self == Colour.BLACK:
            return "b"
        else:
            return ""
        
    @property
    def opposite(self):
        return Colour(self.value ^ 1)
        
        
class Rank(IntEnum):
    ONE = 0
    TWO = 1
    THREE = 2
    FOUR = 3
    FIVE = 4
    SIX = 5
    SEVEN = 6
    EIGHT = 7
  
    
class File(IntEnum):
    A = 0
    B = 1
    C = 2
    D = 3
    E = 4
    F = 5
    G = 6
    H = 7
   
    
class Direction(IntEnum):
    N = 0
    NE = 1
    E = 2
    SE = 3
    S = 4
    SW = 5
    W = 6
    NW = 7
    
    @property
    def opposite(self):
        if self.value - 4 >= 0:
            return Direction(self.value - 4)
        else:
            return Direction(self.value + 4)
    
class Castling(IntEnum):
    WK = 1
    WQ = 2
    BK = 4
    BQ = 8
    

'''
    0 	0 	0 	0 	0 	quiet moves
    1 	0 	0 	0 	1 	double pawn push
    2 	0 	0 	1 	0 	king castle
    3 	0 	0 	1 	1 	queen castle
    4 	0 	1 	0 	0 	captures
    5 	0 	1 	0 	1 	ep-capture
    8 	1 	0 	0 	0 	knight-promotion
    9 	1 	0 	0 	1 	bishop-promotion
    10 	1 	0 	1 	0 	rook-promotion
    11 	1 	0 	1 	1 	queen-promotion
    12 	1 	1 	0 	0 	knight-promo capture
    13 	1 	1 	0 	1 	bishop-promo capture
    14 	1 	1 	1 	0 	rook-promo capture
    15 	1 	1 	1 	1 	queen-promo capture 
'''

class MoveFlags(IntEnum):
    QUIET = 0
    DBL_PAWN_PUSH = 1
    KING_CASTLE = 2
    QUEEN_CASTLE = 3
    CAPTURE = 4
    EP_CAPTURE = 5
    KNIGHT_PROMOTION = 8
    BISHOP_PROMOTION = 9
    ROOK_PROMOTION = 10
    QUEEN_PROMOTION = 11
    KNIGHT_PROMOTION_CAPTURE = 12
    BISHOP_PROMOTION_CAPTURE = 13
    ROOK_PROMOTION_CAPTURE = 14
    QUEEN_PROMOTION_CAPTURE = 15