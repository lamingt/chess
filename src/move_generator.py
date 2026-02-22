import numpy as np
from constants import Colour, Piece, Rank, File, Direction, Castling, MoveFlags
from bitboard_helper import get_lsb_index, get_msb_index
from typing import TYPE_CHECKING
from move import encode_move

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
        self.knight_moves = np.zeros(64, dtype=np.uint64) 
        self.king_moves = np.zeros(64, dtype=np.uint64) 
        self.pawn_attacks = np.zeros((2,64), dtype=np.uint64) 
        # doesn't include starting square, includes end square
        self.rays = np.zeros((64,8), dtype=np.uint64) 
        self.between = np.zeros((64, 64), dtype=np.uint64)
        
        self.not_a_file = ~FILE_MASK[File.A]
        self.not_h_file = ~FILE_MASK[File.H]
        self.not_ab_file = ~(FILE_MASK[File.A] | FILE_MASK[File.B])
        self.not_gh_file = ~(FILE_MASK[File.G] | FILE_MASK[File.H])
        
        self._init_pawn_attacks()
        self._init_king_moves()
        self._init_knight_moves()
        self._init_rays()
        self._init_between_masks()
        
    
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
            
    
    def _init_pawn_attacks(self):
        for square in range(64):
            pos = np.uint64(1) << square
                
            # White attacks
            if pos & self.not_a_file:
                self.pawn_attacks[Colour.WHITE][square] |= pos << 7
            if pos & self.not_h_file:
                self.pawn_attacks[Colour.WHITE][square] |= pos << 9
             
            if pos & self.not_a_file:
                self.pawn_attacks[Colour.BLACK][square] |= pos >> 9
            if pos & self.not_h_file:
                self.pawn_attacks[Colour.BLACK][square] |= pos >> 7
            
    
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
            

    def _init_between_masks(self):
        for start in range(64):
            for direction in range(8):
                # Walk down the ray
                ray = self.rays[start][direction]
                
                # Scan bits in this ray, iterating from lsb -> msb
                while ray:
                    end = get_lsb_index(ray)
                    
                    full_ray = self.rays[start][direction]
                    ray_from_end = self.rays[end][direction]
                    
                    self.between[start][end] = (full_ray ^ ray_from_end) & ~(np.uint64(1) << np.uint64(end))
                    
                    # Move to next square in ray.
                    ray &= ray - 1
                

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
            # Moving one square forward
            if occupancy & infront == 0:
                moves |= infront
            # Moving two squares forward
            if (occupancy & two_infront == 0) and (pos & RANK_MASK[Rank.TWO] != 0):
                moves |= two_infront
        elif colour == Colour.BLACK:
            infront = pos >> 8
            two_infront = infront >> 8
            # Moving one square forward
            if occupancy & infront == 0:
                moves |= infront
            # Moving two squares forward
            if (occupancy & two_infront == 0) and (pos & RANK_MASK[Rank.SEVEN] != 0):
                moves |= two_infront
                
        # Including en passant in captures
        if board.ep_target != -1:
            opponent_occupancy |= np.uint64(1) << board.ep_target
            
        moves |= self.pawn_attacks[colour][squareIndex] & opponent_occupancy
 
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
    
    
    def get_attackers(self, board: "Board", colour: Colour, king_square: int) -> np.uint64:
        '''
            We get the position of the king, and place all different types of pieces 
            on it to see how many attackers we have
        '''
        attackers = np.uint64(0)
        opponent_colour = colour.opposite
        
        # Pawn attackers
        attackers |= self.pawn_attacks[colour][king_square] & board.bitboards[opponent_colour][Piece.PAWN]
        
        # Knight attackers
        attackers |= self.knight_moves[king_square] & board.bitboards[opponent_colour][Piece.KNIGHT]
        
        # Sliding attackers (Bishop, Rook, Queen)
        attackers |= self._get_sliding_moves(board, Piece.BISHOP, king_square) & board.bitboards[opponent_colour][Piece.BISHOP]
        attackers |= self._get_sliding_moves(board, Piece.ROOK, king_square) & board.bitboards[opponent_colour][Piece.ROOK]
        attackers |= self._get_sliding_moves(board, Piece.QUEEN, king_square) & board.bitboards[opponent_colour][Piece.QUEEN]
        
        return attackers
    
    
    def is_square_attacked(self, board: "Board", colour: Colour, square: int) -> bool:
        '''
            get_attackers, but returns earlier if an attacker is found
        '''
        opponent_colour = Colour.BLACK if colour == Colour.WHITE else colour.WHITE
        
        # Pawn attackers
        if self.pawn_attacks[colour][square] & board.bitboards[opponent_colour][Piece.PAWN]:
            return True
        
        # Knight attackers
        if self.knight_moves[square] & board.bitboards[opponent_colour][Piece.KNIGHT]:
            return True
        
        # Sliding attackers (Bishop, Rook, Queen)
        if self._get_sliding_moves(board, Piece.BISHOP, square) & board.bitboards[opponent_colour][Piece.BISHOP]:
            return True
        
        if self._get_sliding_moves(board, Piece.ROOK, square) & board.bitboards[opponent_colour][Piece.ROOK]:
            return True
        
        if self._get_sliding_moves(board, Piece.QUEEN, square) & board.bitboards[opponent_colour][Piece.QUEEN]:
            return True

        return False

    
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
    
    
    def get_legal_moves(self, board: "Board", colour: Colour) -> list[np.int16]:
        '''
        https://peterellisjones.com/posts/generating-legal-chess-moves-efficiently/
        When there is a single attacker, we can either
        1. Move the king
        2. Block the attack (if it is a rook, bishop or queen)
        3. Capture the attacker
        
        For the king, legal moves are moves which do not move into an attacked square. We can do this by using
        get_attackers on every legal king move, including the inbetween squares for castling
        We can use a similar approach to get_sliding_moves to find squares which are inbetween the king and attacker
        We already have moves which capture the attacker through its bit location in get_attackers
        For multiple attackers, we must move the king out of the way
            
        For pins, I can again use a similar approach to get_sliding_moves for the sliding pieces. For each
        direction, I check if the king is along the ray. If so, the king is the 'blocking' piece, and any pieces
        along the ray are unable to move. We don't include the king in this ray
        '''
        # List of 16-bit encoded move integers
        move_list = []
        king_pos = get_lsb_index(board.bitboards[colour][Piece.KING])
        attackers = self.get_attackers(board, colour, king_pos)
        num_attackers = attackers.bit_count()
        opposite_colour_occupancy = board.get_colour_occupancy(colour.opposite)
        
        # Add legal king moves. This is the same regardless of the number of attackers
        candidate_king_moves = self.get_pseudo_legal_moves(board, Piece.KING, colour, king_pos)
        while candidate_king_moves:
            move_index = get_lsb_index(candidate_king_moves)
            candidate_king_moves ^= 1 << move_index
            is_capture = opposite_colour_occupancy & (1 << move_index)
            if self.is_square_attacked(board, colour, move_index):
                continue
                
            if abs(move_index - king_pos) == 1:
                # Regular king move
                move_list.append(encode_move(king_pos, move_index, MoveFlags.CAPTURE if is_capture else MoveFlags.QUIET))
            else:
                # Castling. We check if the inbetween squares are attacked
                legal = True
                for sq_index in range(min(king_pos, move_index) + 1, max(king_pos, move_index)):
                    if self.is_square_attacked(board, colour, sq_index):
                        legal = False
                        break
                
                # King side castling
                if legal and abs(move_index - king_pos) == 2:
                    move_list.append(encode_move(king_pos, move_index, MoveFlags.KING_CASTLE))
                # Queen side castling
                elif legal and abs(move_index - king_pos) == 3:
                    move_list.append(encode_move(king_pos, move_index, MoveFlags.QUEEN_CASTLE))
        
        # By default, all moves are legal. 
        # The capture mask represents legal capture moves
        # The push mask represents normal legal moves
        capture_mask = np.uint64(0xFFFFFFFFFFFFFFFF)
        push_mask = np.uint64(0xFFFFFFFFFFFFFFFF)
        pinned_mask = np.uint64(0)
        
        # We can either block or capture the attacker      
        if num_attackers == 1:
            # Legal capture moves are just capturing the attackers
            capture_mask = attackers
            attacker_pos = get_lsb_index(attackers)
            
            # We block
            if board.is_slider(attacker_pos, colour.opposite):
                push_mask = self.between[attacker_pos][king_pos]
            # If piece isn't slider, we can't block it
            else:
                push_mask = np.uint64(0)
        # We must move the king; all other moves are illegal
        elif num_attackers == 2:
            capture_mask = np.uint64(0)
            push_mask = np.uint64(0)
        
        # Calculating moves for pinned pieces
        enemy_pieces = opposite_colour_occupancy
        while enemy_pieces:
            enemy_piece_pos = get_lsb_index(enemy_pieces)
            enemy_pieces ^= 1 << enemy_piece_pos
            
            if not board.is_slider(enemy_piece_pos, colour.opposite):
                continue  
            
            enemy_piece_type = board.get_piece_at(enemy_piece_pos, colour.opposite)
            if enemy_piece_type is None:
                continue
            
            dirs = []
            match enemy_piece_type:
                case Piece.BISHOP:
                    dirs = [Direction.NE, Direction.SE, Direction.SW, Direction.NW]
                case Piece.ROOK:
                    dirs = [Direction.N, Direction.S, Direction.W, Direction.E]
                case Piece.QUEEN:
                    dirs = [Direction.NE, Direction.SE, Direction.SW, Direction.NW, Direction.N, Direction.S, Direction.W, Direction.E]
                case _:
                    continue
            
            POS_DIR = [Direction.NW, Direction.N, Direction.NE, Direction.E]
            for dir in dirs:
                enemy_blocked_bits = board.get_occupancy() & self.rays[enemy_piece_pos][dir]
                if enemy_blocked_bits == 0:
                    continue
                enemy_candidate_bit = get_lsb_index(enemy_blocked_bits) if dir in POS_DIR else get_msb_index(enemy_blocked_bits)
                
                # We take sliding moves from the king in the opposite direciton
                king_blocked_bits = board.get_occupancy() & self.rays[king_pos][dir.opposite]
                king_candidate_bit = get_lsb_index(king_blocked_bits) if dir not in POS_DIR else get_msb_index(king_blocked_bits)
                
                # There is a single piece blocking check, and it is our piece so it is pinned
                candidate_piece = board.get_piece_at(enemy_candidate_bit, colour)
                if (enemy_candidate_bit == king_candidate_bit) and (candidate_piece is not None):
                    pinned_mask |= 1 << enemy_candidate_bit
                    psuedo_legal_moves = self.get_pseudo_legal_moves(board, candidate_piece, colour, enemy_candidate_bit)
                    legal_moves = (self.between[king_pos][enemy_piece_pos] | (1 << enemy_piece_pos)) & psuedo_legal_moves
                    self._add_bitboard_to_move_list(enemy_candidate_bit, legal_moves, capture_mask, push_mask, move_list, opposite_colour_occupancy)
        
        # We iterate over all pseudo_legal moves and use the masks to remove illegal moves
        occupancy = board.get_colour_occupancy(colour)
        while occupancy:
            piece_index = get_lsb_index(occupancy)
            occupancy &= occupancy - 1
            if pinned_mask & (1 << piece_index):
                print(f"Piece at {piece_index} is pinned")
                continue
            
            occupancy &= occupancy - 1
            piece_type = board.get_piece_at(piece_index, colour)
            if piece_type is None:
                continue
            
            psuedo_legal_moves = self.get_pseudo_legal_moves(board, piece_type, colour, piece_index)
            self._add_bitboard_to_move_list(piece_index, psuedo_legal_moves, capture_mask, push_mask, move_list, opposite_colour_occupancy)
            
        return move_list
    

    def _add_bitboard_to_move_list(self, source: int, bitboard: np.uint64, capture_mask: np.uint64, push_mask: np.uint64, move_list: list, opponent_occupancy: np.uint64):
        # 1. First, apply the Constraints (Legality)
        # We combine both masks. A move is legal if it satisfies EITHER blocking OR capturing.
        # (When not in check, both masks are all 1s, so everything allows)
        legal_destinations = bitboard & (capture_mask | push_mask)

        while legal_destinations:
            next_move = get_lsb_index(legal_destinations)
            legal_destinations &= legal_destinations - 1
            
            # 2. Convert Index to Bitboard for checking
            dest_bit = np.uint64(1) << np.uint64(next_move)
            
            # 3. Determine Flag based on what is on the board
            if dest_bit & opponent_occupancy:
                move_list.append(encode_move(source, next_move, MoveFlags.CAPTURE))
            else:
                # Note: This marks En Passant as Quiet. 
                # You might want to pass 'ep_target' to this function to mark EP correctly, 
                # but for basic movement, QUIET is safer than CAPTURE for empty squares.
                move_list.append(encode_move(source, next_move, MoveFlags.QUIET))
            
            