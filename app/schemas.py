from enum import IntEnum, Enum
from typing import Optional, List
from pydantic import BaseModel, Field

class TeamID(IntEnum):
    TURING = 1   # claro e rey
    LOVELACE = 2 # karin e beatriz

class TurnPhase(str, Enum):
    SETUP = "setup_placement"
    PLAYER_TURN = "player_turn"




class Cell(BaseModel):
    level: int = Field(ge=0, le=4)
    professor: Optional[str] = None

class Position(BaseModel):
    row: int = Field(ge=0, le=4)
    col: int = Field(ge=0, le=4)




class AITurnRequest(BaseModel):
    """
    Payload que foi enviado pelo orquestrador de partidas
    """
    game_id: str
    turn_number: int
    turn_phase: TurnPhase
    your_team: TeamID
    professor_to_place: Optional[str]
    board: List[List[Cell]]
    professor_to_place: str = Field(default=None)

class SetupResponse(BaseModel):
    row: int = Field(ge=0, le=4)
    col: int = Field(ge=0, le=4)

class PlayerTurnResponse(BaseModel):
    professor: str
    move_to: Position
    mentor_at: Optional[Position] = None
