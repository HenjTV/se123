import os
import redis
import json
import uuid
import time
from classes.UserOnServer import UserOnServer
from classes.GameRooms import GameRooms
from core.GameManager import GameManager
from server import socketio, app
from classes.game_manager_store import active_game_managers

redis_client = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)

def find_players_in_queue():
    all_users = redis_client.keys("user:*")
    unique_players = set()
    players_in_queue = []
    for user_key in all_users:
        username = user_key.split(":")[1]
        if username in unique_players:
            continue
        user_on_server = UserOnServer(username)
        if user_on_server.get_game_status() == "startQue":
            rating = user_on_server.get_rating()
            players_in_queue.append((username, rating))
            unique_players.add(username)
    return players_in_queue

def create_room(players):
    room_id = str(uuid.uuid4())
    game_room = GameRooms.create_room(room_id, players[0][0], players[1][0])
    
    # Загружаем рейтинг из users.json и синхронизируем с Redis
    with open("users.json", "r") as file:
        users_data = json.load(file)
    
    for index, player in enumerate(players):
        username = player[0]
        user_on_server = UserOnServer(username)
        # Устанавливаем рейтинг из users.json, если он там есть
        if username in users_data:
            rating = users_data[username]["rating"]
            user_on_server.set_rating(rating)
        else:
            user_on_server.set_rating(1500)  # Значение по умолчанию, если нет в JSON
        
        user_on_server.set_room(room_id)
        user_on_server.set_game_status("inRoom")
    
    game_manager = GameManager(room_id)
    active_game_managers[room_id] = game_manager
    game_manager.start()
    print(f"Комната {room_id} создана с игроками: {[player[0] for player in players]}")

def matchmaking_loop():
    print(f"Матчмейкер запущен в процессе: {os.getpid()}")
    while True:
        players_in_queue = find_players_in_queue()
        if len(players_in_queue) < 2:
            print("MATCHMAKER: Недостаточно игроков для создания комнаты.")
            time.sleep(15)
            continue
        players_in_queue.sort(key=lambda x: x[1])
        while len(players_in_queue) >= 2:
            player1, player2 = players_in_queue[:2]
            if are_players_in_room(player1[0], player2[0]):
                print(f"Игроки {player1[0]} и {player2[0]} уже находятся в комнате. Пропускаем создание комнаты.")
                players_in_queue = players_in_queue[2:]
                continue
            create_room([player1, player2])
            players_in_queue = players_in_queue[2:]
        time.sleep(15)

def are_players_in_room(player1_username, player2_username):
    user1 = UserOnServer(player1_username)
    user2 = UserOnServer(player2_username)
    room1 = user1.get_room()
    room2 = user2.get_room()
    return room1 and room2 and room1 == room2