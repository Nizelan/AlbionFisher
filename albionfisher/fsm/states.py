"""Fishing cycle states (SPEC §5)."""

from enum import Enum


class State(Enum):
    IDLE = "IDLE"
    FIND_ZONE = "FIND_ZONE"
    CAST = "CAST"
    WAIT_BITE = "WAIT_BITE"
    HOOK = "HOOK"
    MINIGAME = "MINIGAME"
    RESULT = "RESULT"
