from dataclasses import dataclass, field
from typing import Dict, Optional, Literal

Phase = Literal['lobby', 'night', 'day', 'game_over']
Role = Literal['villager', 'godfather', 'volunteer']

@dataclass
class Player:
    socket_id: str
    name: str
    role: Role = "villager"
    alive: bool = True
    isHost: bool = False

@dataclass
class Room:
    