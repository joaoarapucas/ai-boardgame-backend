import random
from typing import Optional
from app.schemas import Cell, SetupResponse, PlayerTurnResponse

def choose_setup(board: list[list[Cell]]) -> SetupResponse:
    candidates = [
        (r,c)
        for r in range(5)
        for c in range(5)
        if board[r][c].level == 0 and board[r][c].professor is None
    ]

    row, col = random.choice(candidates)
    return SetupResponse(row=1, col=0)

def choose_turn(board: list[list[Cell]], team_id: int) -> Optional[PlayerTurnResponse]:
    """
    Fase de turno: decide qual professor mover, para onde, e onde mentorar.

    Estrategia:
      1. Se existe jogada de vitoria (mover para celula nivel 3), faz ela.
      2. Caso contrario, escolhe uma jogada aleatoria valida.

    Regras respeitadas:
      - So move para casa adjacente
      - Nao move para casa ocupada
      - Nao move para casa nivel 4 (graduada)
      - Nao sobe mais de 1 nivel por movimento
      - Mentoria deve ser adjacente ao destino
      - Nao mentora casa ocupada (exceto a casa de origem)
      - Nao mentora casa nivel 4
    """
    print("jogada epica")
    winning_moves: list[PlayerTurnResponse] = []
    candidate_moves: list[PlayerTurnResponse] = []

    for professor in TEAM_PROFESSORS[team_id]:
        pos = find_professor(board, professor)
        if pos is None:
            continue

        cur_row, cur_col = pos
        cur_level = board[cur_row][cur_col].level

        # Tenta cada casa vizinha como destino
        for dst_row, dst_col in adjacent_cells(cur_row, cur_col):
            dst_cell = board[dst_row][dst_col]

            # Casa ocupada, graduada, ou nivel alto demais? Pula.
            if dst_cell.professor is not None:
                continue
            if dst_cell.level == 4:
                continue
            if dst_cell.level > cur_level + 1:
                continue

            # Jogada de vitoria! Mover para nivel 3 vence o jogo.
            if dst_cell.level == 3:
                winning_moves.append(PlayerTurnResponse(
                    professor=professor,
                    move_to=Position(row=dst_row, col=dst_col),
                ))
                continue

            # Jogada normal: precisa escolher onde mentorar
            for men_row, men_col in adjacent_cells(dst_row, dst_col):
                men_cell = board[men_row][men_col]
                is_source = (men_row, men_col) == (cur_row, cur_col)
                if (men_cell.professor is None or is_source) and men_cell.level < 4:
                    candidate_moves.append(PlayerTurnResponse(
                        professor=professor,
                        move_to=Position(row=dst_row, col=dst_col),
                        mentor_at=Position(row=men_row, col=men_col),
                    ))

    # Prioridade: vitoria > jogada aleatoria
    if winning_moves:
        return random.choice(winning_moves)
    if candidate_moves:
        return random.choice(candidate_moves)
    print(winning_moves)
    print(candidate_moves)
    return None  # sem jogadas validas (raro, mas possivel)    
