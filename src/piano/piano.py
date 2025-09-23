from src.piano.keyNote import KeyNote


class Piano():
    """
    钢琴类，初始参数包含钢琴最小键值和最大键值
    """

    def __init__(self, min_key: int = 21, max_key: int = 108, middle_left: int = 52, middle_right: int = 76):
        self.min_key = min_key
        self.max_key = max_key
        self.middle_left = middle_left
        self.middle_right = middle_right
        self.black_keys = {1, 3, 6, 8, 10}
        self.white_keys = []
        self.numberOfWhiteKeys = self.caculate_number_of_white_keys()

    def note_to_key(self, note: int) -> KeyNote:
        """
        将 MIDI 音符转换为钢琴键盘上的键位置
        :param note: MIDI 音符编号 (0-127)
        :return: 钢琴键盘上的键位置 (相对于钢琴最小键的位置)
        """
        # 检查音符是否在钢琴范围内
        if note < self.min_key:
            print(f"音高 {note} 小于钢琴最小键值 {self.min_key}")
            note = self.min_key

        if note > self.max_key:
            print(f"音高 {note} 大于钢琴最大键值 {self.max_key}")
            note = self.max_key

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

    def caculate_number_of_white_keys(self) -> int:
        """
        通过键位计算位置
        """
        amount = 0
        for note in range(self.min_key, self.max_key + 1):
            is_black = (note % 12) in self.black_keys
            if not is_black:
                amount += 1
                self.white_keys.append(note)
        return amount
