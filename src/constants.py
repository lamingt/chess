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