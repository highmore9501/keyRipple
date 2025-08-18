from piano.keyNote import KeyNote


class Piano():
    """
    钢琴类，初始参数包含钢琴最小键值和最大键值
    """

    def __init__(self, min_key: int = 21, max_key: int = 108):
        self.min_key = min_key
        self.max_key = max_key
        self.black_keys = {1, 3, 6, 8, 10}

    def note_to_key(self, note: int) -> KeyNote:
        """
        将 MIDI 音符转换为钢琴键盘上的键位置
        :param note: MIDI 音符编号 (0-127)
        :return: 钢琴键盘上的键位置 (相对于钢琴最小键的位置)
        """
        # 检查音符是否在钢琴范围内
        if note < self.min_key or note > self.max_key:
            raise ValueError(
                f"音高 {note} 超出了钢琴音域 ({self.min_key}-{self.max_key})")

        # 计算位置
        position = note - self.min_key

        # 判断是否为黑键 (基于 MIDI 音符编号的模 12 余数)
        # 黑键: 1, 3, 6, 8, 10 (对应升号音符)
        is_black = (note % 12) in self.black_keys

        return KeyNote(note=note, position=position, is_black=is_black)

    def position_to_key_note(self, position: int) -> KeyNote:
        """
        通过位置计算键位
        """
        note = self.min_key + position
        is_black = (note % 12) in self.black_keys
        return KeyNote(note, position, is_black)
