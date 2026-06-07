# app/logic.py
import random
from typing import Optional

from app.schemas import Cell, Position, SetupResponse, PlayerTurnResponse, TEAM_PROFESSORS

BOARD_SIZE = 5



def adjacent_cells(row: int, col: int) -> list[tuple[int, int]]:
    """
    Retorna todas as casas vizinhas (incluindo diagonais).
    O tabuleiro e 5x5, entao filtra coordenadas fora dos limites.
    """
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
    """Encontra a posicao (row, col) de um professor no tabuleiro."""
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c].professor == name:
                return (r, c)
    return None


def choose_setup(board: list[list[Cell]]) -> SetupResponse:
    """
    Fase de posicionamento: escolhe uma casa de nivel 0 desocupada.
    """
    candidates = [
        (r, c)
        for r in range(BOARD_SIZE)
        for c in range(BOARD_SIZE)
        if board[r][c].level == 0 and board[r][c].professor is None
    ]
    row, col = random.choice(candidates)
    return SetupResponse(row=row, col=col)


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

    return None  # sem jogadas validas (raro, mas possivel)
