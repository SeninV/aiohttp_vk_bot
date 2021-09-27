from dataclasses import dataclass
from typing import List


@dataclass
class UpdateObject:
    id: int
    user_id: int
    peer_id: int
    body: str


@dataclass
class Update:
    type: str
    object: UpdateObject


@dataclass
class Message:
    peer_id: int
    text: str

@dataclass
class KeyboardMessage:
    peer_id: int
    text: str
    keyboard_text: List[str]
