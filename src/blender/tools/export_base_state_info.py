from enum import Enum
import bpy  # type: ignore
import json


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

        self.hand_expand_targets = {}


def export_base_state_info(left_hand_note: int, right_hand_note: int, key_type: KeyType) -> dict:
    # 创建 BaseState 实例
    base_state = BaseState(left_hand_note, right_hand_note, key_type)

    # 初始化导出数据
    export_data = {
        "base_state_params": {
            "left_hand_note": left_hand_note,
            "right_hand_note": right_hand_note,
            "key_type": key_type.value
        },
        "position_balls": {
            "finger_positions": {}
        },
        "hand_targets": {
            "left_hand_target": {},
            "right_hand_target": {}
        }
    }

    # 获取手指位置球位置
    finger_positions_dict = base_state.position_balls["finger_positions"]["names"]
    export_data["position_balls"]["finger_positions"] = {
        "names": {}
    }

    for finger_index, finger_position_name in finger_positions_dict.items():
        finger_obj_name = f'{finger_index}'

        if finger_obj_name in bpy.data.objects and finger_position_name in bpy.data.objects:
            finger_position_ball = bpy.data.objects[finger_position_name]
            export_data["position_balls"]["finger_positions"]["names"][finger_index] = {
                "name": finger_position_name,
                "location": list(finger_position_ball.location)
            }
        else:
            print(f"{finger_position_name} 没找到")

    # 获取左手目标点位置和旋转值
    left_hand_target_name = base_state.hand_target["left_hand_target"]["name"]
    left_hand_target_obj_name = f'Tar_H_L'

    if left_hand_target_obj_name in bpy.data.objects and left_hand_target_name in bpy.data.objects:
        left_hand_target = bpy.data.objects[left_hand_target_name]
        # 根据旋转模式导出相应的旋转值
        if left_hand_target.rotation_mode == 'QUATERNION':
            export_data["hand_targets"]["left_hand_target"] = {
                "name": left_hand_target_name,
                "location": list(left_hand_target.location),
                "rotation_mode": "QUATERNION",
                "rotation": list(left_hand_target.rotation_quaternion)
            }
        else:
            export_data["hand_targets"]["left_hand_target"] = {
                "name": left_hand_target_name,
                "location": list(left_hand_target.location),
                "rotation_mode": left_hand_target.rotation_mode,
                "rotation": list(left_hand_target.rotation_euler)
            }
    else:
        print(
            f"警告: 未找到目标控制器 {left_hand_target_obj_name} 或目标记录器 {left_hand_target_name}")

    # 获取右手目标点位置和旋转值
    right_hand_target_name = base_state.hand_target["right_hand_target"]["name"]
    right_hand_target_obj_name = f'Tar_H_R'

    if right_hand_target_obj_name in bpy.data.objects and right_hand_target_name in bpy.data.objects:
        right_hand_target = bpy.data.objects[right_hand_target_name]
        # 根据旋转模式导出相应的旋转值
        if right_hand_target.rotation_mode == 'QUATERNION':
            export_data["hand_targets"]["right_hand_target"] = {
                "name": right_hand_target_name,
                "location": list(right_hand_target.location),
                "rotation_mode": "QUATERNION",
                "rotation": list(right_hand_target.rotation_quaternion)
            }
        else:
            export_data["hand_targets"]["right_hand_target"] = {
                "name": right_hand_target_name,
                "location": list(right_hand_target.location),
                "rotation_mode": right_hand_target.rotation_mode,
                "rotation": list(right_hand_target.rotation_euler)
            }
    else:
        print(
            f"警告: 未找到目标控制器 {right_hand_target_obj_name} 或目标记录器 {right_hand_target_name}")

    return export_data


def export_piano_info() -> dict:
    piano_info = {}

    # 定义需要导出的钢琴关键物体名称
    key_objects = [
        "black_key",
        "highest_white_key",
        "lowest_white_key"
    ]

    # 遍历每个关键物体，获取它们的位置信息
    for obj_name in key_objects:
        if obj_name in bpy.data.objects:
            obj = bpy.data.objects[obj_name]
            piano_info[obj_name] = {
                "location": list(obj.location)
            }
        else:
            raise KeyError(f"未找到对象 {obj_name}")

    return piano_info


def export_expand_info() -> dict:
    # 寻找后缀为.expand的物体，以及它的参照对象
    hand_expand_target = [
        obj for obj in bpy.data.objects if obj.name.endswith(".expand")][0]
    hand_expand_target_obj_name = hand_expand_target.name.replace(
        ".expand", "")
    hand_expand_target_obj = bpy.data.objects[hand_expand_target_obj_name]
    hand_expand_targets = {
        "hand_expand_target": {
            "name": hand_expand_target.name,
            "location": list(hand_expand_target.location),
            "collection": "hand_expand_targets"
        },
        "hand_expand_target_obj": {
            "name": hand_expand_target_obj_name,
            "location": list(hand_expand_target_obj.location),
            "collection": "hand_expand_targets"
        }
    }
    return hand_expand_targets


if __name__ == "__main__":
    avatar_name = "kinich"
    file_path = f"H:/keyRipple/asset/avatars/{avatar_name}.avatar"

    base_states = {
        "0": {
            "left_hand_note": 24,
            "right_hand_note": 52,
            "key_type": KeyType.WHITE,
        },
        "1": {
            "left_hand_note": 52,
            "right_hand_note": 76,
            "key_type": KeyType.BLACK,
        },
        "2": {
            "left_hand_note": 76,
            "right_hand_note": 105,
            "key_type": KeyType.WHITE,
        }
    }

    result = {
        "piano_info": export_piano_info(),
        "hand_expand_targets": export_expand_info(),
        "base_states": []
    }

    for i in range(3):
        base_state = base_states[f"{i}"]
        left_hand_note = base_state["left_hand_note"]
        right_hand_note = base_state["right_hand_note"]
        key_type = base_state["key_type"]
        result["base_states"].append(export_base_state_info(
            left_hand_note, right_hand_note, key_type))

    with open(file_path, 'w') as f:
        json.dump(result, f)
        print(f'已导出{avatar_name}的基础状态信息到 {file_path}')
