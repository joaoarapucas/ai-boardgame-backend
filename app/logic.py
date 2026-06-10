from typing import Optional
from app.schemas import Cell, Position, SetupResponse, PlayerTurnResponse, TEAM_PROFESSORS
import random
import copy
import time


# MARK: PARAMS AND CONSTANTS

BOARD_SIZE = 5
MAX_DEPTH = 4 #for the minimax search
INF = float("inf") #infinity

#each prof will have a different heuristic
OFFENSIVE_PROFESSORS = {"CLARO", "KARIN"}
DEFENSIVE_PROFESSORS = {"REY", "BEATRIZ"}

# ! ! ! HEURISTICS WEIGHTS ! ! !
#note: arbitrary weight values! 
MOBILITY_WEIGHT    = 1.0   # both - move possibilites
HEIGHT_WEIGHT      = 5.0   # both - better height
BLOCK_WEIGHT       = 1.5   # offense - try to block opponet
ADVANCE_WEIGHT     = 3.0   # defensive - try to get higher
CELL_DISTANCE_W   = 0.8   # defensive - try to get closer to high cells

TIME_LIMIT = 4.3 # time limit for the IDS (depth search/thinking)




##################################################################
#MARK: UTIL FUNCS

def adjacent_cells(row: int, col: int) -> list[tuple[int, int]]:
    cells = []
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            nr, nc = row + dr, col + dc
            if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                cells.append((nr, nc))
    return cells


def find_professor(board: list[list[Cell]], name: str) -> Optional[tuple[int, int]]:
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c].professor == name:
                return (r, c)
    return None



def get_possible_moves( board: list[list[Cell]], team_id: int ) -> list[PlayerTurnResponse]:
    """
    goes around every adjacent cell from a professor and saves them as possible moves,
    then goes around every possible move and saves them as mentorship possibilities
    """
    moves: list[PlayerTurnResponse] = []

    for professor in TEAM_PROFESSORS[team_id]: #for each player's professor
        
        pos = find_professor(board, professor)
        if pos is None:
            continue
        
        cur_row, cur_col = pos
        cur_level = board[cur_row][cur_col].level

        for move_row, move_col in adjacent_cells(cur_row, cur_col):
            
            move_cell = board[move_row][move_col]

            #skip illegal moves
            if move_cell.professor is not None:
                continue
            if move_cell.level == 4:
                continue
            if move_cell.level > cur_level + 1:
                continue

            if move_cell.level == 3: #winning move! :D
                print("found winning move!")
                moves.append(PlayerTurnResponse(
                    professor=professor,
                    move_to=Position(row=move_row, col=move_col),
                ))
                continue

            for men_row, men_col in adjacent_cells(move_row, move_col): #for each mentorship possibility
                                                                        #around the move's cell
                men_cell = board[men_row][men_col]
                is_source = (men_row, men_col) == (cur_row, cur_col)
                
                if (men_cell.professor is None or is_source) and men_cell.level < 4:
                    moves.append(PlayerTurnResponse(
                        professor=professor,
                        move_to=Position(row=move_row, col=move_col),
                        mentor_at=Position(row=men_row, col=men_col),
                    ))
    return moves


def apply_move( board: list[list[Cell]], move: PlayerTurnResponse) -> list[list[Cell]]:
    """
    simulates a move for the minimax algo
    """

    new_board = board_copy(board)

    prof_pos = find_professor(new_board, move.professor)
    if prof_pos is None:
        return new_board
    old_r, old_c = prof_pos

    #move prof
    new_board[old_r][old_c].professor = None
    new_board[move.move_to.row][move.move_to.col].professor = move.professor

    #increase height
    if move.mentor_at is not None:
        new_board[move.mentor_at.row][move.mentor_at.col].level += 1

    return new_board


def board_copy(board: list[list[Cell]]) -> list[list[Cell]]:
    #ensures deep copy 
    return [[Cell(level=board[r][c].level, professor=board[r][c].professor)
             for c in range(BOARD_SIZE)]
            for r in range(BOARD_SIZE)]

def winner_move(board: list[list[Cell]], last_mover_team: int) -> bool:
    """checks for a winning move!"""
    for prof in TEAM_PROFESSORS[last_mover_team]:
        pos = find_professor(board, prof)
        if pos and board[pos[0]][pos[1]].level == 3:
            return True
    return False






##################################################################
# MARK: SETUP PHASE

