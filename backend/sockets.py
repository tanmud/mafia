import random
from typing import Dict, Any
import socketio
import httpx

from game_models import game_state, Player, Room
from game_logic import ensure_active_room, start_game, resolve_night, check_win, reset_game

PLAYER_NAMESPACE = "/"
CONTROL_NAMESPACE = "/control"

MCQ_SERVICE_URL = "http://localhost:9000/question"  # Ollama RAG service


def is_room_joinable(room: Room) -> bool:
    return room.phase in ("lobby", "ended")


def get_or_create_active_room() -> Room:
    return ensure_active_room()


def register_socket_handlers(sio: socketio.AsyncServer) -> None:
    # ---------- PLAYER NAMESPACE ----------

    @sio.event(namespace=PLAYER_NAMESPACE)
    async def connect(sid, environ):
        print("player connect", sid)

    @sio.event(namespace=PLAYER_NAMESPACE)
    async def disconnect(sid):
        print("player disconnect", sid)
        # On disconnect, keep them in room state for simplicity.

    async def broadcast_public_state():
        room = game_state.active_room
        if room:
            await sio.emit("room_state", room.public_state(), room=room.room_id, namespace=PLAYER_NAMESPACE)
        await sio.emit(
            "waiting_count",
            {"count": len(game_state.waiting_players)},
            room="waiting",
            namespace=PLAYER_NAMESPACE,
        )

    @sio.event(namespace=PLAYER_NAMESPACE)
    async def join_player(sid, data: Dict[str, Any]):
        """
        Called by regular players.
        data: { "name": str }
        """
        name = data.get("name") or "Player"

        room = get_or_create_active_room()

        # Decide whether this player joins active room or waiting
        if is_room_joinable(room):
            # join active game lobby
            is_first = len(room.players) == 0
            player = Player(socket_id=sid, name=name, is_host=is_first)
            room.players[sid] = player
            sio.enter_room(sid, room.room_id, namespace=PLAYER_NAMESPACE)
        else:
            # game in progress, join waiting
            player = Player(socket_id=sid, name=name, is_host=False)
            game_state.waiting_players[sid] = player
            sio.enter_room(sid, "waiting", namespace=PLAYER_NAMESPACE)

        await broadcast_public_state()

    @sio.event(namespace=PLAYER_NAMESPACE)
    async def night_kill(sid, data: Dict[str, Any]):
        """
        data: { "targetId": str }
        """
        room = game_state.active_room
        if not room or room.phase != "night":
            return

        if sid != room.godfather_id or not room.players.get(sid) or not room.players[sid].alive:
            return

        target_id = data.get("targetId")
        if not target_id or target_id not in room.players or not room.players[target_id].alive:
            return

        room.night_kill_target = target_id

    @sio.event(namespace=PLAYER_NAMESPACE)
    async def night_save(sid, data: Dict[str, Any]):
        """
        data: { "targetId": str }
        """
        room = game_state.active_room
        if not room or room.phase != "night":
            return

        if sid != room.doctor_id or not room.players.get(sid) or not room.players[sid].alive:
            return

        target_id = data.get("targetId")
        if not target_id or target_id not in room.players or not room.players[target_id].alive:
            return

        room.night_save_target = target_id

    @sio.event(namespace=PLAYER_NAMESPACE)
    async def mcq_answer(sid, data: Dict[str, Any]):
        """
        data: { "questionId": str, "targetId": str }
        All players (even dead) can answer.
        """
        room = game_state.active_room
        if not room or room.phase != "night":
            return

        qid = data.get("questionId")
        target_id = data.get("targetId")
        if not qid or not target_id:
            return

        if target_id not in room.players:
            return

        round_index = room.night_round or 1
        if round_index not in room.mcq_answers:
            room.mcq_answers[round_index] = {}
        room.mcq_answers[round_index][sid] = target_id

    # ---------- CONTROL NAMESPACE ----------

    @sio.event(namespace=CONTROL_NAMESPACE)
    async def connect(sid, environ):
        print("control connect", sid)
        await push_control_state()

    @sio.event(namespace=CONTROL_NAMESPACE)
    async def disconnect(sid):
        print("control disconnect", sid)

    async def push_control_state():
        room = game_state.active_room
        if room:
            public = room.public_state()
        else:
            public = None
        print('HERE')
        print(type(game_state.waiting_players), flush=True)
        await sio.emit(
            "control_state",
            {
                "activeRoom": public,
                "waitingCount": len(game_state.waiting_players),
                "waitingPlayers": [
                    {"id": p.socket_id, "name": p.name}
                    for p in game_state.waiting_players.values()
                ],
            },
            namespace=CONTROL_NAMESPACE,
        )

    @sio.event(namespace=CONTROL_NAMESPACE)
    async def control_set_doctor_enabled(sid, data: Dict[str, Any]):
        """
        data: { "enabled": bool }
        Applies to current or next game.
        """
        room = get_or_create_active_room()
        room.doctor_enabled = bool(data.get("enabled"))
        await broadcast_public_state()
        await push_control_state()

    @sio.event(namespace=CONTROL_NAMESPACE)
    async def control_start_game(sid, data: Dict[str, Any]):
        """
        Pulls waiting players into a fresh room and starts night.
        """

        # If no active room or active room already used, create/reset
        room = get_or_create_active_room()
        if room.phase != "lobby" and len(room.players) > 0:
            # cannot start if current game in progress; require reset
            return

        # Move waiting players into room
        for p in game_state.waiting_players.values():
            room.players[p.socket_id] = p
            sio.enter_room(p.socket_id, room.room_id, namespace=PLAYER_NAMESPACE)
            sio.leave_room(p.socket_id, "waiting", namespace=PLAYER_NAMESPACE)
        game_state.waiting_players.clear()

        if len(room.players) < 3:
            # require at least 3 players
            return

        # Auto-assign roles
        alive_players = list(room.players.values())
        for p in alive_players:
            p.role = "villager"
            p.alive = True

        random.shuffle(alive_players)
        godfather = alive_players[0]
        room.godfather_id = godfather.socket_id
        godfather.role = "godfather"

        if room.doctor_enabled and len(alive_players) >= 2:
            doctor = alive_players[1]
            room.doctor_id = doctor.socket_id
            doctor.role = "doctor"
        else:
            room.doctor_id = None

        # Start first night
        start_game(room)

        # Send private role info
        for p in room.players.values():
            await sio.emit(
                "role_info",
                {"role": p.role},
                to=p.socket_id,
                namespace=PLAYER_NAMESPACE,
            )

        # Ask MCQ service for a question
        await request_and_broadcast_mcq(room)

        await broadcast_public_state()
        await push_control_state()

    async def request_and_broadcast_mcq(room: Room):
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(MCQ_SERVICE_URL)
                resp.raise_for_status()
                payload = resp.json()
                qid = payload.get("id")
                text = payload.get("text")
        except Exception as e:
            print("MCQ service error", e)
            qid = None
            text = None

        if not qid or not text:
            # fallback simple question
            qid = f"q-{room.night_round}"
            text = "Who is most likely to survive a zombie apocalypse?"

        room.current_question_id = qid
        room.current_question_text = text

        options = [
            {"id": p.socket_id, "name": p.name, "alive": p.alive}
            for p in room.players.values()
        ]

        await sio.emit(
            "mcq_question",
            {"questionId": qid, "text": text, "options": options},
            room=room.room_id,
            namespace=PLAYER_NAMESPACE,
        )

    @sio.event(namespace=CONTROL_NAMESPACE)
    async def control_end_night(sid, data: Dict[str, Any]):
        """
        Host/GM ends night, resolves kill/save and moves to day or next night.
        """
        room = game_state.active_room
        if not room or room.phase != "night":
            return

        killed_id = resolve_night(room)
        winner = check_win(room)

        await sio.emit(
            "night_result",
            {"roomId": room.room_id, "killedId": killed_id, "winner": winner},
            room=room.room_id,
            namespace=PLAYER_NAMESPACE,
        )

        if winner:
            await broadcast_public_state()
            await push_control_state()
            return

        room.phase = "day"
        await sio.emit(
            "phase_change",
            {"roomId": room.room_id, "phase": room.phase},
            room=room.room_id,
            namespace=PLAYER_NAMESPACE,
        )
        await broadcast_public_state()
        await push_control_state()

    @sio.event(namespace=CONTROL_NAMESPACE)
    async def control_start_next_night(sid, data: Dict[str, Any]):
        """
        After day/votes, GM starts the next night, asks new MCQ.
        """
        room = game_state.active_room
        if not room or room.phase != "day":
            return

        room.phase = "night"
        room.night_round += 1

        await sio.emit(
            "phase_change",
            {"roomId": room.room_id, "phase": room.phase},
            room=room.room_id,
            namespace=PLAYER_NAMESPACE,
        )

        await request_and_broadcast_mcq(room)
        await broadcast_public_state()
        await push_control_state()

    @sio.event(namespace=CONTROL_NAMESPACE)
    async def control_reset_game(sid, data: Dict[str, Any]):
        """
        End game and clear active room; waiting players remain in waiting.
        """
        reset_game()
        await broadcast_public_state()
        await push_control_state()
