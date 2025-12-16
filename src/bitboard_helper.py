import numpy as np

def get_msb_index(bitboard: np.uint64) -> int:
    if bitboard == 0:
        return -1
    
    return int(bitboard).bit_length() - 1

def get_lsb_index(bitboard: np.uint64) -> int:
    if bitboard == 0:
        return -1
    
    lsb_uint64 = bitboard & -bitboard
    
    return int(lsb_uint64).bit_length() - 1