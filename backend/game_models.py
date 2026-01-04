from dataclasses import dataclass, field
from typing import Dict, Optional, Literal

Phase = Literal["lobby", "night", "day", "ended"]
Role = Literal["villager", "godfather", "doctor"]


@dataclass
class Player:
    socket_id: str
    name: str
    role: Role = "villager"
    alive: bool = True
    is_host: bool = False  # host in the sense of "room owner" (player), not controller UI


@dataclass
class Room:
    room_id: str
    phase: Phase = "lobby"
    players: Dict[str, Player] = field(default_factory=dict)

    godfather_id: Optional[str] = None
    doctor_id: Optional[str] = None
    doctor_enabled: bool = False

    # night actions
    night_kill_target: Optional[str] = None
    night_save_target: Optional[str] = None

    # MCQ
    current_question_id: Optional[str] = None
    current_question_text: Optional[str] = None
    mcq_answers: Dict[int, Dict[str, str]] = field(default_factory=dict)
    night_round: int = 0

    def public_state(self) -> dict:
        return {
            "roomId": self.room_id,
            "phase": self.phase,
            "doctorEnabled": self.doctor_enabled,
            "nightRound": self.night_round,
            "players": [
                {
                    "id": p.socket_id,
                    "name": p.name,
                    "alive": p.alive,
                    "isHost": p.is_host,
                }
                for p in self.players.values()
            ],
        }


@dataclass
class GameState:
    active_room: Optional[Room] = None
    waiting_players: Dict[str, Player] = field(default_factory=dict)


game_state = GameState()
