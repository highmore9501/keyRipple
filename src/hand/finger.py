from typing import List
from src.piano.keyNote import KeyNote


class Finger:
    def __init__(self, finger_index: int, key_note: KeyNote, is_left: bool = True, pressed: bool = False):
        self.finger_index = finger_index
        self.key_note = key_note
        self.is_left = is_left
        self.pressed = pressed

    def export_finger_info(self) -> dict:
        return {
            'finger_index': self.finger_index,
            'key_note': self.key_note.export_key_note_info(),
            'is_left': self.is_left,
            'pressed': self.pressed
        }
