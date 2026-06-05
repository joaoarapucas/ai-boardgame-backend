from fastapi import FastAPI, HTTPException
from datetime import date

from app.schemas import AITurnRequest, TurnPhase
from app.logic import choose_setup, choose_turn

app = FastAPI(
    title="piegas, o jogador inteligente",
    description="API do piegas",
    version="0.1.0"
)

@app.get("/health")
async def health():
    return date.today()

@app.post("/move")
async def move(body: AITurnRequest):
    """
        Endpoint principal pelo orquestrador de partidas.
        
        recebe o estado completo de um turno de partida e devolve a jogada escolhida
    """ 
    print("veremos")
    if body.turn_phase == TurnPhase.SETUP:
        return choose_setup(body.board)
    elif body.turn_phase == TurnPhase.PLAYER_TURN:
        jogada = choose_turn(body.board, int(body.your_team))

        if jogada is None:
            raise HTTPException(status_code=422)

        return jogada
    #else raise 
