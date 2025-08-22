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
            finger_positions[finger_index] = f'P{left_hand_position}_finger{finger_index}_{key_type.value}'

        for finger_index in self.right_finger_indexs:
            finger_positions[finger_index] = f'P{right_hand_position}_finger{finger_index}_{key_type.value}'

        self.position_balls = {
            "left_hand_position_ball": {
                "name": f'P{left_hand_position}_H_{key_type.value}_L',
                "collection": "hand_position_balls"},
            "right_hand_position_ball": {
                "name": f'P{right_hand_position}_H_{key_type.value}_R',
                "collection": "hand_position_balls"},
            "left_hand_pivot_position": {
                "name": f'P{left_hand_position}_HP_{key_type.value}_L',
                "collection": "hand_position_balls"},
            "right_hand_pivot_position": {
                "name": f'P{right_hand_position}_HP_{key_type.value}_R',
                "collection": "hand_position_balls"},
            "finger_positions": {
                "names": finger_positions,
                "collection": f"finger_position_balls"}
        }

        self.rotate_cones = {
            "left_rotate_cone": {
                "name": f'P{left_hand_position}_H_rotation_{key_type.value}_L',
                "collection": "hand_rotation_cones"
            },
            "right_rotate_cone": {
                "name": f'P{right_hand_position}_H_rotation_{key_type.value}_R',
                "collection": "hand_rotation_cones"
            }
        }

        self.hand_target = {
            "left_hand_target": {
                "name": f'P{left_hand_position}_H_tar_{key_type.value}_L',
                "collection": "hand_targets"
            },
            "right_hand_target": {
                "name": f'P{right_hand_position}_H_tar_{key_type.value}_R',
                "collection": "hand_targets"
            }
        }


