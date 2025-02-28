import redis
import json

redis_client = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)

class GameRooms:
    def __init__(self, room_id):
        self.room_id = room_id
        self.redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)
        self.key = f"room:{room_id}"

    def get_room_data(self):
        data = self.redis_client.get(self.key)
        if data:
            return json.loads(data)
        return {}

    def set_room_data(self, data):
        self.redis_client.set(self.key, json.dumps(data))

    def get_player1_id(self):
        data = self.get_room_data()
        return data.get('player1_id', None)

    def set_player1_id(self, player1_id):
        data = self.get_room_data()
        data['player1_id'] = player1_id
        self.set_room_data(data)

    def get_player2_id(self):
        data = self.get_room_data()
        return data.get('player2_id', None)

    def set_player2_id(self, player2_id):
        data = self.get_room_data()
        data['player2_id'] = player2_id
        self.set_room_data(data)

    def get_status(self):
        data = self.get_room_data()
        return data.get('status', 'waiting')

    def set_status(self, status):
        data = self.get_room_data()
        data['status'] = status
        self.set_room_data(data)

    def get_round(self):
        data = self.get_room_data()
        return data.get('round', 1)

    def set_round(self, round_number):
        data = self.get_room_data()
        data['round'] = round_number
        self.set_room_data(data)

    def get_winner_id(self):
        data = self.get_room_data()
        return data.get('winner_id', None)

    def set_winner_id(self, winner_id):
        data = self.get_room_data()
        data['winner_id'] = winner_id
        self.set_room_data(data)

    def get_round_start_time(self):
        data = self.get_room_data()
        return data.get('round_start_time', 0)  # Время в миллисекундах

    def set_round_start_time(self, start_time):
        data = self.get_room_data()
        data['round_start_time'] = start_time
        self.set_room_data(data)

    def clear_room(self):
        self.redis_client.delete(self.key)

    @staticmethod
    def create_room(room_id, player1_id, player2_id):
        room = GameRooms(room_id)
        initial_data = {
            "room_id": room_id,
            "player1_id": player1_id,
            "player2_id": player2_id,
            "status": "waiting",
            "round": 1,
            "round_start_time": 0,  # Изначально 0
            "winner_id": None
        }
        room.set_room_data(initial_data)
        return room