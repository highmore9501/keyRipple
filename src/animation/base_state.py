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
    param left_hand_position: 左手位置
    param right_hand_position: 右手位置    
    param key_type: 当前按的是黑键还是白键
    param finger_number: 一共有多少个手指，当然默认情况下是5个手指
    """

    def __init__(self, left_hand_position: int, right_hand_position: int, key_type: KeyType, finger_number: int = 5) -> None:
        self.left_hand_position = left_hand_position
        self.right_hand_position = right_hand_position
        self.key_type = key_type
        self.finger_number = finger_number
        self.body_position = (left_hand_position + right_hand_position)/2

        self.left_finger_indexs = [finger_index for finger_index in range(
            self.finger_number)]
        self.right_finger_indexs = [finger_index for finger_index in range(
            self.finger_number, 2*self.finger_number)]

        finger_positions = {}

        for finger_index in self.left_finger_indexs:
            finger_positions[finger_index] = f'P{left_hand_position}_{right_hand_position}_finger{finger_index}_{key_type.value}'

        for finger_index in self.right_finger_indexs:
            finger_positions[finger_index] = f'P{left_hand_position}_{right_hand_position}_finger{finger_index}_{key_type.value}'

        self.position_balls = {
            "left_hand_position_ball": {
                "name": f'P{left_hand_position}_{right_hand_position}_H_{key_type.value}_L',
                "collection": "hand_position_balls"},
            "right_hand_position_ball": {
                "name": f'P{left_hand_position}_{right_hand_position}_H_{key_type.value}_R',
                "collection": "hand_position_balls"},
            "left_hand_pivot_position": {
                "name": f'P{left_hand_position}_{right_hand_position}_HP_{key_type.value}_L',
                "collection": "hand_position_balls"},
            "right_hand_pivot_position": {
                "name": f'P{left_hand_position}_{right_hand_position}_HP_{key_type.value}_R',
                "collection": "hand_position_balls"},
            "finger_positions": {
                "names": finger_positions,
                "collection": f"finger_position_balls"}
        }

        self.rotate_cones = {
            "left_rotate_cone": {
                "name": f'P{left_hand_position}_{right_hand_position}_H_rotation_{key_type.value}_L',
                "collection": "hand_rotation_cones"
            },
            "right_rotate_cone": {
                "name": f'P{left_hand_position}_{right_hand_position}_H_rotation_{key_type.value}_R',
                "collection": "hand_rotation_cones"
            }
        }


class NormalBaseState(Enum):
    BOTH_FAR_WHITE = BaseState(24, 105, KeyType.WHITE, 5)
    BOTH_MIDDLE_WHITE = BaseState(52, 76, KeyType.WHITE, 5)
    RIGHT_FAR_LEFT_MIDDLE_WHITE = BaseState(52, 105, KeyType.WHITE, 5)
    LEFT_FAR_RIGHT_MIDDLE_BLACK = BaseState(24, 76, KeyType.BLACK, 5)
