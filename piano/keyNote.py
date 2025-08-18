class KeyNote:
    """
    钢琴键信息,包含键值和键位置，以及是否黑键
    """

    def __init__(self, note: int, position: int, is_black: bool):
        self.note = note
        self.position = position
        self.is_black = is_black

    def export_key_note_info(self) -> dict:
        return {
            'note': self.note,
            'position': self.position,
            'is_black': self.is_black
        }
