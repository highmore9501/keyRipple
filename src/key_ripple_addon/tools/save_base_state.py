from enum import Enum
import bpy  # type: ignore


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


def operate_base_state(base_state: BaseState, is_operate_save: bool = False):
    """
    操作基准状态：保存或加载手部位置和旋转数据
    :param base_state: BaseState 对象
    :param is_operate_save: True 表示保存操作，False 表示加载操作
    """
    # 获取 position_balls 数据
    position_balls = base_state.position_balls

    # 定义一个辅助函数来处理位置复制
    def copy_position(source_obj, target_obj):
        target_obj.location = source_obj.location
        print(f"已复制 {source_obj.name} 的位置到 {target_obj.name}")

    # 定义一个辅助函数来处理旋转复制
    def copy_rotation(source_obj, target_obj):
        if source_obj.rotation_mode == 'QUATERNION':
            target_obj.rotation_quaternion = source_obj.rotation_quaternion
        else:
            target_obj.rotation_euler = source_obj.rotation_euler

        print(f"已复制 {source_obj.name} 的旋转到 {target_obj.name}")

    # 处理手指位置球
    finger_positions_dict = position_balls["finger_positions"]["names"]

    for finger_index, finger_position_name in finger_positions_dict.items():
        finger_obj_name = f'{finger_index}'

        # 检查对象是否存在
        if finger_obj_name in bpy.data.objects and finger_position_name in bpy.data.objects:
            finger_obj = bpy.data.objects[finger_obj_name]
            finger_position_ball = bpy.data.objects[finger_position_name]

            # 根据操作类型确定源和目标
            if is_operate_save:
                copy_position(finger_obj, finger_position_ball)
            else:
                copy_position(finger_position_ball, finger_obj)
        else:
            # 错误处理
            if finger_obj_name not in bpy.data.objects:
                print(f"警告: 未找到手指物体 {finger_obj_name}")
            if finger_position_name not in bpy.data.objects:
                print(f"警告: 未找到手指位置球 {finger_position_name}")

    # 处理手部目标点
    hand_targets = base_state.hand_target

    # 处理左手目标点
    left_hand_target_name = hand_targets["left_hand_target"]["name"]
    left_hand_target_obj_name = f'Tar_H_L'

    # 检查对象是否存在
    if left_hand_target_obj_name in bpy.data.objects and left_hand_target_name in bpy.data.objects:
        left_hand_target_obj = bpy.data.objects[left_hand_target_obj_name]
        left_hand_target = bpy.data.objects[left_hand_target_name]

        # 检查旋转模式是否一致
        target_obj = left_hand_target_obj if is_operate_save else left_hand_target
        source_obj = left_hand_target if is_operate_save else left_hand_target_obj
        if target_obj.rotation_mode != source_obj.rotation_mode:
            names = (left_hand_target_obj_name, left_hand_target_name) if is_operate_save else (
                left_hand_target_name, left_hand_target_obj_name)
            print(f"警告: {names[0]} 和 {names[1]} 的旋转模式不一致")
        else:
            # 根据操作类型确定源和目标
            if is_operate_save:
                copy_position(left_hand_target_obj, left_hand_target)
                copy_rotation(left_hand_target_obj, left_hand_target)
            else:
                copy_position(left_hand_target, left_hand_target_obj)
                copy_rotation(left_hand_target, left_hand_target_obj)
    else:
        # 错误处理
        if left_hand_target_obj_name not in bpy.data.objects:
            print(f"警告: 未找到目标控制器 {left_hand_target_obj_name}")
        if left_hand_target_name not in bpy.data.objects:
            print(f"警告: 未找到目标记录器 {left_hand_target_name}")

    # 处理右手目标点
    right_hand_target_name = hand_targets["right_hand_target"]["name"]
    right_hand_target_obj_name = f'Tar_H_R'

    # 检查对象是否存在
    if right_hand_target_obj_name in bpy.data.objects and right_hand_target_name in bpy.data.objects:
        right_hand_target_obj = bpy.data.objects[right_hand_target_obj_name]
        right_hand_target = bpy.data.objects[right_hand_target_name]

        # 检查旋转模式是否一致
        target_obj = right_hand_target_obj if is_operate_save else right_hand_target
        source_obj = right_hand_target if is_operate_save else right_hand_target_obj
        if target_obj.rotation_mode != source_obj.rotation_mode:
            names = (right_hand_target_obj_name, right_hand_target_name) if is_operate_save else (
                right_hand_target_name, right_hand_target_obj_name)
            print(f"警告: {names[0]} 和 {names[1]} 的旋转模式不一致")
        else:
            # 根据操作类型确定源和目标
            if is_operate_save:
                copy_position(right_hand_target_obj, right_hand_target)
                copy_rotation(right_hand_target_obj, right_hand_target)
            else:
                copy_position(right_hand_target, right_hand_target_obj)
                copy_rotation(right_hand_target, right_hand_target_obj)
    else:
        # 错误处理
        if right_hand_target_obj_name not in bpy.data.objects:
            print(f"警告: 未找到目标控制器 {right_hand_target_obj_name}")
        if right_hand_target_name not in bpy.data.objects:
            print(f"警告: 未找到目标记录器 {right_hand_target_name}")


if __name__ == "__main__":
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
    base_state_index = 2

    left_hand_note = base_states[str(
        base_state_index)]["left_hand_note"]
    right_hand_note = base_states[str(
        base_state_index)]["right_hand_note"]
    key_type = base_states[str(base_state_index)]["key_type"]

    base_state = BaseState(left_hand_note, right_hand_note, key_type)

    is_operate_save = False
    # is_operate_save = True

    operate_base_state(base_state, is_operate_save)
