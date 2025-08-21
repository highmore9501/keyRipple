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


def save_base_state(base_state: BaseState):
    # 获取 position_balls 数据
    position_balls = base_state.position_balls

    # 保存左手位置球位置
    left_hand_position_ball_name = position_balls["left_hand_position_ball"]["name"]
    left_hand_obj_name = f'H_L'

    if left_hand_obj_name in bpy.data.objects and left_hand_position_ball_name in bpy.data.objects:
        left_hand_obj = bpy.data.objects[left_hand_obj_name]
        left_hand_position_ball = bpy.data.objects[left_hand_position_ball_name]
        # 设置位置
        left_hand_position_ball.location = left_hand_obj.location
    else:
        if left_hand_obj_name not in bpy.data.objects:
            print(f"警告: 未找到物体 {left_hand_obj_name}")
        if left_hand_position_ball_name not in bpy.data.objects:
            print(f"警告: 未找到位置球 {left_hand_position_ball_name}")

    # 保存右手位置球位置
    right_hand_position_ball_name = position_balls["right_hand_position_ball"]["name"]
    right_hand_obj_name = f'H_R'

    if right_hand_obj_name in bpy.data.objects and right_hand_position_ball_name in bpy.data.objects:
        right_hand_obj = bpy.data.objects[right_hand_obj_name]
        right_hand_position_ball = bpy.data.objects[right_hand_position_ball_name]
        # 设置位置
        right_hand_position_ball.location = right_hand_obj.location
    else:
        if right_hand_obj_name not in bpy.data.objects:
            print(f"警告: 未找到物体 {right_hand_obj_name}")
        if right_hand_position_ball_name not in bpy.data.objects:
            print(f"警告: 未找到位置球 {right_hand_position_ball_name}")

    # 保存左手轴心点位置
    left_hand_pivot_position_name = position_balls["left_hand_pivot_position"]["name"]
    left_hand_pivot_obj_name = f'HP_L'

    if left_hand_pivot_obj_name in bpy.data.objects and left_hand_pivot_position_name in bpy.data.objects:
        left_hand_pivot_obj = bpy.data.objects[left_hand_pivot_obj_name]
        left_hand_pivot_position = bpy.data.objects[left_hand_pivot_position_name]
        # 设置位置
        left_hand_pivot_position.location = left_hand_pivot_obj.location
    else:
        if left_hand_pivot_obj_name not in bpy.data.objects:
            print(f"警告: 未找到物体 {left_hand_pivot_obj_name}")
        if left_hand_pivot_position_name not in bpy.data.objects:
            print(f"警告: 未找到轴心点 {left_hand_pivot_position_name}")

    # 保存右手轴心点位置
    right_hand_pivot_position_name = position_balls["right_hand_pivot_position"]["name"]
    right_hand_pivot_obj_name = f'HP_R'

    if right_hand_pivot_obj_name in bpy.data.objects and right_hand_pivot_position_name in bpy.data.objects:
        right_hand_pivot_obj = bpy.data.objects[right_hand_pivot_obj_name]
        right_hand_pivot_position = bpy.data.objects[right_hand_pivot_position_name]
        # 设置位置
        right_hand_pivot_position.location = right_hand_pivot_obj.location
    else:
        if right_hand_pivot_obj_name not in bpy.data.objects:
            print(f"警告: 未找到物体 {right_hand_pivot_obj_name}")
        if right_hand_pivot_position_name not in bpy.data.objects:
            print(f"警告: 未找到轴心点 {right_hand_pivot_position_name}")

    # 保存手指位置球位置
    finger_positions_dict = position_balls["finger_positions"]["names"]

    for finger_index, finger_position_name in finger_positions_dict.items():
        finger_obj_name = f'{finger_index}'

        if finger_obj_name in bpy.data.objects and finger_position_name in bpy.data.objects:
            finger_obj = bpy.data.objects[finger_obj_name]
            finger_position_ball = bpy.data.objects[finger_position_name]
            # 设置位置
            finger_position_ball.location = finger_obj.location
        else:
            if finger_obj_name not in bpy.data.objects:
                print(f"警告: 未找到手指物体 {finger_obj_name}")
            if finger_position_name not in bpy.data.objects:
                print(f"警告: 未找到手指位置球 {finger_position_name}")

    # 保存左手旋转锥体旋转值
    left_rotate_cone_name = base_state.rotate_cones["left_rotate_cone"]["name"]
    left_hand_rotation_obj_name = f'H_rotation_L'

    if left_hand_rotation_obj_name in bpy.data.objects and left_rotate_cone_name in bpy.data.objects:
        left_hand_rotation_obj = bpy.data.objects[left_hand_rotation_obj_name]
        left_rotate_cone = bpy.data.objects[left_rotate_cone_name]
        # 设置旋转
        left_rotate_cone.rotation_euler = left_hand_rotation_obj.rotation_euler
    else:
        if left_hand_rotation_obj_name not in bpy.data.objects:
            print(f"警告: 未找到旋转物体 {left_hand_rotation_obj_name}")
        if left_rotate_cone_name not in bpy.data.objects:
            print(f"警告: 未找到旋转锥体 {left_rotate_cone_name}")

    # 保存右手旋转锥体旋转值
    right_rotate_cone_name = base_state.rotate_cones["right_rotate_cone"]["name"]
    right_hand_rotation_obj_name = f'H_rotation_R'

    if right_hand_rotation_obj_name in bpy.data.objects and right_rotate_cone_name in bpy.data.objects:
        right_hand_rotation_obj = bpy.data.objects[right_hand_rotation_obj_name]
        right_rotate_cone = bpy.data.objects[right_rotate_cone_name]
        # 设置旋转
        right_rotate_cone.rotation_euler = right_hand_rotation_obj.rotation_euler
    else:
        if right_hand_rotation_obj_name not in bpy.data.objects:
            print(f"警告: 未找到旋转物体 {right_hand_rotation_obj_name}")
        if right_rotate_cone_name not in bpy.data.objects:
            print(f"警告: 未找到旋转锥体 {right_rotate_cone_name}")


