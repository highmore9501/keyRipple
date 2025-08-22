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


def generate_base_state_recorders(base_state: BaseState):
    # 处理 position_balls
    position_balls = base_state.position_balls

    # 处理左手位置球
    left_hand_position_data = position_balls["left_hand_position_ball"]
    left_hand_position_name = left_hand_position_data["name"]
    left_hand_position_collection = left_hand_position_data["collection"]

    if left_hand_position_name not in bpy.data.objects:
        # 创建球形空物体
        left_hand_position_ball = bpy.data.objects.new(
            left_hand_position_name, None)
        left_hand_position_ball.empty_display_type = 'SPHERE'
        left_hand_position_ball.empty_display_size = 0.1

        # 添加到场景中
        bpy.context.collection.objects.link(left_hand_position_ball)

        # 将物体移动到对应的集合
        target_collection = bpy.data.collections.get(
            left_hand_position_collection)
        if target_collection:
            # 从当前所有集合中移除
            for coll in left_hand_position_ball.users_collection:
                coll.objects.unlink(left_hand_position_ball)
            # 添加到目标集合
            target_collection.objects.link(left_hand_position_ball)

    # 处理右手位置球
    right_hand_position_data = position_balls["right_hand_position_ball"]
    right_hand_position_name = right_hand_position_data["name"]
    right_hand_position_collection = right_hand_position_data["collection"]

    if right_hand_position_name not in bpy.data.objects:
        # 创建球形空物体
        right_hand_position_ball = bpy.data.objects.new(
            right_hand_position_name, None)
        right_hand_position_ball.empty_display_type = 'SPHERE'
        right_hand_position_ball.empty_display_size = 0.1

        # 添加到场景中
        bpy.context.collection.objects.link(right_hand_position_ball)

        # 将物体移动到对应的集合
        target_collection = bpy.data.collections.get(
            right_hand_position_collection)
        if target_collection:
            # 从当前所有集合中移除
            for coll in right_hand_position_ball.users_collection:
                coll.objects.unlink(right_hand_position_ball)
            # 添加到目标集合
            target_collection.objects.link(right_hand_position_ball)

    # 处理左手轴心点
    left_hand_pivot_data = position_balls["left_hand_pivot_position"]
    left_hand_pivot_name = left_hand_pivot_data["name"]
    left_hand_pivot_collection = left_hand_pivot_data["collection"]

    if left_hand_pivot_name not in bpy.data.objects:
        # 创建球形空物体
        left_hand_pivot_position = bpy.data.objects.new(
            left_hand_pivot_name, None)
        left_hand_pivot_position.empty_display_type = 'SPHERE'
        left_hand_pivot_position.empty_display_size = 0.1

        # 添加到场景中
        bpy.context.collection.objects.link(left_hand_pivot_position)

        # 将物体移动到对应的集合
        target_collection = bpy.data.collections.get(
            left_hand_pivot_collection)
        if target_collection:
            # 从当前所有集合中移除
            for coll in left_hand_pivot_position.users_collection:
                coll.objects.unlink(left_hand_pivot_position)
            # 添加到目标集合
            target_collection.objects.link(left_hand_pivot_position)

    # 处理右手轴心点
    right_hand_pivot_data = position_balls["right_hand_pivot_position"]
    right_hand_pivot_name = right_hand_pivot_data["name"]
    right_hand_pivot_collection = right_hand_pivot_data["collection"]

    if right_hand_pivot_name not in bpy.data.objects:
        # 创建球形空物体
        right_hand_pivot_position = bpy.data.objects.new(
            right_hand_pivot_name, None)
        right_hand_pivot_position.empty_display_type = 'SPHERE'
        right_hand_pivot_position.empty_display_size = 0.1

        # 添加到场景中
        bpy.context.collection.objects.link(right_hand_pivot_position)

        # 将物体移动到对应的集合
        target_collection = bpy.data.collections.get(
            right_hand_pivot_collection)
        if target_collection:
            # 从当前所有集合中移除
            for coll in right_hand_pivot_position.users_collection:
                coll.objects.unlink(right_hand_pivot_position)
            # 添加到目标集合
            target_collection.objects.link(right_hand_pivot_position)

    # 处理手指位置球
    finger_positions_data = position_balls["finger_positions"]
    finger_positions_dict = finger_positions_data["names"]
    finger_positions_collection = finger_positions_data["collection"]

    for finger_index, finger_position_name in finger_positions_dict.items():
        if finger_position_name not in bpy.data.objects:
            # 创建球形空物体
            finger_position_ball = bpy.data.objects.new(
                finger_position_name, None)
            finger_position_ball.empty_display_type = 'SPHERE'
            finger_position_ball.empty_display_size = 0.05

            # 添加到场景中
            bpy.context.collection.objects.link(finger_position_ball)

            # 将物体移动到对应的集合
            target_collection = bpy.data.collections.get(
                finger_positions_collection)
            if target_collection:
                # 从当前所有集合中移除
                for coll in finger_position_ball.users_collection:
                    coll.objects.unlink(finger_position_ball)
                # 添加到目标集合
                target_collection.objects.link(finger_position_ball)

    # 处理旋转锥体
    rotate_cones = base_state.rotate_cones

    # 处理左手旋转锥体
    left_rotate_cone_data = rotate_cones["left_rotate_cone"]
    left_rotate_cone_name = left_rotate_cone_data["name"]
    left_rotate_cone_collection = left_rotate_cone_data["collection"]

    if left_rotate_cone_name not in bpy.data.objects:
        # 创建圆锥形空物体
        left_rotate_cone = bpy.data.objects.new(left_rotate_cone_name, None)
        left_rotate_cone.empty_display_type = 'CONE'
        left_rotate_cone.empty_display_size = 0.1

        # 添加到场景中
        bpy.context.collection.objects.link(left_rotate_cone)

        # 将物体移动到对应的集合
        target_collection = bpy.data.collections.get(
            left_rotate_cone_collection)
        if target_collection:
            # 从当前所有集合中移除
            for coll in left_rotate_cone.users_collection:
                coll.objects.unlink(left_rotate_cone)
            # 添加到目标集合
            target_collection.objects.link(left_rotate_cone)

    # 处理右手旋转锥体
    right_rotate_cone_data = rotate_cones["right_rotate_cone"]
    right_rotate_cone_name = right_rotate_cone_data["name"]
    right_rotate_cone_collection = right_rotate_cone_data["collection"]

    if right_rotate_cone_name not in bpy.data.objects:
        # 创建圆锥形空物体
        right_rotate_cone = bpy.data.objects.new(right_rotate_cone_name, None)
        right_rotate_cone.empty_display_type = 'CONE'
        right_rotate_cone.empty_display_size = 0.1

        # 添加到场景中
        bpy.context.collection.objects.link(right_rotate_cone)

        # 将物体移动到对应的集合
        target_collection = bpy.data.collections.get(
            right_rotate_cone_collection)
        if target_collection:
            # 从当前所有集合中移除
            for coll in right_rotate_cone.users_collection:
                coll.objects.unlink(right_rotate_cone)
            # 添加到目标集合
            target_collection.objects.link(right_rotate_cone)

    # 处理手部目标点 (新增部分)
    hand_targets = base_state.hand_target

    # 处理左手目标点
    left_hand_target_data = hand_targets["left_hand_target"]
    left_hand_target_name = left_hand_target_data["name"]
    left_hand_target_collection = left_hand_target_data["collection"]

    if left_hand_target_name not in bpy.data.objects:
        # 创建圆锥形空物体
        left_hand_target = bpy.data.objects.new(left_hand_target_name, None)
        left_hand_target.empty_display_type = 'CONE'
        left_hand_target.empty_display_size = 0.1

        # 添加到场景中
        bpy.context.collection.objects.link(left_hand_target)

        # 将物体移动到对应的集合
        target_collection = bpy.data.collections.get(
            left_hand_target_collection)
        if target_collection:
            # 从当前所有集合中移除
            for coll in left_hand_target.users_collection:
                coll.objects.unlink(left_hand_target)
            # 添加到目标集合
            target_collection.objects.link(left_hand_target)

    # 处理右手目标点
    right_hand_target_data = hand_targets["right_hand_target"]
    right_hand_target_name = right_hand_target_data["name"]
    right_hand_target_collection = right_hand_target_data["collection"]

    if right_hand_target_name not in bpy.data.objects:
        # 创建圆锥形空物体
        right_hand_target = bpy.data.objects.new(right_hand_target_name, None)
        right_hand_target.empty_display_type = 'CONE'
        right_hand_target.empty_display_size = 0.1

        # 添加到场景中
        bpy.context.collection.objects.link(right_hand_target)

        # 将物体移动到对应的集合
        target_collection = bpy.data.collections.get(
            right_hand_target_collection)
        if target_collection:
            # 从当前所有集合中移除
            for coll in right_hand_target.users_collection:
                coll.objects.unlink(right_hand_target)
            # 添加到目标集合
            target_collection.objects.link(right_hand_target)


if __name__ == "__main__":
    base_states: list[BaseState] = []

    base_states.append(BaseState(24, 52, KeyType.WHITE))
    base_states.append(BaseState(52, 76, KeyType.BLACK))
    base_states.append(BaseState(76, 105, KeyType.WHITE))

    # 为以上所有状态生成位置球
    for base_state in base_states:
        generate_base_state_recorders(base_state)
