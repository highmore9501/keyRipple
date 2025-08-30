from src.piano.piano import Piano
from src.hand.finger import Finger


class Hand:
    def __init__(self, fingers: list[Finger], piano: Piano, is_left: bool, max_distance: int = 13, finger_number: int = 5):
        self.fingers: list[Finger] = fingers
        self.piano: Piano = piano
        self.is_left: bool = is_left
        self.middle_position: int = 52 if is_left else 76
        self.max_distance: int = max_distance
        self.finger_number: int = finger_number
        self.hand_note: float = 0.0
        if len(fingers) < self.finger_number:
            self._generate_empty_fingers()
        self._calculate_hand_note()

    def _generate_empty_fingers(self):
        """
        生成空的手指，确保手指数量为finger_number
        根据已有的手指位置推断缺失手指的合理位置
        """
        # 确定手指索引范围
        finger_indices = list(range(self.finger_number)) if self.is_left else \
            list(range(self.finger_number, 2 * self.finger_number))

        # 获取已存在的手指索引和位置
        existing_fingers = {finger.finger_index: finger.key_note.position
                            for finger in self.fingers}

        # 找出缺失的手指索引
        missing_indices = [
            idx for idx in finger_indices if idx not in existing_fingers]

        # 如果没有缺失的手指，直接返回
        if not missing_indices:
            return

        # 如果没有任何手指存在，使用默认位置，其实一般不会运行到这里
        if not existing_fingers:
            # 左手从位置52+21开始，右手从位置76+21开始
            base_position = 73 if self.is_left else 93
            for i, finger_index in enumerate(finger_indices):
                position = base_position + (i - 2) * 2  # 大致按五指分布
                self.fingers.append(
                    Finger(finger_index,
                           self.piano.position_to_key_note(position),
                           self.is_left,
                           False))
            return

        # 根据现有手指推断缺失手指的位置
        for missing_index in missing_indices:
            # 计算相邻手指的位置来推断缺失手指位置
            position = self._estimate_finger_position(
                missing_index, existing_fingers)
            self.fingers.append(
                Finger(missing_index,
                       self.piano.position_to_key_note(position),
                       self.is_left,
                       False))

        # 按手指索引排序
        self.fingers.sort(key=lambda f: f.finger_index)

    def _estimate_finger_position(self, finger_index: int, existing_fingers: dict[int, int]) -> int:
        """
        根据相邻手指位置估算指定手指的位置
        考虑到E-F和B-C之间只相隔1个半音，需要特殊处理
        """
        # 获取所有存在的手指索引并排序
        existing_indices = sorted(existing_fingers.keys())

        # 找到相邻的手指
        left_neighbor = None
        right_neighbor = None

        for idx in existing_indices:
            if idx < finger_index:
                left_neighbor = idx
            elif idx > finger_index and right_neighbor is None:
                right_neighbor = idx
                break

        # 如果有左侧邻居
        if left_neighbor is not None:
            left_pos = existing_fingers[left_neighbor]

            if right_neighbor is not None:
                # 两侧都有邻居，在中间位置附近估算
                right_pos = existing_fingers[right_neighbor]
                # 计算加权位置
                estimated_pos = int((right_pos + left_pos)/2)
            else:
                # 只有左侧邻居，根据手指索引差值估算位置
                left_distance = finger_index - left_neighbor
                estimated_pos = left_pos + \
                    self._calculate_expected_distance(left_pos, left_distance)
            return estimated_pos

        # 如果只有右侧邻居
        elif right_neighbor is not None:
            right_pos = existing_fingers[right_neighbor]
            right_distance = right_neighbor - finger_index
            estimated_pos = right_pos - \
                self._calculate_expected_distance(right_pos, right_distance)
            return estimated_pos

        # 如果没有邻居（理论上不应该发生），使用默认位置
        return 52 if self.is_left else 76

    def _calculate_expected_distance(self, base_position: int, finger_distance: int) -> int:
        """
        根据基础位置和手指距离计算期望的距离
        考虑E-F和B-C之间只相隔1个半音的特殊情况
        """
        expected_distance = 0
        current_note = self.piano.min_key + base_position

        for i in range(finger_distance):
            # 检查当前音符是否是E或B（这些音符到下一个音符只有1个半音）
            note_mod = current_note % 12
            if note_mod == 4 or note_mod == 11:  # E(4)或B(11)
                expected_distance += 1  # 只移动1个半音
            else:
                expected_distance += 2  # 通常移动2个半音
            current_note += 2  # 近似增加

        return expected_distance

    def calculate_hand_diff(self, next_hand: 'Hand') -> float:
        total_diff = 0

        # 如果手跨过了它的舒适区，左手去弹右边的，或者相反，那么diff乘10
        # 这里的舒适区参数是写死了的，其实应该从avatar_info中获取
        punishment_multiplicer = 1
        over_right = self.is_left and next_hand.hand_note > 52
        if over_right:
            punishment_multiplicer += 0.1 * (next_hand.hand_note - 52)

        over_left = not self.is_left and next_hand.hand_note < 76
        if over_left:
            punishment_multiplicer += 0.1 * (76 - next_hand.hand_note)

        # 计算每个手指的diff
        for i in range(self.finger_number):
            current_finger = self.fingers[i]
            next_finger = next_hand.fingers[i]
            diff = abs(current_finger.key_note.note -
                       next_finger.key_note.note)
            total_diff += diff
            # 如果两个手指都是按下的，那么diff翻倍，因为不推荐同一个手指反复使用
            if current_finger.pressed and next_finger.pressed:
                total_diff += (2 * diff + 4)

        return total_diff * punishment_multiplicer

    def _calculate_hand_note(self):
        # 检测当前手指数量是否满足要求
        if len(self.fingers) != self.finger_number:
            raise ValueError("当前手指数量不满足要求")
        notes = [finger.key_note.note for finger in self.fingers]
        # 计算当前手指跨度
        self.hand_span = max(notes) - min(notes)
        if self.hand_span > 12:
            for finger in self.fingers:
                print(
                    f"finger_index: {finger.finger_index}, note: {finger.key_note.note},pressed: {finger.pressed}")
            raise ValueError("当前手指跨度超过12")
        # 检测一下hand_note和中指的finger_index差距有多大
        middle_finger_index = 2 if self.is_left else 7
        middle_finger = next(
            finger for finger in self.fingers if finger.finger_index == middle_finger_index)
        self.hand_note = middle_finger.key_note.note

    def export_hand_info(self) -> dict:
        return {
            'hand_note': self.hand_note,
            'fingers': [finger.export_finger_info() for finger in self.fingers],
            'is_left': self.is_left,
            'hand_span': self.hand_span
        }
