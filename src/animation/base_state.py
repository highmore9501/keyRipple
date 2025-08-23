from enum import Enum
from typing import Dict, Any, TypedDict, Optional


class HandType(Enum):
    LEFT = 'L'
    RIGHT = 'R'


class KeyType(Enum):
    WHITE = 'white'
    BLACK = 'black'


class BaseState:
    """
    表示一个基准手型
    param left_hand_note: 左手位置
    param right_hand_note: 右手位置    
    param key_type: 当前按的是黑键还是白键
    param finger_number: 一共有多少个手指，当然默认情况下是5个手指
    """

    def __init__(self, left_hand_note: int, right_hand_note: int, key_type: KeyType, finger_number: int = 5) -> None:
        self.left_hand_note = left_hand_note
        self.right_hand_note = right_hand_note
        self.key_type = key_type
        self.finger_number = finger_number
        self.body_position = (left_hand_note + right_hand_note)/2

        self.left_finger_indices = [finger_index for finger_index in range(
            self.finger_number)]
        self.right_finger_indices = [finger_index for finger_index in range(
            self.finger_number, 2*self.finger_number)]

        finger_positions = {}

        for finger_index in self.left_finger_indices:
            finger_positions[finger_index] = f'P{left_hand_note}_finger{finger_index}_{key_type.value}'

        for finger_index in self.right_finger_indices:
            finger_positions[finger_index] = f'P{right_hand_note}_finger{finger_index}_{key_type.value}'

        self.position_balls = {
            "finger_positions": {
                "names": finger_positions,
                "collection": f"finger_position_balls"}
        }

        self.hand_target = {
            "left_hand_target": {
                "name": f'P{left_hand_note}_H_tar_{key_type.value}_L',
                "collection": "hand_targets"
            },
            "right_hand_target": {
                "name": f'P{right_hand_note}_H_tar_{key_type.value}_R',
                "collection": "hand_targets"
            }
        }


class NormalBaseState(Enum):
    RIGHT_WHITE = BaseState(24, 52, KeyType.WHITE, 5)
    MIDDLE_BLACK = BaseState(52, 76, KeyType.BLACK, 5)
    LEFT_WHITE = BaseState(76, 105, KeyType.WHITE, 5)