def load_base_state(base_state: BaseState):
    # 获取 position_balls 数据
    position_balls = base_state.position_balls

    # 从左手位置球加载位置到对应物体
    left_hand_position_ball_name = position_balls["left_hand_position_ball"]["name"]
    left_hand_obj_name = f'H_L'

    if left_hand_obj_name in bpy.data.objects and left_hand_position_ball_name in bpy.data.objects:
        left_hand_obj = bpy.data.objects[left_hand_obj_name]
        left_hand_position_ball = bpy.data.objects[left_hand_position_ball_name]
        # 应用位置
        left_hand_obj.location = left_hand_position_ball.location
    else:
        if left_hand_obj_name not in bpy.data.objects:
            print(f"警告: 未找到物体 {left_hand_obj_name}")
        if left_hand_position_ball_name not in bpy.data.objects:
            print(f"警告: 未找到位置球 {left_hand_position_ball_name}")

    # 从右手位置球加载位置到对应物体
    right_hand_position_ball_name = position_balls["right_hand_position_ball"]["name"]
    right_hand_obj_name = f'H_R'

    if right_hand_obj_name in bpy.data.objects and right_hand_position_ball_name in bpy.data.objects:
        right_hand_obj = bpy.data.objects[right_hand_obj_name]
        right_hand_position_ball = bpy.data.objects[right_hand_position_ball_name]
        # 应用位置
        right_hand_obj.location = right_hand_position_ball.location
    else:
        if right_hand_obj_name not in bpy.data.objects:
            print(f"警告: 未找到物体 {right_hand_obj_name}")
        if right_hand_position_ball_name not in bpy.data.objects:
            print(f"警告: 未找到位置球 {right_hand_position_ball_name}")

    # 从左手轴心点加载位置到对应物体
    left_hand_pivot_position_name = position_balls["left_hand_pivot_position"]["name"]
    left_hand_pivot_obj_name = f'HP_L'

    if left_hand_pivot_obj_name in bpy.data.objects and left_hand_pivot_position_name in bpy.data.objects:
        left_hand_pivot_obj = bpy.data.objects[left_hand_pivot_obj_name]
        left_hand_pivot_position = bpy.data.objects[left_hand_pivot_position_name]
        # 应用位置
        left_hand_pivot_obj.location = left_hand_pivot_position.location
    else:
        if left_hand_pivot_obj_name not in bpy.data.objects:
            print(f"警告: 未找到物体 {left_hand_pivot_obj_name}")
        if left_hand_pivot_position_name not in bpy.data.objects:
            print(f"警告: 未找到轴心点 {left_hand_pivot_position_name}")

    # 从右手轴心点加载位置到对应物体
    right_hand_pivot_position_name = position_balls["right_hand_pivot_position"]["name"]
    right_hand_pivot_obj_name = f'HP_R'

    if right_hand_pivot_obj_name in bpy.data.objects and right_hand_pivot_position_name in bpy.data.objects:
        right_hand_pivot_obj = bpy.data.objects[right_hand_pivot_obj_name]
        right_hand_pivot_position = bpy.data.objects[right_hand_pivot_position_name]
        # 应用位置
        right_hand_pivot_obj.location = right_hand_pivot_position.location
    else:
        if right_hand_pivot_obj_name not in bpy.data.objects:
            print(f"警告: 未找到物体 {right_hand_pivot_obj_name}")
        if right_hand_pivot_position_name not in bpy.data.objects:
            print(f"警告: 未找到轴心点 {right_hand_pivot_position_name}")

    # 从手指位置球加载位置到对应物体
    finger_positions_dict = position_balls["finger_positions"]["names"]

    for finger_index, finger_position_name in finger_positions_dict.items():
        finger_obj_name = f'{finger_index}'

        if finger_obj_name in bpy.data.objects and finger_position_name in bpy.data.objects:
            finger_obj = bpy.data.objects[finger_obj_name]
            finger_position_ball = bpy.data.objects[finger_position_name]
            # 应用位置
            finger_obj.location = finger_position_ball.location
        else:
            if finger_obj_name not in bpy.data.objects:
                print(f"警告: 未找到手指物体 {finger_obj_name}")
            if finger_position_name not in bpy.data.objects:
                print(f"警告: 未找到手指位置球 {finger_position_name}")

    # 从左手旋转锥体加载旋转到对应物体
    left_rotate_cone_name = base_state.rotate_cones["left_rotate_cone"]["name"]
    left_hand_rotation_obj_name = f'H_rotation_L'

    if left_hand_rotation_obj_name in bpy.data.objects and left_rotate_cone_name in bpy.data.objects:
        left_hand_rotation_obj = bpy.data.objects[left_hand_rotation_obj_name]
        left_rotate_cone = bpy.data.objects[left_rotate_cone_name]
        # 应用旋转
        left_hand_rotation_obj.rotation_euler = left_rotate_cone.rotation_euler
    else:
        if left_hand_rotation_obj_name not in bpy.data.objects:
            print(f"警告: 未找到旋转物体 {left_hand_rotation_obj_name}")
        if left_rotate_cone_name not in bpy.data.objects:
            print(f"警告: 未找到旋转锥体 {left_rotate_cone_name}")

    # 从右手旋转锥体加载旋转到对应物体
    right_rotate_cone_name = base_state.rotate_cones["right_rotate_cone"]["name"]
    right_hand_rotation_obj_name = f'H_rotation_R'

    if right_hand_rotation_obj_name in bpy.data.objects and right_rotate_cone_name in bpy.data.objects:
        right_hand_rotation_obj = bpy.data.objects[right_hand_rotation_obj_name]
        right_rotate_cone = bpy.data.objects[right_rotate_cone_name]
        # 应用旋转
        right_hand_rotation_obj.rotation_euler = right_rotate_cone.rotation_euler
    else:
        if right_hand_rotation_obj_name not in bpy.data.objects:
            print(f"警告: 未找到旋转物体 {right_hand_rotation_obj_name}")
        if right_rotate_cone_name not in bpy.data.objects:
            print(f"警告: 未找到旋转锥体 {right_rotate_cone_name}")


if __name__ == "__main__":
    base_states = {
        "0": {
            "left_hand_position": 24,
            "right_hand_position": 105,
            "key_type": KeyType.WHITE,
        },
        "1": {
            "left_hand_position": 52,
            "right_hand_position": 76,
            "key_type": KeyType.WHITE,
        },
        "2": {
            "left_hand_position": 24,
            "right_hand_position": 76,
            "key_type": KeyType.BLACK,
        },
        "3": {
            "left_hand_position": 52,
            "right_hand_position": 105,
            "key_type": KeyType.WHITE,
        }
    }
    base_state_index = 2

    left_hand_position = base_states[str(
        base_state_index)]["left_hand_position"]
    right_hand_position = base_states[str(
        base_state_index)]["right_hand_position"]
    key_type = base_states[str(base_state_index)]["key_type"]

    base_state = BaseState(left_hand_position, right_hand_position, key_type)

    save_base_state(base_state)
    load_base_state(base_state)
