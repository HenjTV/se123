import json
import os
import bcrypt
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_socketio import SocketIO, emit
from threading import Thread
from classes.UserOnServer import UserOnServer
from classes.character import characters
from classes.game_manager_store import active_game_managers
import random

app = Flask(__name__)
app.secret_key = 'supersecretkey'
socketio = SocketIO(app, message_queue='redis://localhost:6379/')
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'index'
print(f"Проверка сервера сокетио: {socketio}")
USERS_FILE = 'users.json'

class User(UserMixin):
    def __init__(self, username):
        self.id = username

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, 'r') as file:
        return json.load(file)

def save_users(users):
    with open(USERS_FILE, 'w') as file:
        json.dump(users, file, indent=4)

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

@login_manager.user_loader
def load_user(username):
    users = load_users()
    if username in users:
        return User(username)
    return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/user_status')
def user_status():
    if current_user.is_authenticated:
        return jsonify({"authenticated": True, "username": current_user.id})
    return jsonify({"authenticated": False})

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username, password = data.get('username'), data.get('password')
    if ' ' in username or ' ' in password:
        return jsonify({'error': 'Логин и пароль не должны содержать пробелы'}), 400
    users = load_users()
    if username not in users or not check_password(password, users[username]['password_hash']):
        return jsonify({'error': 'Неверные учетные данные'}), 400
    user = load_user(username)
    login_user(user)
    return jsonify({'success': 'Вы успешно вошли'})

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username, password = data.get('username'), data.get('password')
    if ' ' in username or ' ' in password:
        return jsonify({'error': 'Логин и пароль не должны содержать пробелы'}), 400
    users = load_users()
    if username in users:
        return jsonify({'error': 'Такой пользователь уже существует'}), 400
    users[username] = {'password_hash': hash_password(password), 'rating': 1500}
    save_users(users)
    return jsonify({'success': 'Вы успешно зарегистрированы'})

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/characterlist')
@login_required
def characterlist():
    return render_template('characterlist.html', user=current_user, characters=characters)

@app.route('/game')
@login_required
def game():
    return render_template('game.html', username=current_user.id)

@socketio.on('request_ui_data')
def handle_request_ui_data(data):
    username = data.get('username')
    if not username or username != current_user.id:
        emit('error', {'message': 'Несоответствие имени пользователя или данных'})
        return
    
    user_on_server = UserOnServer(username)
    room_id = user_on_server.get_room()
    if not room_id:
        print(f"Пользователь {username} не в комнате")
        return

    from classes.GameRooms import GameRooms
    game_room = GameRooms(room_id)
    player1_id = game_room.get_player1_id()
    player2_id = game_room.get_player2_id()

    is_player1 = (username == player1_id)
    opponent_id = player2_id if is_player1 else player1_id

    player_data = user_on_server.get_user_data()
    opponent = UserOnServer(opponent_id)
    opponent_data = opponent.get_user_data()

    ui_data = {
        "status": player_data.get("status"),
        "gameStatus": player_data.get("gameStatus"),
        "rating": player_data.get("rating"),
        "player": username,
        "room": room_id,
        "character": player_data.get("character", {}),
        "round_values": player_data.get("round_values", {}),
        "avg": player_data.get("avg", 0),
        "sid": user_on_server.get_sid(),
        "is_player1": is_player1,
        "round_number": game_room.get_round(),
        "round_start_time": game_room.get_round_start_time(),
        "skills": player_data.get("character", {}).get("skills", {}),
        "selected_skills": player_data.get("selected_skills", []),  # Обновлено на массив
        "action_committed": user_on_server.get_action_committed(),
        "opponent": {
            "status": opponent_data.get("status"),
            "gameStatus": opponent_data.get("gameStatus"),
            "rating": opponent_data.get("rating"),
            "player": opponent_id,
            "room": opponent_data.get("room"),
            "character": opponent_data.get("character", {}),
            "round_values": opponent_data.get("round_values", {}),
            "avg": opponent_data.get("avg", 0),
            "sid": opponent.get_sid(),
            "selected_skills": opponent_data.get("selected_skills", []),  # Обновлено на массив
            "action_committed": opponent.get_action_committed()
        }
    }
    emit('update_ui', ui_data)

