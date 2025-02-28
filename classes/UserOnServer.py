import redis
import json

redis_client = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)

class UserOnServer:
    def __init__(self, username):
        self.username = username
        self.redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)
        self.key = f"user:{username}"
        self.sid_key = f"user:{username}:sid"

    def get_user_data(self):
        data = self.redis_client.get(self.key)
        if data:
            return json.loads(data)
        #print(f"[{self.username}] No user data found in Redis, returning empty dict")
        return {}

    def set_user_data(self, data):
        self.redis_client.set(self.key, json.dumps(data))
        #print(f"[{self.username}] User data updated in Redis")

    def get_status(self):
        data = self.get_user_data()
        status = data.get('status', 'offline')
        #print(f"[{self.username}] Retrieved status: {status}")
        return status

    def set_status(self, status):
        data = self.get_user_data()
        data['status'] = status
        self.set_user_data(data)
        print(f"[{self.username}] Status set to: {status}")

    def get_game_status(self):
        data = self.get_user_data()
        game_status = data.get('gameStatus', 'mainMenu')
        #print(f"[{self.username}] Retrieved game status: {game_status}")
        return game_status

    def set_game_status(self, game_status):
        data = self.get_user_data()
        data['gameStatus'] = game_status
        self.set_user_data(data)
        print(f"[{self.username}] Game status set to: {game_status}")

    def get_rating(self):
        data = self.get_user_data()
        rating = data.get('rating', 0)
        #print(f"[{self.username}] Retrieved rating: {rating}")
        return rating

    def set_rating(self, rating):
        data = self.get_user_data()
        data['rating'] = rating
        self.set_user_data(data)
        print(f"[{self.username}] Rating set to: {rating}")

    def get_room(self):
        data = self.get_user_data()
        room = data.get('room', None)
        #print(f"[{self.username}] Retrieved room: {room}")
        return room

    def set_room(self, room_id):
        data = self.get_user_data()
        data['room'] = room_id
        self.set_user_data(data)
        print(f"[{self.username}] Room set to: {room_id}")

    def clear_room(self):
        data = self.get_user_data()
        data.pop('room', None)
        self.set_user_data(data)
        print(f"[{self.username}] Room cleared")

    def get_open_scene(self):
        data = self.get_user_data()
        open_scene = data.get('open_scene', None)
        #print(f"[{self.username}] Retrieved open scene: {open_scene}")
        return open_scene

    def set_open_scene(self, open_scene):
        data = self.get_user_data()
        data['open_scene'] = open_scene
        self.set_user_data(data)
        print(f"[{self.username}] Open scene set to: {open_scene}")

    def get_player(self):
        data = self.get_user_data()
        player = data.get('player', None)
        #print(f"[{self.username}] Retrieved player: {player}")
        return player

    def set_player(self, player_id):
        data = self.get_user_data()
        data['player'] = player_id
        self.set_user_data(data)
        print(f"[{self.username}] Player set to: {player_id}")

    def clear_player(self):
        data = self.get_user_data()
        data.pop('player', None)
        self.set_user_data(data)
        print(f"[{self.username}] Player cleared")

    def get_character(self):
        data = self.get_user_data()
        character = data.get('character', {})
        #print(f"[{self.username}] Retrieved character: {character.get('name', 'No character')}")
        return character

    def set_character(self, character_data):
        data = self.get_user_data()
        data['character'] = character_data
        self.set_user_data(data)
        print(f"[{self.username}] Character set to: {character_data.get('name')}")

    def update_character(self, updates):
        data = self.get_user_data()
        character = data.get('character', {})
        character.update(updates)
        data['character'] = character
        self.set_user_data(data)
        print(f"[{self.username}] Character updated with: {updates}")

    def clear_character(self):
        data = self.get_user_data()
        data.pop('character', None)
        self.set_user_data(data)
        print(f"[{self.username}] Character cleared")

    def get_round_values(self):
        data = self.get_user_data()
        round_values = data.get('round_values', {})
        if 'skill_cooldowns' not in round_values:
            round_values['skill_cooldowns'] = {}
        #print(f"[{self.username}] Retrieved round values: HP={round_values.get('currentHP', 'N/A')}, skills={round_values.get('selected_skills', 'None')}")
        return round_values

    def set_round_values(self, round_values):
        data = self.get_user_data()
        data['round_values'] = round_values
        self.set_user_data(data)
        print(f"[{self.username}] Round values set: HP={round_values.get('currentHP', 'N/A')}")

    def update_round_values(self, updates):
        data = self.get_user_data()
        round_values = data.get('round_values', {})
        round_values.update(updates)
        data['round_values'] = round_values
        self.set_user_data(data)
        print(f"[{self.username}] Round values updated with: {updates}")

    def clear_round_values(self):
        data = self.get_user_data()
        data.pop('round_values', None)
        self.set_user_data(data)
        print(f"[{self.username}] Round values cleared")

    def get_avg(self):
        data = self.get_user_data()
        avg = data.get('avg', 0)
        #print(f"[{self.username}] Retrieved avg: {avg}")
        return avg

    def set_avg(self, avg_value):
        data = self.get_user_data()
        data['avg'] = avg_value
        self.set_user_data(data)
        #print(f"[{self.username}] Avg set to: {avg_value}")

    def clear_avg(self):
        data = self.get_user_data()
        data.pop('avg', None)
        self.set_user_data(data)
        #print(f"[{self.username}] Avg cleared")

    def set_sid(self, sid):
        data = self.get_user_data()
        data['sid'] = sid
        self.set_user_data(data)
        print(f"[{self.username}] SID set to: {sid}")

    def get_sid(self):
        data = self.get_user_data()
        sid = data.get('sid', None)
        #print(f"[{self.username}] Retrieved SID: {sid}")
        return sid

    def clear_sid(self):
        data = self.get_user_data()
        data.pop('sid', None)
        self.set_user_data(data)
        print(f"[{self.username}] SID cleared")

    def get_selected_skills(self):
        data = self.get_user_data()
        selected_skills = data.get('selected_skills', [])
        #print(f"[{self.username}] Retrieved selected skills: {[s['id'] + f' (Level {s['level']})' for s in selected_skills]}")
        return selected_skills

    def set_selected_skill(self, skill_id):
        from skill.skills import skills
        data = self.get_user_data()
        selected_skills = data.get('selected_skills', [])
        skill = skills[int(skill_id)]
        base_action = skill.base_action
        
        # Получаем текущие кулдауны
        round_values = self.get_round_values()
        current_cooldowns = round_values.get('skill_cooldowns', {})
        
        # Проверяем, есть ли навык с таким base_action
        for t in selected_skills:
            if t['base_action'] == base_action:
                old_level = t['level']
                t['level'] += 1
                print(f"[{self.username}] Upgraded skill {skill_id} from level {old_level} to {t['level']}")
                if base_action in current_cooldowns:
                    t['cooldown'] = current_cooldowns[base_action]
                break
        else:
            new_skill = {"id": str(skill_id), "level": 1, "base_action": base_action}
            selected_skills.append(new_skill)
            current_cooldowns[base_action] = 0
            print(f"[{self.username}] Added new skill {skill_id} at level 1")
        
        data['selected_skills'] = selected_skills
        round_values['skill_cooldowns'] = current_cooldowns
        data['round_values'] = round_values
        self.set_user_data(data)

    def clear_selected_skills(self):
        data = self.get_user_data()
        data.pop('selected_skills', None)
        self.set_user_data(data)
        print(f"[{self.username}] Selected skills cleared")

    def set_action_committed(self, committed=True):
        data = self.get_user_data()
        data['action_committed'] = committed
        self.set_user_data(data)
        print(f"[{self.username}] Action committed set to: {committed}")

    def get_action_committed(self):
        data = self.get_user_data()
        committed = data.get('action_committed', False)
        #print(f"[{self.username}] Retrieved action committed: {committed}")
        return committed