def export_base_state_info(left_hand_position: int, right_hand_position: int, key_type: KeyType) -> dict:
    # 创建 BaseState 实例
    base_state = BaseState(left_hand_position, right_hand_position, key_type)

    # 初始化导出数据
    export_data = {
        "base_state_params": {
            "left_hand_position": left_hand_position,
            "right_hand_position": right_hand_position,
            "key_type": key_type.value
        },
        "position_balls": {
            "left_hand_position_ball": {},
            "right_hand_position_ball": {},
            "left_hand_pivot_position": {},
            "right_hand_pivot_position": {},
            "finger_positions": {}
        },
        "rotate_cones": {
            "left_rotate_cone": {},
            "right_rotate_cone": {}
        },
        "hand_targets": {
            "left_hand_target": {},
            "right_hand_target": {}
        }
    }

    # 获取左手位置球位置
    left_hand_position_ball_name = base_state.position_balls["left_hand_position_ball"]["name"]
    left_hand_obj_name = f'H_L'

    if left_hand_obj_name in bpy.data.objects and left_hand_position_ball_name in bpy.data.objects:
        left_hand_position_ball = bpy.data.objects[left_hand_position_ball_name]
        export_data["position_balls"]["left_hand_position_ball"] = {
            "name": left_hand_position_ball_name,
            "location": list(left_hand_position_ball.location)
        }
    else:
        print(f"警告: 未找到位置球 {left_hand_position_ball_name}")

    # 获取右手位置球位置
    right_hand_position_ball_name = base_state.position_balls["right_hand_position_ball"]["name"]
    right_hand_obj_name = f'H_R'

    if right_hand_obj_name in bpy.data.objects and right_hand_position_ball_name in bpy.data.objects:
        right_hand_position_ball = bpy.data.objects[right_hand_position_ball_name]
        export_data["position_balls"]["right_hand_position_ball"] = {
            "name": right_hand_position_ball_name,
            "location": list(right_hand_position_ball.location)
        }
    else:
        print(f"警告: 未找到物体 {right_hand_obj_name}")

    # 获取左手轴心点位置
    left_hand_pivot_position_name = base_state.position_balls["left_hand_pivot_position"]["name"]
    left_hand_pivot_obj_name = f'HP_L'

    if left_hand_pivot_obj_name in bpy.data.objects and left_hand_pivot_position_name in bpy.data.objects:
        left_hand_pivot_position = bpy.data.objects[left_hand_pivot_position_name]
        export_data["position_balls"]["left_hand_pivot_position"] = {
            "name": left_hand_pivot_position_name,
            "location": list(left_hand_pivot_position.location)
        }
    else:
        print(f"警告: 未找到物体 {left_hand_pivot_obj_name}")

    # 获取右手轴心点位置
    right_hand_pivot_position_name = base_state.position_balls["right_hand_pivot_position"]["name"]
    right_hand_pivot_obj_name = f'HP_R'

    if right_hand_pivot_obj_name in bpy.data.objects and right_hand_pivot_position_name in bpy.data.objects:
        right_hand_pivot_position = bpy.data.objects[right_hand_pivot_position_name]
        export_data["position_balls"]["right_hand_pivot_position"] = {
            "name": right_hand_pivot_position_name,
            "location": list(right_hand_pivot_position.location)
        }
    else:
        print(f"警告: 未找到轴心点 {right_hand_pivot_position_name}")

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

    # 获取左手旋转锥体旋转值
    left_rotate_cone_name = base_state.rotate_cones["left_rotate_cone"]["name"]
    left_hand_rotation_obj_name = f'H_rotation_L'

    if left_hand_rotation_obj_name in bpy.data.objects and left_rotate_cone_name in bpy.data.objects:
        left_rotate_cone = bpy.data.objects[left_rotate_cone_name]
        # 根据旋转模式导出相应的旋转值
        if left_rotate_cone.rotation_mode == 'QUATERNION':
            export_data["rotate_cones"]["left_rotate_cone"] = {
                "name": left_rotate_cone_name,
                "rotation_mode": "QUATERNION",
                "rotation": list(left_rotate_cone.rotation_quaternion)
            }
        else:
            export_data["rotate_cones"]["left_rotate_cone"] = {
                "name": left_rotate_cone_name,
                "rotation_mode": left_rotate_cone.rotation_mode,
                "rotation": list(left_rotate_cone.rotation_euler)
            }
    else:
        print(f"警告: 未找到旋转物体 {left_hand_rotation_obj_name}")

    # 获取右手旋转锥体旋转值
    right_rotate_cone_name = base_state.rotate_cones["right_rotate_cone"]["name"]
    right_hand_rotation_obj_name = f'H_rotation_R'

    if right_hand_rotation_obj_name in bpy.data.objects and right_rotate_cone_name in bpy.data.objects:
        right_rotate_cone = bpy.data.objects[right_rotate_cone_name]
        # 根据旋转模式导出相应的旋转值
        if right_rotate_cone.rotation_mode == 'QUATERNION':
            export_data["rotate_cones"]["right_rotate_cone"] = {
                "name": right_rotate_cone_name,
                "rotation_mode": "QUATERNION",
                "rotation": list(right_rotate_cone.rotation_quaternion)
            }
        else:
            export_data["rotate_cones"]["right_rotate_cone"] = {
                "name": right_rotate_cone_name,
                "rotation_mode": right_rotate_cone.rotation_mode,
                "rotation": list(right_rotate_cone.rotation_euler)
            }
    else:
        print(
            f"警告: 未找到旋转物体 {right_hand_rotation_obj_name} 或旋转锥体 {right_rotate_cone_name}")

    # 获取左手目标点位置和旋转值 (新增部分)
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


if __name__ == "__main__":
    avatar_name = "kinich"
    file_path = f"H:/keyRipple/asset/avatars/{avatar_name}.avatar"

    base_states = {
        "0": {
            "left_hand_position": 24,
            "right_hand_position": 52,
            "key_type": KeyType.WHITE,
        },
        "1": {
            "left_hand_position": 52,
            "right_hand_position": 76,
            "key_type": KeyType.BLACK,
        },
        "2": {
            "left_hand_position": 76,
            "right_hand_position": 105,
            "key_type": KeyType.WHITE,
        }
    }

    result = {
        "piano_info": {},
        "base_states": []
    }

    for i in range(3):
        base_state = base_states[f"{i}"]
        left_hand_position = base_state["left_hand_position"]
        right_hand_position = base_state["right_hand_position"]
        key_type = base_state["key_type"]
        result["base_states"].append(export_base_state_info(
            left_hand_position, right_hand_position, key_type))

    result["piano_info"] = export_piano_info()

    with open(file_path, 'w') as f:
        json.dump(result, f)
        print(f'已导出{avatar_name}的基础状态信息到 {file_path}')
