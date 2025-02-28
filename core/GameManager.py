import threading
import time
import random
from flask_socketio import emit
from classes.UserOnServer import UserOnServer
from classes.GameRooms import GameRooms
from server import socketio, app
from core.RoundLogic import resolve_round, Player
import json
from classes.game_manager_store import active_game_managers
from skill.skills import skills

socketio.init_app(app)

class GameManager:
    def __init__(self, room_id):
        self.room_id = room_id
        self.game_room = GameRooms(room_id)
        self.is_running = True
        self.players_ready = set()

    def start(self):
        thread = threading.Thread(target=self.run, daemon=True)
        thread.start()

    def player_joined(self, player_id):
        self.players_ready.add(player_id)

    def are_all_players_ready(self):
        player1_id = self.game_room.get_player1_id()
        player2_id = self.game_room.get_player2_id()
        return player1_id in self.players_ready and player2_id in self.players_ready

    def send_ui_data(self, player_id, round_number):
        user = UserOnServer(player_id)
        sid = user.get_sid()
        if not sid:
            return

        player1_id = self.game_room.get_player1_id()
        player2_id = self.game_room.get_player2_id()
        opponent_id = player2_id if player_id == player1_id else player1_id
        opponent = UserOnServer(opponent_id)

        player1_round_values = UserOnServer(player1_id).get_round_values()
        player1_buffs = {
            name: {
                "duration": data["duration"],
                "trigger_conditions": data["trigger_conditions"],
                "stacks": data.get("stacks", 1)
            }
            for name, data in player1_round_values.get("active_buffs", {}).items()
        }
        player1_debuffs = {
            name: {"duration": data["duration"], "stacks": data.get("stacks", 1)}
            for name, data in player1_round_values.get("active_debuffs", {}).items()
        }

        player2_round_values = UserOnServer(player2_id).get_round_values()
        player2_buffs = {
            name: {
                "duration": data["duration"],
                "trigger_conditions": data["trigger_conditions"],
                "stacks": data.get("stacks", 1)
            }
            for name, data in player2_round_values.get("active_buffs", {}).items()
        }
        player2_debuffs = {
            name: {"duration": data["duration"], "stacks": data.get("stacks", 1)}
            for name, data in player2_round_values.get("active_debuffs", {}).items()
        }

        player_skills = user.get_character().get("skills", {})
        player_skills_data = {
            str(id): {"base_action": skills[int(id)].base_action, "level": skills[int(id)].level}
            for id in player_skills.keys()
        }
        opponent_skills = opponent.get_character().get("skills", {})
        opponent_skills_data = {
            str(id): {"base_action": skills[int(id)].base_action, "level": skills[int(id)].level}
            for id in opponent_skills.keys()
        }

        round_start_time = self.game_room.get_round_start_time()
        current_time = time.time() * 1000
        elapsed_time = (current_time - round_start_time) / 1000
        round_duration = 15
        remaining_time = max(0, round_duration - elapsed_time)

        player_round_values = user.get_round_values()
        super_cooldowns = player_round_values.get("skill_cooldowns", {})
        blocked_actions = {
            action: max(0, player_round_values.get(f"blocked{action}", 0) - int(elapsed_time / round_duration))
            for action in ["Attack", "Defence", "Parry", "Kick", "Heal"]
        }

        opponent_round_values = opponent.get_round_values()
        opponent_super_cooldowns = opponent_round_values.get("skill_cooldowns", {})
        opponent_blocked_actions = {
            action: max(0, opponent_round_values.get(f"blocked{action}", 0) - int(elapsed_time / round_duration))
            for action in ["Attack", "Defence", "Parry", "Kick", "Heal"]
        }

        ui_data = {
            "status": user.get_status(),
            "gameStatus": user.get_game_status(),
            "rating": user.get_rating(),
            "player": player_id,
            "room": user.get_room(),
            "character": user.get_character() or {},
            "round_values": {
                **player_round_values,
                "skill_cooldowns": {k: max(0, v - int(elapsed_time / round_duration)) for k, v in super_cooldowns.items()},
                **{f"blocked{action}": value for action, value in blocked_actions.items()}
            },
            "avg": user.get_avg(),
            "sid": sid,
            "is_player1": (player_id == player1_id),
            "round_number": round_number,
            "round_start_time": round_start_time,
            "round_remaining_time": remaining_time,
            "skills": player_skills_data,
            "selected_skills": user.get_selected_skills(),
            "action_committed": user.get_action_committed(),
            "player1_buffs": player1_buffs,
            "player1_debuffs": player1_debuffs,
            "player2_buffs": player2_buffs,
            "player2_debuffs": player2_debuffs,
            "opponent": {
                "status": opponent.get_status(),
                "gameStatus": opponent.get_game_status(),
                "rating": opponent.get_rating(),
                "player": opponent_id,
                "room": opponent.get_room(),
                "character": opponent.get_character() or {},
                "round_values": {
                    **opponent_round_values,
                    "skill_cooldowns": {k: max(0, v - int(elapsed_time / round_duration)) for k, v in opponent_super_cooldowns.items()},
                    **{f"blocked{action}": value for action, value in opponent_blocked_actions.items()}
                },
                "avg": opponent.get_avg(),
                "sid": opponent.get_sid(),
                "selected_skills": opponent.get_selected_skills(),
                "action_committed": opponent.get_action_committed(),
                "skills": opponent_skills_data
            }
        }
        socketio.emit('update_ui', ui_data, to=sid)

    def run(self):
        player1_id = self.game_room.get_player1_id()
        player2_id = self.game_room.get_player2_id()

        for player_id in [player1_id, player2_id]:
            user = UserOnServer(player_id)
            sid = user.get_sid()
            if sid:
                socketio.emit('redirect_to_game', {'url': '/game'}, to=sid)
        
        while not self.are_all_players_ready():
            time.sleep(1)

        for player_id in [player1_id, player2_id]:
            self.send_ui_data(player_id, self.game_room.get_round())

        for player_id in [player1_id, player2_id]:
            user = UserOnServer(player_id)
            sid = user.get_sid()
            opponent_id = player2_id if player_id == player1_id else player1_id
            opponent = UserOnServer(opponent_id)
            if sid:
                avg_data = {
                    "player": player_id,
                    "rating": user.get_rating(),
                    "character": user.get_character() or {},
                    "opponent": {
                        "player": opponent_id,
                        "rating": opponent.get_rating(),
                        "character": opponent.get_character() or {}
                    }
                }
                socketio.emit('prepare_avg', avg_data, to=sid)

                player_skills = user.get_character().get("skills", {})
                skill_data = {
                    "player": player_id,
                    "skills": {
                        str(id): {"base_action": skills[int(id)].base_action, "level": skills[int(id)].level}
                        for id in player_skills.keys()
                    }
                }
                socketio.emit('prepare_skill', skill_data, to=sid)
        
        time.sleep(10)

        for player_id in [player1_id, player2_id]:
            user = UserOnServer(player_id)
            if not user.get_selected_skills():
                player_skills = user.get_character().get("skills", {})
                if player_skills:
                    random_skill = random.choice(list(player_skills.keys()))
                    user.set_selected_skill(random_skill)
                    print(f"[{player_id}] Auto-selected '{skills[int(random_skill)].display_name}'")

        round_number = 1
        round_data = {"room_id": self.room_id, "round": round_number}
        for player_id in [player1_id, player2_id]:
            user = UserOnServer(player_id)
            sid = user.get_sid()
            if sid:
                socketio.emit('round_result', round_data, to=sid)

        while self.is_running:
            start_time = time.time() * 1000
            self.game_room.set_round_start_time(start_time)
            self.send_ui_update(round_number)
            time.sleep(15)
            
            self.process_round(round_number)
            self.send_ui_update(round_number)

            player1_hp = UserOnServer(player1_id).get_round_values().get("currentHP", 0)
            player2_hp = UserOnServer(player2_id).get_round_values().get("currentHP", 0)
            if player1_hp <= 0 or player2_hp <= 0:
                self.game_over(player1_hp, player2_hp)
                break

            for player_id in [player1_id, player2_id]:
                user = UserOnServer(player_id)
                sid = user.get_sid()
                if sid:
                    player_skills = user.get_character().get("skills", {})
                    socketio.emit('prepare_skill', {
                        "player": player_id,
                        "skills": {
                            str(id): {"base_action": skills[int(id)].base_action, "level": skills[int(id)].level}
                            for id in player_skills.keys()
                        }
                    }, to=sid)

            time.sleep(10)

            for player_id in [player1_id, player2_id]:
                user = UserOnServer(player_id)
                if not user.get_selected_skills():
                    player_skills = user.get_character().get("skills", {})
                    if player_skills:
                        random_skill = random.choice(list(player_skills.keys()))
                        user.set_selected_skill(random_skill)
                        print(f"[{player_id}] Auto-selected '{skills[int(random_skill)].display_name}' in round {round_number}")

            round_number += 1
            self.game_room.set_round(round_number)

    def process_round(self, round_number):
        player1_id = self.game_room.get_player1_id()
        player2_id = self.game_room.get_player2_id()
        
        if not player1_id or not player2_id:
            return
        
        user1 = UserOnServer(player1_id)
        user2 = UserOnServer(player2_id)
        
        char1 = user1.get_character()
        char2 = user2.get_character()
        if not char1 or not char2:
            return
        
        p1 = Player(char1)
        p2 = Player(char2)
        p1.enemy = p2
        p2.enemy = p1
        
        p1_skills = user1.get_selected_skills()
        p2_skills = user2.get_selected_skills()
        for skill in p1_skills:
            p1.set_skill(skill['id'], skill['level'])
        for skill in p2_skills:
            p2.set_skill(skill['id'], skill['level'])
        
        p1_round_values = user1.get_round_values()
        p2_round_values = user2.get_round_values()
        for key, value in p1_round_values.items():
            if hasattr(p1, key):
                setattr(p1, key, value)
        for key, value in p2_round_values.items():
            if hasattr(p2, key):
                setattr(p2, key, value)
        
        p1.load_effects(p1_round_values.get("active_debuffs", {}))
        p2.load_effects(p2_round_values.get("active_debuffs", {}))
        p1.load_buffs(p1_round_values.get("active_buffs", {}))
        p2.load_buffs(p2_round_values.get("active_buffs", {}))

        resolve_round(p1, p2, p1_round_values.get("action", "Idle"), p2_round_values.get("action", "Idle"))
        
        p1_data = {key: value for key, value in vars(p1).items() if isinstance(value, (int, float, str, bool, type(None)))}
        p1_data["action"] = "Idle"
        p1_data["currentPowerBar"] = 0
        p1_data["skill_cooldowns"] = p1.skill_cooldowns
        p1_data["active_buffs"] = {
            name: {
                "duration": data["duration"],
                "visual_duration": data["visual_duration"],
                "name": data["instance"].name,
                "trigger_conditions": data["trigger_conditions"],
                "effect_applied": data["effect_applied"],
                "buff_applied_this_round": data["buff_applied_this_round"],
                "stacks": data["stacks"],
                "level": data["level"]
            } for name, data in p1.active_buffs.items()
        }
        p1_data["active_debuffs"] = {
            name: {
                "duration": data["duration"],
                "visual_duration": data["visual_duration"],
                "name": data["instance"].name,
                "trigger_conditions": data["trigger_conditions"],
                "effect_applied": data["effect_applied"],
                "buff_applied_this_round": data["buff_applied_this_round"],
                "stacks": data["stacks"],
                "level": data["level"],
                "max_stacks": data["instance"].max_stacks
            } for name, data in p1.active_debuffs.items()
        }
        user1.set_round_values(p1_data)
        
        p2_data = {key: value for key, value in vars(p2).items() if isinstance(value, (int, float, str, bool, type(None)))}
        p2_data["action"] = "Idle"
        p2_data["currentPowerBar"] = 0
        p2_data["skill_cooldowns"] = p2.skill_cooldowns
        p2_data["active_buffs"] = {
            name: {
                "duration": data["duration"],
                "visual_duration": data["visual_duration"],
                "name": data["instance"].name,
                "trigger_conditions": data["trigger_conditions"],
                "effect_applied": data["effect_applied"],
                "buff_applied_this_round": data["buff_applied_this_round"],
                "stacks": data["stacks"],
                "level": data["level"]
            } for name, data in p2.active_buffs.items()
        }
        p2_data["active_debuffs"] = {
            name: {
                "duration": data["duration"],
                "visual_duration": data["visual_duration"],
                "name": data["instance"].name,
                "trigger_conditions": data["trigger_conditions"],
                "effect_applied": data["effect_applied"],
                "buff_applied_this_round": data["buff_applied_this_round"],
                "stacks": data["stacks"],
                "level": data["level"],
                "max_stacks": data["instance"].max_stacks
            } for name, data in p2.active_debuffs.items()
        }
        user2.set_round_values(p2_data)
        
        user1.set_action_committed(False)
        user2.set_action_committed(False)
        
        round_data = {
            "room_id": self.room_id,
            "round": round_number,
            "player1_action": f"{p1.character['name']} used '{p1_round_values.get('action', 'Idle')}' (Damage: {p1.roundDamage:.1f}, Heal: {p1.roundHeal:.1f})",
            "player2_action": f"{p2.character['name']} used '{p2_round_values.get('action', 'Idle')}' (Damage: {p2.roundDamage:.1f}, Heal: {p2.roundHeal:.1f})"
        }
        
        for player_id in [player1_id, player2_id]:
            user = UserOnServer(player_id)
            sid = user.get_sid()
            if sid:
                socketio.emit('round_result', round_data, to=sid)

    def send_ui_update(self, round_number):
        player1_id = self.game_room.get_player1_id()
        player2_id = self.game_room.get_player2_id()
        for player_id in [player1_id, player2_id]:
            self.send_ui_data(player_id, round_number)

    def stop(self):
        self.is_running = False
        self.game_room.clear_room()
        if self.room_id in active_game_managers:
            del active_game_managers[self.room_id]

    def game_over(self, player1_hp, player2_hp):
        player1_id = self.game_room.get_player1_id()
        player2_id = self.game_room.get_player2_id()
        
        user1 = UserOnServer(player1_id)
        user2 = UserOnServer(player2_id)
        user1_avg = user1.get_avg()
        user2_avg = user2.get_avg()

        with open("users.json", "r") as file:
            users_data = json.load(file)
        player1_rating = users_data[player1_id]["rating"]
        player2_rating = users_data[player2_id]["rating"]
        winner_id = None
        if player1_hp > 0 and player2_hp <= 0:
            player1_rating += 50 + user1_avg
            player2_rating -= 50 + user2_avg
            winner_id = player1_id
            print(f"[Game] {player1_id} wins! Ratings: {player1_id}={player1_rating}, {player2_id}={player2_rating}")
        elif player2_hp > 0 and player1_hp <= 0:
            player2_rating += 50 + user2_avg
            player1_rating -= 50 + user1_avg
            winner_id = player2_id
            print(f"[Game] {player2_id} wins! Ratings: {player1_id}={player1_rating}, {player2_id}={player2_rating}")
        else:
            player1_rating -= 25 + user1_avg
            player2_rating -= 25 + user2_avg
            winner_id = None
            print(f"[Game] Draw! Ratings: {player1_id}={player1_rating}, {player2_id}={player2_rating}")

        if player1_id in users_data:
            users_data[player1_id]["rating"] = player1_rating
        if player2_id in users_data:
            users_data[player2_id]["rating"] = player2_rating
        
        with open("users.json", "w") as file:
            json.dump(users_data, file, indent=4)

        user1.set_rating(player1_rating)
        user2.set_rating(player2_rating)
        
        user1.clear_room()
        user2.clear_room()
        user1.set_game_status("mainMenu")
        user2.set_game_status("mainMenu")
        user1.set_avg(0)
        user2.set_avg(0)
        for player_id in [player1_id, player2_id]:
            user = UserOnServer(player_id)
            sid = user.get_sid()
            if sid:
                socketio.emit('game_over', {
                    'message': 'Game has ended!',
                    'winner': winner_id,
                    'rating': player1_rating if player_id == player1_id else player2_rating
                }, to=sid)
        
        self.stop()