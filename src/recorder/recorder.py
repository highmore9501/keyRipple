from src.hand.hand import Hand
from src.hand.finger import Finger
from src.midi.midiToNotes import NotesMap
from src.piano.piano import Piano
from typing import Iterator, Optional
import itertools
import json


class Recorder:
    def __init__(self, piano: Piano, left_hands: list[Hand], right_hands: list[Hand], current_entropy: int, real_tick: float, real_ticks: list[float]):
        self.piano: Piano = piano
        self.left_hands: list[Hand] = left_hands
        self.right_hands: list[Hand] = right_hands
        self.current_entropy: int = current_entropy
        self.real_tick = real_tick
        self.real_ticks: list[float] = real_ticks[:]
        self.real_ticks.append(real_tick)

    def next_generation_recorders_generator(self, notes_map: NotesMap, hand_range: int, finger_range: int) -> Iterator['Recorder']:
        notes = notes_map['notes']
        real_tick = notes_map['real_tick']
        note_amount = len(notes)
        finger_indexs = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

        # 生成所有可能的组合
        # 从10个手指中选择len(notes)个手指来按这些音符
        for finger_combination in itertools.combinations(finger_indexs, note_amount):
            # 生成手指与音符的所有可能分配方式
            for finger_permutation in itertools.permutations(finger_combination):
                # 为每个音符分配一个手指
                note_finger_mapping = dict(zip(notes, finger_permutation))

                # 根据映射创建新的Recorder实例
                new_recorder = self._create_new_recorder(
                    note_finger_mapping, note_amount, hand_range, finger_range, real_tick)
                if new_recorder is not None:
                    yield new_recorder

    def _create_new_recorder(self, note_finger_mapping: dict[int, int], note_amount: int, hand_range: int, finger_range: int, real_tick: float) -> Optional['Recorder']:
        # 按手指索引排序
        sorted_items = sorted(note_finger_mapping.items(),
                              key=lambda x: x[1])

        left_hand_notes_amount = 0
        lasted_note = 0
        lasted_finger_index = 0
        left_hand_lowest_note = 0
        left_hand_highest_note = 0
        current_is_left = True
        right_hand_lowest_note = 0
        right_hand_highest_note = 0

        for i, (note, finger_index) in enumerate(sorted_items):
            # 排序靠后的手指按的音符比前面的还低，判定无效
            if note < lasted_note:
                return None

            if i == 0:
                left_hand_lowest_note = note
                lasted_note = note

            if i == len(sorted_items) - 1:
                right_hand_highest_note = note

            # 检查音符间隔是否过大（除了左手到右手的第一次过渡）
            is_transition_from_left_to_right = current_is_left and finger_index >= 5
            if not is_transition_from_left_to_right:
                note_span_too_wide = note - lasted_note > finger_range * \
                    (finger_index - lasted_finger_index)
                if note_span_too_wide:
                    return None

            if finger_index < 5:
                left_hand_notes_amount += 1
                # 左手按音超过5个，判定无效
                if left_hand_notes_amount > 5:
                    return None
                lasted_note = note
                left_hand_highest_note = note
                lasted_finger_index = finger_index
            else:
                if current_is_left:
                    if note_amount - left_hand_notes_amount > 5:
                        return None
                    current_is_left = False
                    right_hand_lowest_note = note
                lasted_note = note

        # 左右手任何一只跨度超过hand_range，判定无效
        if left_hand_highest_note - left_hand_lowest_note > hand_range:
            return None

        if right_hand_highest_note - right_hand_lowest_note > hand_range:
            return None

        # 生成新的左右手并且计算它们的熵
        left_hand_items = list(filter(lambda item: item[1] < 5, sorted_items))
        left_fingers: list[Finger] = []
        for note, finger_index in left_hand_items:
            key_note = self.piano.note_to_key(note)
            left_fingers.append(Finger(finger_index, key_note, True, True))

        lasted_left_hand = self.left_hands[-1]
        # 如果左手没有需要按的音符，那么保持上一手型
        if len(left_fingers) == 0:
            left_fingers = lasted_left_hand.fingers[:]
        new_left_hand = Hand(left_fingers, self.piano, True,
                             lasted_left_hand.max_distance, lasted_left_hand.finger_number)
        left_hand_diff = lasted_left_hand.calculate_hand_diff(new_left_hand)

        right_hand_items = list(
            filter(lambda item: item[1] >= 5, sorted_items))
        right_fingers: list[Finger] = []
        for note, finger_index in right_hand_items:
            key_note = self.piano.note_to_key(note)
            right_fingers.append(Finger(finger_index, key_note, False, True))
        lasted_right_hand = self.right_hands[-1]

        # 如果右手没有需要按的音符，那么保持上一手型
        if len(right_fingers) == 0:
            right_fingers = lasted_right_hand.fingers[:]

        new_right_hand = Hand(right_fingers, self.piano, False,
                              lasted_right_hand.max_distance, lasted_right_hand.finger_number)
        right_hand_diff = lasted_right_hand.calculate_hand_diff(
            new_right_hand)

        # 生成新的recorder
        new_left_hands: list[Hand] = self.left_hands[:]
        new_left_hands.append(new_left_hand)

        new_right_hands: list[Hand] = self.right_hands[:]
        new_right_hands.append(new_right_hand)

        new_entropy = self.current_entropy + \
            left_hand_diff + right_hand_diff
        new_recorder = Recorder(
            self.piano, new_left_hands, new_right_hands, new_entropy, real_tick, self.real_ticks)

        return new_recorder

    def export_recorders(self, file_path: str):
        if len(self.left_hands) != len(self.right_hands) or len(self.left_hands) != len(self.real_ticks):
            print(
                f'Error: 左手一共{len(self.left_hands)}个，右手一共{len(self.right_hands)}个，real_ticks一共{len(self.real_ticks)}个')
            raise Exception('数量不一致')

        result = []
        left_hands_info = [hand.export_hand_info() for hand in self.left_hands]
        right_hands_info = [hand.export_hand_info()
                            for hand in self.right_hands]

        for i in range(len(self.real_ticks)):
            result.append({
                'left_hand': left_hands_info[i],
                'right_hand': right_hands_info[i],
                'real_tick': self.real_ticks[i]
            })

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=4)
