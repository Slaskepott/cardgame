from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from uuid import uuid4
from typing import Dict, List, Optional
import asyncio

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

games: Dict[str, dict] = {}

class Game:
    def __init__(self):
        self.players: List[str] = []
        self.turn_index: int = 0
        self.state: Dict = {}
        self.websocket_connections: Dict[str, WebSocket] = {}
        self.lock = asyncio.Lock()

    async def broadcast(self, message: dict):
        disconnected_players = []
        for player, ws in self.websocket_connections.items():
            try:
                await ws.send_json(message)
            except Exception:
                disconnected_players.append(player)

        # Remove disconnected players
        for player in disconnected_players:
            del self.websocket_connections[player]

@app.get("/game/{game_id}/players")
def get_players(game_id: str):
    if game_id not in games:
        return {"error": "Game not found"}
    return {"players": games[game_id].players}

@app.post("/game/create/{game_id}")
def create_game(game_id: str):
    if game_id in games:
        return {"error": "Game ID already exists. Choose a different ID."}
    
    games[game_id] = Game()
    return {"message": f"Game {game_id} created successfully"}

@app.post("/game/join/{game_id}")
async def join_game(game_id: str, player_id: str):
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
    print(f"WebSocket connected: {player_id}")

    try:
        while True:
            data = await websocket.receive_json()
            print(f"Received WebSocket message from {player_id}: {data}")

            # ✅ Broadcast message to ALL players
            await game.broadcast({"player": player_id, "data": data})

    except WebSocketDisconnect:
        print(f"WebSocket disconnected: {player_id}")
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
