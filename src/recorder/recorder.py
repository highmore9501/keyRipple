from src.hand.hand import Hand
from src.hand.finger import Finger
from src.midi.midiToNotes import NotesMap
from src.piano.piano import Piano
from typing import Iterator, Optional
import itertools
import json


class Recorder:
    def __init__(self, piano: Piano, left_hands: list[Hand], right_hands: list[Hand], current_entropy: float, frame: float, frames: list[float]):
        self.piano: Piano = piano
        self.left_hands: list[Hand] = left_hands
        self.right_hands: list[Hand] = right_hands
        self.current_entropy: float = current_entropy
        self.frame = frame
        self.frames: list[float] = frames
        self.frames.append(frame)

    def next_generation_recorders_generator(self, notes_map: NotesMap, hand_range: int, finger_range: float, finger_distribution: list[int]) -> Iterator['Recorder']:
        notes = notes_map['notes']
        frame = notes_map['frame']
        note_amount = len(notes)
        finger_indices = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

        # 生成所有可能的组合
        # 从10个手指中选择len(notes)个手指来按这些音符，且手指按顺序排列
        for finger_combination in itertools.combinations(finger_indices, note_amount):
            # 直接将有序的音符与有序的手指组合配对
            note_finger_mapping = dict(zip(notes, finger_combination))

            # 根据映射创建新的Recorder实例
            new_recorder = self._create_new_recorder(
                note_finger_mapping, hand_range, finger_range, finger_distribution, frame)
            if new_recorder is not None:
                yield new_recorder

    def _create_new_recorder(self, note_finger_mapping: dict[int, int], hand_range: int, finger_range: float, finger_distribution: list[int], frame: float) -> Optional['Recorder']:
        # 存储左手的音符 [(note, finger_index), ...]
        left_hand_notes: list[tuple[int, int]] = []
        # 存储右手的音符 [(note, finger_index), ...]
        right_hand_notes: list[tuple[int, int]] = []

        # 初始化左右手的统计变量
        left_lowest_note = None
        left_highest_note = None
        right_lowest_note = None
        right_highest_note = None

        # 分离左右手的音符
        for note, finger_index in note_finger_mapping.items():
            if finger_index < 5:
                # 左手处理
                left_hand_notes.append((note, finger_index))

                # 更新左手音域范围
                if left_lowest_note is None:
                    left_lowest_note = note
                    left_highest_note = note
                else:
                    # 由于音符已经有序，只需要更新最高音符
                    if not left_highest_note or note > left_highest_note:
                        left_highest_note = note

                # 检查音域跨度
                if left_highest_note - left_lowest_note > hand_range:
                    return None

            else:
                # 右手处理
                right_hand_notes.append((note, finger_index))

                # 更新右手音域范围
                if right_lowest_note is None:
                    right_lowest_note = note
                    right_highest_note = note
                else:
                    # 由于音符已经有序，只需要更新最高音符
                    if not right_highest_note or note > right_highest_note:
                        right_highest_note = note

                # 检查音域跨度
                if right_highest_note - right_lowest_note > hand_range:
                    return None

        # 检查手指跨度限制（仅在有多个音符时检查）
        if len(left_hand_notes) > 1:
            for i in range(1, len(left_hand_notes)):
                note, finger_index = left_hand_notes[i]
                prev_note, prev_finger_index = left_hand_notes[i-1]
                note_diff = note - prev_note
                finger_diff = abs(
                    finger_distribution[finger_index] - finger_distribution[prev_finger_index])
                if note_diff > finger_range * finger_diff:
                    return None

        if len(right_hand_notes) > 1:
            for i in range(1, len(right_hand_notes)):
                note, finger_index = right_hand_notes[i]
                prev_note, prev_finger_index = right_hand_notes[i-1]
                note_diff = note - prev_note
                finger_diff = abs(
                    finger_distribution[finger_index-5] - finger_distribution[prev_finger_index-5])
                if note_diff > finger_range * finger_diff:
                    return None

        # 生成新的左右手并且计算它们的熵
        left_fingers: list[Finger] = []
        for note, finger_index in left_hand_notes:
            key_note = self.piano.note_to_key(note)
            left_fingers.append(Finger(finger_index, key_note, True, True))

        lasted_left_hand = self.left_hands[-1]
        # 如果左手没有需要按的音符，那么保持上一手型
        if len(left_fingers) == 0:
            left_fingers = lasted_left_hand.fingers[:]

        new_left_hand = Hand(left_fingers, self.piano, True,
                             lasted_left_hand.max_distance, lasted_left_hand.finger_number)
        left_hand_diff = lasted_left_hand.calculate_hand_diff(new_left_hand)

        right_fingers: list[Finger] = []
        for note, finger_index in right_hand_notes:
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
        new_frames = self.frames[:]
        new_recorder = Recorder(
            self.piano, new_left_hands, new_right_hands, new_entropy, frame, new_frames)

        return new_recorder

    def export_recorders(self, file_path: str):
        if len(self.left_hands) != len(self.right_hands) or len(self.left_hands) != len(self.frames):
            print(
                f'Error: 左手一共{len(self.left_hands)}个，右手一共{len(self.right_hands)}个，frames一共{len(self.frames)}个')
            raise Exception('数量不一致')

        result = []
        left_hands_info = [hand.export_hand_info()
                           for hand in self.left_hands]  # type: ignore
        right_hands_info = [hand.export_hand_info()
                            for hand in self.right_hands]

        for i in range(len(self.frames)):
            result.append({
                'left_hand': left_hands_info[i],
                'right_hand': right_hands_info[i],
                'frame': self.frames[i]
            })

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=4)
