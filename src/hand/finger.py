from typing import List
from src.piano.keyNote import KeyNote


class Finger:
    def __init__(self, finger_index: int, key_note: KeyNote, is_left: bool = True, pressed: bool = False, is_keep_pressed: bool = False):
        self.finger_index = finger_index
        self.key_note = key_note
        self.is_left = is_left
        self.pressed = pressed
        self.is_keep_pressed = is_keep_pressed

    def _is_next_finger_too_far(self, next_finger: 'Finger', finger_range: float, finger_distribution: list[int]) -> bool:
        current_finger_index = self.finger_index if self.is_left else self.finger_index - \
            len(finger_distribution)
        next_finger_index = next_finger.finger_index if next_finger.is_left else next_finger.finger_index - \
            len(finger_distribution)
        valid_finger_distance = abs(
            finger_distribution[current_finger_index] - finger_distribution[next_finger_index]) * finger_range
        note_distance = abs(self.key_note.note - next_finger.key_note.note)

        return note_distance > valid_finger_distance

    def export_finger_info(self) -> dict:
        return {
            'finger_index': self.finger_index,
            'key_note': self.key_note.export_key_note_info(),
            'is_left': self.is_left,
            'pressed': self.pressed,
            'is_keep_pressed': self.is_keep_pressed
        }
