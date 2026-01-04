from typing import Optional
from game_models import Room, game_state


def ensure_active_room() -> Room:
    if game_state.active_room is None:
        game_state.active_room = Room(room_id="game")
    return game_state.active_room


def start_game(room: Room) -> None:
    room.phase = "night"
    room.night_round = 1


def resolve_night(room: Room) -> Optional[str]:
    killed_id = room.night_kill_target

    if killed_id and killed_id == room.night_save_target:
        killed_id = None

    if killed_id and killed_id in room.players:
        room.players[killed_id].alive = False

    room.night_kill_target = None
    room.night_save_target = None
    room.current_question_id = None
    room.current_question_text = None

    return killed_id


def alive_counts(room: Room) -> tuple[int, int]:
    mafia = 0
    village = 0
    for sid, p in room.players.items():
        if not p.alive:
            continue
        if sid == room.godfather_id:
            mafia += 1
        else:
            village += 1
    return mafia, village


def check_win(room: Room) -> Optional[str]:
    mafia, village = alive_counts(room)
    if mafia == 0:
        room.phase = "ended"
        return "village"
    if mafia >= village:
        room.phase = "ended"
        return "mafia"
    return None


def reset_game() -> None:
    game_state.active_room = None
    game_state.waiting_players.clear()
