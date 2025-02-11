from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from uuid import uuid4
from typing import Dict, List, Optional
import asyncio

app = FastAPI()

games: Dict[str, dict] = {}

class Game:
    def __init__(self):
        self.players: List[str] = []
        self.turn_index: int = 0
        self.state: Dict = {}
        self.websocket_connections: Dict[str, WebSocket] = {}
        self.lock = asyncio.Lock()

    async def broadcast(self, message: dict):
        for ws in self.websocket_connections.values():
            await ws.send_json(message)

@app.get("/game/{game_id}/players")
def get_players(game_id: str):
    if game_id not in games:
        return {"error": "Game not found"}
    
    return {"players": games[game_id].players}

@app.post("/game/create")
def create_game():
    game_id = str(uuid4())
    games[game_id] = Game()
    return {"game_id": game_id}

@app.post("/game/join/{game_id}")
async def join_game(game_id: str, player_id: str):
    print(games)
    if game_id not in games:
        return {"error": "Game not found"}
    game = games[game_id]
    if player_id in game.players:
        return {"error": "Player already in game"}
    game.players.append(player_id)
    return {"message": "Joined game", "players": game.players}

@app.websocket("/game/{game_id}/ws/{player_id}")
async def game_websocket(websocket: WebSocket, game_id: str, player_id: str):
    if game_id not in games:
        await websocket.close()
        return
    game = games[game_id]
    await websocket.accept()
    game.websocket_connections[player_id] = websocket
    print(f"WebSocket connected: {player_id}")  # Debugging

    try:
        while True:
            data = await websocket.receive_json()
            print(f"Received WebSocket message from {player_id}: {data}")  # Debugging

            await game.broadcast(data)
    except WebSocketDisconnect:
        del game.websocket_connections[player_id]

@app.post("/game/{game_id}/play")
async def play_card(game_id: str, player_id: str, card: str):
    if game_id not in games:
        return {"error": "Game not found"}
    game = games[game_id]
    async with game.lock:
        if game.players[game.turn_index] != player_id:
            return {"error": "Not your turn"}
        game.state[player_id] = card
        await game.broadcast({"player": player_id, "card": card})
        return {"message": "Card played", "card": card}

@app.post("/game/{game_id}/end_turn")
async def end_turn(game_id: str, player_id: str):
    if game_id not in games:
        return {"error": "Game not found"}
    game = games[game_id]
    async with game.lock:
        if game.players[game.turn_index] != player_id:
            return {"error": "Not your turn"}
        game.turn_index = (game.turn_index + 1) % len(game.players)
        await game.broadcast({"message": "Turn ended", "next_player": game.players[game.turn_index]})
        return {"message": "Turn ended"}