CENTRAL_RING: list[tuple[int, int]] = [
    (1, 1), (1, 2), (1, 3),
    (2, 1),         (2, 3),
    (3, 1), (3, 2), (3, 3),
]
 
def choose_setup(board: list[list[Cell]]) -> SetupResponse:
    """
    positions the pieces around the central ring, if possible.
    the strategy is to place them there to be close to any spot
    in the board. this ensures more good possible moves for both professors:
        - the defensive professor will move to free spot to try to build up
        - the offensive professor will go closer to enemy's pieces to stop them
    
    at the same time, it saves processing time by not having to calculate best moves
    for an empty board with the minimax algo.

    this is based on opening books from other classic AI players for board games!
    """

    occupied = {
        (r, c)
        for r in range(BOARD_SIZE)
        for c in range(BOARD_SIZE)
        if board[r][c].professor is not None or board[r][c].level != 0
    }

    ring_free = [pos for pos in CENTRAL_RING if pos not in occupied]
    row, col = random.choice(ring_free) 
    return SetupResponse(row=row, col=col)






##################################################################
# MARK: HEURISTICS

def count_mobility(board: list[list[Cell]], professor: str) -> int:
    """
    counts number of valid movements around a professor.
    used to score a move in the heuristic.
    """
    pos = find_professor(board, professor)
    if pos is None:
        return 0
    cur_row, cur_col = pos
    cur_level = board[cur_row][cur_col].level
    count = 0
    for dr, dc in adjacent_cells(cur_row, cur_col):
        cell = board[dr][dc]
        if cell.professor is None and cell.level < 4 and cell.level <= cur_level + 1:
            count += 1
    return count


def score_professor( board: list[list[Cell]], professor: str, 
                     offensive: bool,      enemy_professors: list[str] ) -> float:

    pos = find_professor(board, professor)
    if pos is None: #fallback
        return 0.0

    r, c = pos
    level = board[r][c].level
    mobility = count_mobility(board, professor)
    score = 0.0

    score += HEIGHT_WEIGHT * level # better height
    score += MOBILITY_WEIGHT * mobility # better move options

    if level == 0:
        score -= 6.0

    #OFFENSIVE AND DEFENSIVE POINTS
    if offensive:
        if level > 0: #wont block if on ground (harder to get out!)
            for enemy in enemy_professors:
                #scores better if diminished enemy's options - basically a troll
                score += BLOCK_WEIGHT * (8 - count_mobility(board, enemy)) 
        else:
            score -= 4.0

    else: # defensive
        # incentive to get heigher
        if level == 2:
            score += ADVANCE_WEIGHT * 2.5
        elif level == 1:
            score += ADVANCE_WEIGHT * 0.8

        # incentive to be around high level cells
        for cell_row in range(BOARD_SIZE):
            for cell_col in range(BOARD_SIZE):
                cell_level = board[cell_row][cell_col].level
                if cell_level in (2, 3):
                    dist = max(abs(r - cell_row), abs(c - cell_col))  #chebyshev distance
                    if dist <= 1:
                        score += CELL_DISTANCE_W * (3 - dist) * cell_level

    return score


def heuristic(board: list[list[Cell]], maximizing_team: int) -> float:
    """
    scores the board state based on a 'maximing team'.
    higher = better
    """
    opp_team = 3 - maximizing_team

    max_profs = TEAM_PROFESSORS[maximizing_team]
    opp_profs = TEAM_PROFESSORS[opp_team]

    my_score = 0.0
    opp_score = 0.0

    for prof in max_profs:
        is_off = prof in OFFENSIVE_PROFESSORS
        my_score += score_professor(board, prof, is_off, opp_profs)

    for prof in opp_profs:
        is_off = prof in OFFENSIVE_PROFESSORS
        opp_score += score_professor(board, prof, is_off, max_profs)

    return my_score - opp_score






##################################################################
# MARK: MINIMAX

