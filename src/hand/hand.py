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
            # 更新位置
            existing_fingers[finger_index] = estimated_pos
            return estimated_pos

        # 如果只有右侧邻居
        elif right_neighbor is not None:
            right_pos = existing_fingers[right_neighbor]
            right_distance = right_neighbor - finger_index
            estimated_pos = right_pos - \
                self._calculate_expected_distance(right_pos, right_distance)
            # 更新位置
            existing_fingers[finger_index] = estimated_pos
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
        over_right = self.is_left and next_hand.hand_note > 52
        if over_right:
            over_value = next_hand.hand_note - 52
            total_diff += 5 * over_value

        over_left = not self.is_left and next_hand.hand_note < 76
        if over_left:
            over_value = 76 - next_hand.hand_note
            total_diff += 5 * over_value

        # 计算每个手指的diff
        for i in range(self.finger_number):
            current_finger = self.fingers[i]
            next_finger = next_hand.fingers[i]
            diff = 0
            if next_finger.pressed:
                diff = abs(current_finger.key_note.note -
                           next_finger.key_note.note)
                total_diff += diff
            # 如果两个手指都是按下的，那么diff翻倍，因为不推荐同一个手指反复使用,可能的话最好是相邻的两个手指轮流使用
            if current_finger.pressed and next_finger.pressed:
                total_diff += (2 * diff + 2)

        return total_diff

    def _calculate_hand_note(self):
        # 检测当前手指数量是否满足要求
        if len(self.fingers) != self.finger_number:
            raise ValueError("当前手指数量不满足要求")
        notes = [finger.key_note.note for finger in self.fingers]
        # 计算当前手指跨度
        self.hand_span = max(notes) - min(notes)

        # 下面的代码是一个保护机制，如果前面运行的代码正常，这里不应该抛出异常
        if self.hand_span > self.max_distance:
            for finger in self.fingers:
                print(
                    f"finger_index: {finger.finger_index}, note: {finger.key_note.note},pressed: {finger.pressed}")
            raise ValueError(
                f"当前手指跨度超过最大距离{self.max_distance}，为{self.hand_span}")
        # 之所以这样确认手掌位置是因为，经常按不到键的是大拇指和小拇指，所以要由它们来决定手掌位置
        self.hand_note = (max(notes) + min(notes))/2

    def export_hand_info(self) -> dict:
        return {
            'hand_note': self.hand_note,
            'fingers': [finger.export_finger_info() for finger in self.fingers],
            'is_left': self.is_left,
            'hand_span': self.hand_span
        }

    def generate_next_hand(self, next_fingers: list['Finger'], finger_range: float, finger_distribution: list[int]) -> 'Hand':
        """
        这个方法主要是用于判断哪些当前手指可以保留，然后把可以保留的手指添加到next_fingers里传递到下一个Hand对象中。至于其它的手指，则是由下一个Hand对象自己来生成。
        """
        next_notes = [finger.key_note.note for finger in next_fingers]
        next_finger_indices = [finger.finger_index for finger in next_fingers]
        min_next_finger = next_fingers[0]
        max_next_finger = next_fingers[-1]
        # 先遍历当前手指，找出可以保留的手指
        for old_finger in self.fingers:
            # 当前没有按键的手指可以不用管
            if not old_finger.pressed:
                continue

            old_finger_index = old_finger.finger_index
            # 如果当前手指在next_fingers中，则跳过，因为可以直接使用下一个手指的状态
            if old_finger_index in next_finger_indices:
                continue

            old_finger_note = old_finger.key_note.note
            # 如果当前手指占了下一个手指的按键，则跳过
            if old_finger_note in next_notes:
                continue

            # 检查是否会与下一个状态的手指存在错序
            has_conflict = False
            for next_finger in next_fingers:
                next_finger_index = next_finger.finger_index
                next_note = next_finger.key_note.note
                # 如果当前手指和下一个状态的手指存在错序，标记为有冲突
                if (old_finger_index > next_finger_index and old_finger_note < next_note) or \
                        (old_finger_index < next_finger_index and old_finger_note > next_note):
                    has_conflict = True
                    break

            # 如果存在错序冲突，则跳过当前手指
            if has_conflict:
                continue

            # 如果当前手指和下一个状态的手指之间的距离超过最大距离，则跳过
            if old_finger._is_next_finger_too_far(min_next_finger, finger_range, finger_distribution):
                continue

            if old_finger._is_next_finger_too_far(max_next_finger, finger_range, finger_distribution):
                continue

            # 最终符合要求的手指可以得到保留
            keep_finger = Finger(old_finger_index, old_finger.key_note, self.is_left,
                                 True, True)
            next_fingers.append(keep_finger)

        # 用新的手指组合生成下一个Hand对象
        next_hand = Hand(next_fingers, self.piano, self.is_left,
                         self.max_distance, self.finger_number)

        return next_hand