@socketio.on('connect')
def handle_connect(auth):
    user_on_server = UserOnServer(current_user.id)
    print(f'Пользователь {current_user.id} подключился')
    user_on_server.set_status('online')
    user_on_server.get_game_status()
    print(f'Пользователь {current_user.id} подключен и статус установлен в online')
    sid = request.sid
    data = {"message": "Привет от сервера!"}
    user_on_server.set_sid(sid)
    sid = user_on_server.get_sid()
    socketio.emit('custom_event', data)
    if sid:
        print(f'SID для пользователя {current_user.id} успешно установлен: {sid}')
    else:
        print(f'Ошибка: SID для пользователя {current_user.id} не был установлен.')

@socketio.on('disconnect')
def handle_disconnect():
    user_on_server = UserOnServer(current_user.id)
    user_on_server.set_status('offline')
    user_on_server.set_game_status('mainMenu')
    user_on_server.clear_sid()
    print(f'Пользователь {current_user.id} отключен и статус установлен в offline')

@socketio.on('select_character')
def handle_select_character(data):
    username = data.get('username')
    character_name = data.get('character')
    
    if not username or not character_name:
        emit('error', {'message': 'Недостаточно данных для выбора персонажа'})
        return
    
    if username != current_user.id:
        emit('error', {'message': 'Несоответствие имени пользователя'})
        return
    
    user_on_server = UserOnServer(username)
    if user_on_server.get_room():
        emit('error', {'message': 'Нельзя сменить персонажа во время игры'})
        return
    
    character_data = characters.get(character_name.lower())
    if not character_data:
        emit('error', {'message': f'Персонаж "{character_name}" не найден'})
        return
    
    round_values = {
        "action": "Idle",
        "currentAttackPower": character_data["AttackPower"],
        "currentDefencePower": character_data["DefencePower"],
        "currentParryPower": character_data["ParryPower"],
        "currentKickPower": character_data["KickPower"],
        "currentHealPower": character_data["HealPower"],
        "currentHP": character_data["maxHP"],
        "currentPowerBar": 0,
        "currentArmour": character_data["Armour"],
        "currentBreak": character_data["baseBreak"],
        "currentCounterDamage": character_data["CounterDamage"],
        "currentResource": character_data["resourceBaseValue"],
        "currentResourceRegen": character_data["ResourceRegen"],
        "blockedAttack": 0,
        "blockedDefence": 0,
        "blockedParry": 0,
        "blockedKick": 0,
        "blockedHeal": 0,
        "skill_cooldown": 0,
        "canBeBlockedAttack": False,
        "canBeBlockedDefence": True,
        "canBeBlockedParry": False,
        "canBeBlockedKick": False,
        "canBeBlockedHeal": True,
        "canBeInterruptedAttack": False,
        "canBeInterruptedDefence": True,
        "canBeInterruptedParry": False,
        "canBeInterruptedKick": False,
        "canInterruptedHeal": True,
        "roundBaseDamage": 0,
        "roundTrueDamage": 0,
        "roundTrueHeal": 0,
        "roundBaseHeal": 0,
        "roundBaseParry": 0,
        "roundDeadly": 0,
        "roundArmour": 0,
        "roundBreak": 0,
        "roundDamage": 0,
        "roundHeal": 0,
        "roundInterrupt": 0,
        "roundResourceSpended": 0,
        "active_buffs": {},
        "active_debuffs": {},
        "total_healing_reduction": 0
    }
    
    user_on_server.set_player(player_id=username)
    user_on_server.set_character(character_data)
    user_on_server.set_round_values(round_values)
    
    emit('character_selected', {'username': username, 'character': character_name})
    print(f'Пользователь {username} выбрал персонажа: {character_name}')

@socketio.on('select_skill')
def handle_select_skill(data):
    username = data.get('username')
    skill_id = data.get('skill_id')
    
    #print(f"Received select_skill: username={username}, skill_id={skill_id}, type={type(skill_id)}")
    
    if username != current_user.id or not skill_id:
        emit('error', {'message': 'Недостаточно данных или несоответствие пользователя'})
        return
    
    user = UserOnServer(username)
    character = user.get_character()
    skills = character.get("skills", {})
    print(f"Character data for {username}: {character}")
    print(f"Available super abilities: {skills}")
    
    # Изменение: убрано преобразование в int, так как skill_id теперь строка
    if skill_id not in skills:
        emit('error', {'message': 'Недопустимая суперспособность'})
        print(f"Error: {skill_id} not in {list(skills.keys())}")
        return
    
    user.set_selected_skill(skill_id)  # Работает с массивом и строковым skill_id
    emit('skill_selected', {'username': username, 'skill_id': skill_id})
    print(f'Пользователь {username} выбрал суперспособность: {skill_id}')