def minimax(
    board: list[list[Cell]],
    depth: int,
    alpha: float,
    beta: float,
    maximizing_team: int,
    current_team: int,
    root_team: int, #first caller
    start #time
) -> float:
    """
    returns heuristic score of the board state

    this is the intelligent part of the program!
    """

    if time.time() - start > TIME_LIMIT: #abort because of time limit. best of luck!
        return heuristic(board, root_team)
    
    last_team = 3 - current_team

    if winner_move(board, last_team):
        if last_team == root_team:
            return INF - (MAX_DEPTH - depth) #current player - try to win
        else:
            return -INF + (MAX_DEPTH - depth) #opp player - try to make them lose

    if depth == 0:
        return heuristic(board, root_team)

    moves = get_possible_moves(board, current_team)
    if not moves:
        #cant move - defeat
        if current_team == root_team:
            return -INF + (MAX_DEPTH - depth) #bad situation to be
        else:
            return INF - (MAX_DEPTH - depth) #good situation for the opp to be

    next_team = 3 - current_team

    if current_team == root_team:
        # MAX
        value = -INF #wants to go bottom-up

        for move in moves: #for each move
            new_board = apply_move(board, move) #change the board
            child_val = minimax(new_board, depth - 1, alpha, beta, maximizing_team, next_team, root_team, start)
            if child_val > value:
                value = child_val
            alpha = max(alpha, value)
            if alpha >= beta:
                break  # BETA PRUNE
        return value
    else:
        # MIN
        value = INF #wants to go top-down

        for move in moves: #for each move
            new_board = apply_move(board, move) #change the board
            child_val = minimax(new_board, depth - 1, alpha, beta, maximizing_team, next_team, root_team, start)
            if child_val < value:
                value = child_val
            beta = min(beta, value)
            if alpha >= beta:
                break  # ALPHA PRUNE
        return value

# 
def move_score_quick( board: list[list[Cell]], move: PlayerTurnResponse, my_team: int ) -> float:
    """
    sorts moves in a priority order for ab-minimax - helps with the 5s time limit.
    """
    destiny = move.move_to
    destiny_level = board[destiny.row][destiny.col].level

    if destiny_level == 3: #winning move!
        return 1000.0 

    prof_pos = find_professor(board, move.professor)
    if prof_pos:
        cur_level = board[prof_pos[0]][prof_pos[1]].level
        level_diff = destiny_level - cur_level
        level_bonus = level_diff * 5.0  # incentive to get higher
    else:
        level_bonus = 0.0

    new_board = apply_move(board, move)
    return heuristic(new_board, my_team) + level_bonus






##################################################################
# MARK: TURN PHASE

def choose_turn( board: list[list[Cell]], team_id: int ) -> Optional[PlayerTurnResponse]:
    """
    before actually annalysing the moves, this does some sanity checks:
        - checks if can win now
        - checks if opponent can win now

    if none of those are true, then uses ab minimax to search for a best move.
    because the game orchestrator imposes the AIs 5 seconds to make a move, 
    ab minimax is not ideal (although simpler to code!). to bypass this, 
    this function also uses iterative deepening search (IDS), which basically
    means 'keep going until the time limit!'
    """

    start = time.time()

    moves = get_possible_moves(board, team_id)
    if not moves:
        return None

    # ! ! ! AUTO WIN ! ! ! 
    winning = [m for m in moves if board[m.move_to.row][m.move_to.col].level == 3]
    if winning:
        return random.choice(winning)

    # ! ! ! BLOCK OPP WINNING MOVE ! ! ! 
    opp_team = 3 - team_id
    opp_moves = get_possible_moves(board, opp_team)
    opp_winning = [m for m in opp_moves if board[m.move_to.row][m.move_to.col].level == 3]
    if opp_winning:
        blocking = []
        for move in moves:
            new_board = apply_move(board, move)
            opp_after = get_possible_moves(new_board, opp_team)
            opp_win_after = [m for m in opp_after if new_board[m.move_to.row][m.move_to.col].level == 3]
            if not opp_win_after:
                blocking.append(move)
        if blocking:
            # picks the best block
            blocking.sort(key=lambda m: move_score_quick(board, m, team_id), reverse=True)
            return blocking[0]

    # ! ! ! MINIMAX ! ! !
    
    
    moves.sort(key=lambda m: move_score_quick(board, m, team_id), reverse=True)

    best_move  = moves[0]
    best_value = -INF

    for move in moves:
        if time.time() - start > TIME_LIMIT:
            break #reached time limit, best of luck!
        new_board = apply_move(board, move)
        value = minimax(
            board =  new_board,
            depth = MAX_DEPTH - 1,
            alpha = -INF,
            beta = INF,
            maximizing_team = team_id,
            current_team = opp_team,
            root_team = team_id,
            start = start,
        )
        if value > best_value:
            best_value = value
            best_move  = move

    print("\n\nthinking time: " + str(time.time() - start))        
    return best_move
