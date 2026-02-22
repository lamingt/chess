import numpy as np

'''
    Moves are represented as 16 bit integers
    First 6 bits (0-5) represent the source square
    Next 6 bits (6-11) represent the target square
    Final 4 bits (12-15) are move flags:
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


def encode_move(source, target, flag) -> np.int16:
    return source | (target << 6) | (flag << 12)


def decode_source(move_int: np.int16):
    return move_int & 0x3F


def decode_target(move_int: np.int16):
    return (move_int >> 6) & 0x3F


def decode_flag(move_int: np.int16):
    return (move_int >> 12) & 0xF