@socketio.on('startQue')
def handle_start_que(data):
    username = data.get('username')
    
    if not username:
        emit('error', {'message': 'Недостаточно данных для начала очереди'})
        return
    
    if username != current_user.id:
        emit('error', {'message': 'Несоответствие имени пользователя'})
        return
    
    user_on_server = UserOnServer(username)
    user_on_server.set_game_status('startQue')
    print(f'Пользователь {username} начал очередь (gameStatus: startQue)')

@socketio.on('stop_que')
def handle_stop_que(data):
    username = data.get('username')
    
    if not username:
        emit('error', {'message': 'Недостаточно данных для остановки очереди'})
        return
    
    if username != current_user.id:
        emit('error', {'message': 'Несоответствие имени пользователя'})
        return
    
    user_on_server = UserOnServer(username)
    user_on_server.set_game_status('mainMenu')
    print(f'Пользователь {username} остановил очередь (gameStatus: mainMenu)')

@socketio.on('player_action')
def handle_player_action(data):
    username = data.get('username')
    action = data.get('action', "Idle")
    powerbar_value = data.get('powerbarValue', 0)
    print(f"Пользователь {username} выбрал действие '{action}' с силой {powerbar_value}")
    if not username:
        print("Ошибка: отсутствует имя пользователя.")
        return
    
    user = UserOnServer(username)
    if user.get_action_committed():
        print(f"Действие для {username} уже зафиксировано")
        return
    
    round_values = user.get_round_values()
    
    blocked_actions = {
        "Attack": round_values.get("blockedAttack", 0),
        "Defence": round_values.get("blockedDefence", 0),
        "Parry": round_values.get("blockedParry", 0),
        "Kick": round_values.get("blockedKick", 0),
        "Heal": round_values.get("blockedHeal", 0)
    }
    
    if blocked_actions.get(action, 0) > 0:
        print(f"Действие '{action}' заблокировано для {username} ещё на {blocked_actions[action]} раундов.")
        return
    
    round_values.update({"action": action, "currentPowerBar": powerbar_value})
    user.set_round_values(round_values)
    user.set_action_committed(True)
    print(f"Игрок {username} зафиксировал {action} с силой {powerbar_value}")

@socketio.on('joined_game')
def handle_joined_game(data):
    username = data.get('username')
    if not username:
        emit('error', {'message': 'Отсутствует имя пользователя'})
        return
    user_on_server = UserOnServer(username)
    room_id = user_on_server.get_room()
    print(f"joined_game: username={username}, room_id={room_id}, active_game_managers={list(active_game_managers.keys())}")
    if room_id:
        game_manager = active_game_managers.get(room_id)
        if game_manager:
            game_manager.player_joined(username)
            game_manager.send_ui_data(username, game_manager.game_room.get_round())
            print(f"Игрок {username} подтвердил загрузку в комнате {room_id} и получил UI данные")
        else:
            print(f"Ошибка: GameManager для комнаты {room_id} не найден")

@socketio.on('leave_game')
def handle_leave_game(data):
    username = data.get('username')
    if not username or username != current_user.id:
        emit('error', {'message': 'Несоответствие имени пользователя'})
        return
    
    user_on_server = UserOnServer(username)
    room_id = user_on_server.get_room()
    if room_id:
        current_round_values = user_on_server.get_round_values()
        current_round_values['currentHP'] = 0
        user_on_server.set_round_values(current_round_values)
        user_on_server.set_game_status('mainMenu')
        print(f"Пользователь {username} покинул игру в комнате {room_id} и считается проигравшим (HP = 0)")

@socketio.on('set_avg')
def handle_set_avg(data):
    username = data.get('username')
    avg = data.get('avg')
    if not username or username != current_user.id:
        emit('error', {'message': 'Несоответствие имени пользователя'})
        return
    user_on_server = UserOnServer(username)
    user_on_server.set_avg(avg)
    print(f"Пользователь {username} установил avg: {avg}")

def start_matchmaker():
    from core.MatchMaker import matchmaking_loop
    print("Запуск системы поиска игры...")
    socketio.start_background_task(target=matchmaking_loop)
    print(f"Матчмейкер запущен в процессе: {os.getpid()}")

if __name__ == '__main__':
    if not hasattr(app, 'matchmaker_running'):
        app.matchmaker_running = True
        matchmaker_thread = Thread(target=start_matchmaker, daemon=True)
        matchmaker_thread.start()
    socketio.run(app, host="0.0.0.0", port=5000, debug=True, use_reloader=False)