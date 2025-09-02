from src.hand.hand import Hand
from src.hand.finger import Finger
from src.midi.midiToNotes import NotesMap
from src.piano.piano import Piano
from typing import Iterator, Optional
import itertools
import json


class Recorder:
    def __init__(self, piano: Piano, left_hands: list[Hand] = [], right_hands: list[Hand] = [], current_entropy: float = 0.0, frame: float = 0.0, left_frames: list[float] = [], right_frames: list[float] = []):
        self.piano: Piano = piano
        self.left_hands: list[Hand] = left_hands
        self.left_frames: list[float] = left_frames
        self.right_hands: list[Hand] = right_hands
        self.right_frames: list[float] = right_frames
        self.current_entropy: float = current_entropy
        self.frame = frame

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
        left_hand_diff = 0.0
        right_hand_diff = 0.0

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

        # 到这一步时，不适合的指法已经被淘汰，需要用当前指法生成新的左右手并且计算它们的熵
        left_fingers: list[Finger] = []
        for note, finger_index in left_hand_notes:
            key_note = self.piano.note_to_key(note)
            left_fingers.append(Finger(finger_index, key_note, True, True))

        lasted_left_hand = self.left_hands[-1]
        new_left_hands: list[Hand] = self.left_hands[:]
        new_left_frames = self.left_frames[:]

        if left_fingers:
            new_left_hand = lasted_left_hand.generate_next_hand(
                left_fingers, finger_range, finger_distribution)
            left_hand_diff = lasted_left_hand.calculate_hand_diff(
                new_left_hand)
            # 生成新的左手序列

            new_left_hands.append(new_left_hand)

            new_left_frames.append(frame)

        right_fingers: list[Finger] = []
        for note, finger_index in right_hand_notes:
            key_note = self.piano.note_to_key(note)
            right_fingers.append(Finger(finger_index, key_note, False, True))

        lasted_right_hand = self.right_hands[-1]
        new_right_frames = self.right_frames[:]

        new_right_hands: list[Hand] = self.right_hands[:]
        if right_fingers:
            new_right_hand = lasted_right_hand.generate_next_hand(
                right_fingers, finger_range, finger_distribution)
            right_hand_diff = lasted_right_hand.calculate_hand_diff(
                new_right_hand)
            # 生成新的右手序列
            new_right_hands.append(new_right_hand)
            new_right_frames.append(frame)

        new_entropy = self.current_entropy + \
            left_hand_diff + right_hand_diff

        new_recorder = Recorder(
            self.piano, new_left_hands, new_right_hands, new_entropy, frame, new_left_frames, new_right_frames)

        return new_recorder

    def export_recorders(self, file_path: str):
        if len(self.left_hands) != len(self.left_frames) or len(self.right_hands) != len(self.right_frames):
            print(
                f'Error: 左手一共{len(self.left_hands)}个，左手frames一共{len(self.left_frames)}个，右手一共{len(self.right_hands)}个，右手frames一共{len(self.right_frames)}个')
            raise Exception('数量不一致')

        result = []
        left_hands_info = [hand.export_hand_info()
                           for hand in self.left_hands]  # type: ignore
        right_hands_info = [hand.export_hand_info()
                            for hand in self.right_hands]

        left_hand_data = []
        right_hand_data = []

        for i in range(len(self.left_hands)):
            left_hand_data.append({
                'left_hand': left_hands_info[i],
                'frame': self.left_frames[i]
            })

        for j in range(len(self.right_hands)):
            right_hand_data.append({
                'right_hand': right_hands_info[j],
                'frame': self.right_frames[j]
            })

        left_hand_data, right_hand_data = self.detect_and_resolve_hand_conflicts(
            left_hand_data, right_hand_data)

        result = left_hand_data + right_hand_data

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=4)

    def detect_and_resolve_hand_conflicts(self, left_hand_data, right_hand_data):
        """
        检测并解决左右手之间的按键冲突

        Args:
            left_hand_data: 左手数据
            right_hand_data：右手数据

        Returns:
            返回处理后的左右手数据
        """

        # 定义默认手部状态
        default_left_hand = {
            "hand_note": self.piano.middle_left,
            "fingers": [
                {
                    "finger_index": 0,
                    "key_note": {"note": 48, "position": 27, "is_black": False},
                    "is_left": True,
                    "pressed": False,
                    "is_keep_pressed": False
                },
                {
                    "finger_index": 1,
                    "key_note": {"note": 50, "position": 29, "is_black": False},
                    "is_left": True,
                    "pressed": False,
                    "is_keep_pressed": False
                },
                {
                    "finger_index": 2,
                    "key_note": {"note": 52, "position": 31, "is_black": False},
                    "is_left": True,
                    "pressed": False,
                    "is_keep_pressed": False
                },
                {
                    "finger_index": 3,
                    "key_note": {"note": 53, "position": 32, "is_black": False},
                    "is_left": True,
                    "pressed": False,
                    "is_keep_pressed": False
                },
                {
                    "finger_index": 4,
                    "key_note": {"note": 55, "position": 34, "is_black": False},
                    "is_left": True,
                    "pressed": False,
                    "is_keep_pressed": False
                }
            ],
            "is_left": True,
            "hand_span": 8
        }

        default_right_hand = {
            "hand_note": self.piano.middle_right,
            "fingers": [
                {
                    "finger_index": 5,
                    "key_note": {"note": 72, "position": 51, "is_black": False},
                    "is_left": False,
                    "pressed": False,
                    "is_keep_pressed": False
                },
                {
                    "finger_index": 6,
                    "key_note": {"note": 74, "position": 53, "is_black": False},
                    "is_left": False,
                    "pressed": False,
                    "is_keep_pressed": False
                },
                {
                    "finger_index": 7,
                    "key_note": {"note": 76, "position": 55, "is_black": False},
                    "is_left": False,
                    "pressed": False,
                    "is_keep_pressed": False
                },
                {
                    "finger_index": 8,
                    "key_note": {"note": 77, "position": 56, "is_black": False},
                    "is_left": False,
                    "pressed": False,
                    "is_keep_pressed": False
                },
                {
                    "finger_index": 9,
                    "key_note": {"note": 79, "position": 58, "is_black": False},
                    "is_left": False,
                    "pressed": False,
                    "is_keep_pressed": False
                }
            ],
            "is_left": False,
            "hand_span": 8
        }

        # 处理报告
        report = {
            "left_hand_frames": len(left_hand_data),
            "right_hand_frames": len(right_hand_data),
            "conflicts_found": 0,
            "conflicts_resolved": 0
        }

        # 遍历左手数据，检测冲突
        for i in range(len(left_hand_data) - 1):
            left_current = left_hand_data[i]
            left_next = left_hand_data[i + 1]

            # 获取当前左手小指的note值
            left_pinky_note = left_current["left_hand"]["fingers"][4]["key_note"]["note"]

            # 确定时间区间
            frame_start = left_current["frame"]
            frame_end = left_next["frame"]

            # 在该时间区间内检查右手数据
            for right_item in right_hand_data:
                if frame_start <= right_item["frame"] <= frame_end:
                    # 检查右手拇指的note值
                    right_thumb_note = right_item.get("right_hand", {}).get(
                        "fingers", [{}]*5)[0]["key_note"]["note"]

                    # 检查是否有冲突（右手拇指note小于左手小指note）
                    if right_thumb_note < left_pinky_note:
                        report["conflicts_found"] += 1

                        # 添加默认左手状态到处理后的数据中
                        default_state = {
                            "left_hand": default_left_hand,
                            "frame": right_item["frame"]
                        }
                        left_hand_data.append(default_state)
                        report["conflicts_resolved"] += 1

        # 遍历右手数据，检测冲突
        for i in range(len(right_hand_data) - 1):
            right_current = right_hand_data[i]
            right_next = right_hand_data[i + 1]

            # 获取当前右手拇指的note值
            right_thumb_note = right_current.get("right_hand", {}).get(
                "fingers", [{}]*5)[0]["key_note"]["note"]

            # 确定时间区间
            frame_start = right_current["frame"]
            frame_end = right_next["frame"]

            # 在该时间区间内检查左手数据
            for left_item in left_hand_data:
                if frame_start <= left_item["frame"] <= frame_end:
                    # 检查左手小指的note值
                    left_pinky_note = left_item["left_hand"]["fingers"][4]["key_note"]["note"]

                    # 检查是否有冲突（右手拇指note小于左手小指note）
                    if right_thumb_note < left_pinky_note:
                        report["conflicts_found"] += 1

                        # 添加默认右手状态到处理后的数据中
                        default_state = {
                            "right_hand": default_right_hand,
                            "frame": left_item["frame"]
                        }
                        right_hand_data.append(default_state)
                        report["conflicts_resolved"] += 1

        left_hand_data = sorted(left_hand_data, key=lambda x: x["frame"])
        right_hand_data = sorted(right_hand_data, key=lambda x: x["frame"])
        print(report)

        return left_hand_data, right_hand_data
