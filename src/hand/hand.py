from src.piano.piano import Piano
from src.hand.finger import Finger


class Hand:
    def __init__(self, fingers: list[Finger], piano: Piano, is_left: bool, max_distance: int = 13, finger_number: int = 5):
        self.fingers: list[Finger] = fingers
        self.piano: Piano = piano
        self.is_left: bool = is_left
        self.max_distance: int = max_distance
        self.finger_number: int = finger_number
        self.hand_position: float = 0.0
        if len(fingers) < self.finger_number:
            self._gernate_empty_fingers()
        self._calculate_hand_position()

    def _gernate_empty_fingers(self):
        """
        生成空的手指，确保手指数量为finger_number
        """
        finger_indexs = [finger_index for finger_index in range(self.finger_number)] if self.is_left else [
            finger_index for finger_index in range(self.finger_number, 2*self.finger_number)]

        used_finger_indexs = [finger.finger_index for finger in self.fingers]
        leftest_finger_position = self.fingers[0].key_note.position
        leftest_finger_index = self.fingers[0].finger_index
        latest_finger_position = 0
        latest_finger_index = finger_indexs[0]
        is_beyond_leftest_finger = False
        need_new_finger = False

        for i in range(self.finger_number):
            current_finger_index = finger_indexs[i]
            # 如果当前手指已经使用过了，那么就跳过，只更新latest_finger_index和latest_finger_position
            if current_finger_index in used_finger_indexs:
                latest_finger_position = next(
                    (finger.key_note.position for finger in self.fingers if finger.finger_index == latest_finger_index), 0)

                latest_finger_index = current_finger_index
                need_new_finger = False
            # 如果当前手指比最左的手指还小，那么就计算并且生成一个新的休息手指
            elif current_finger_index < leftest_finger_index:
                latest_finger_position = leftest_finger_position - \
                    2*(latest_finger_index-current_finger_index)
                need_new_finger = True
            elif not is_beyond_leftest_finger:
                # 第一次超越最左手指
                is_beyond_leftest_finger = True
                latest_finger_index = current_finger_index
                latest_finger_position = leftest_finger_position + \
                    2*(current_finger_index-leftest_finger_index)
                need_new_finger = True
            else:
                latest_finger_index = current_finger_index
                latest_finger_position = latest_finger_position + \
                    2*(current_finger_index-latest_finger_index)
                need_new_finger = True

            if need_new_finger:
                self.fingers.append(
                    Finger(current_finger_index, self.piano.position_to_key_note(latest_finger_position), self.is_left, False))

    def calculate_hand_diff(self, next_hand: 'Hand') -> int:
        # 因为运行到这里，默认next_hand已经有相同数量的fingers，所以只需要遍历fingers，然后求diff
        total_diff = 0
        for i in range(self.finger_number):
            current_finger = self.fingers[i]
            next_finger = next_hand.fingers[i]
            diff = abs(current_finger.key_note.position -
                       next_finger.key_note.position)
            total_diff += diff

        return total_diff

    def _calculate_hand_position(self):
        positions = [finger.key_note.position for finger in self.fingers]
        avarage_position = sum(positions) / len(positions)
        self.hand_position = avarage_position

    def export_hand_info(self) -> dict:
        return {
            'hand_position': self.hand_position,
            'fingers': [finger.export_finger_info() for finger in self.fingers],
            'is_left': self.is_left
        }
