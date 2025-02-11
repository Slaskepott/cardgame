import httpx

BASE_URL = "https://cardgame-lndd.onrender.com" 

#Create game
response = httpx.post(f"{BASE_URL}/game/create")
print(response.json())  # Should return {"game_id": "..."}

#Join game
game_id = response.json().get("game_id")
player1 = "player1"
player2 = "player2"

httpx.post(f"{BASE_URL}/game/join/{game_id}", params={"player_id": player1})
httpx.post(f"{BASE_URL}/game/join/{game_id}", params={"player_id": player2})

#Play card
response = httpx.post(f"{BASE_URL}/game/{game_id}/play", params={"player_id": player1, "card": "fireball"})
print(response.json())  # Should return {"message": "Card played", "card": "fireball"}

#End turn
response = httpx.post(f"{BASE_URL}/game/{game_id}/end_turn", params={"player_id": player1})
print(response.json())  # Should return {"message": "Turn ended"}
