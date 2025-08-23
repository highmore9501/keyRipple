import json
from src.animation.base_state import NormalBaseState, KeyType
from src.utils import calculate_3d_coefficients, evaluate_3d_point, calculate_2d_coefficients, evaluate_2d_point, quaternion_interpolation_from_3_points, get_key_location, get_touch_point, slerp
from src.piano.piano import Piano
from typing import Dict, Any
import numpy as np


class Animator:
    def __init__(self, hand_recorder_path: str, avatar_info_path: str, piano: Piano, FPS: int = 60):
        self.fps = FPS
        self.finger_count = 10
        self.piano = piano
        self.avatar_name = avatar_info_path.split('/')[-1].split('.')[0]
        self.midi_name = hand_recorder_path.split('/')[-1].split('.')[0]
        try:
            with open(hand_recorder_path, 'r') as f:
                self.hand_recorder = json.load(f)
            with open(avatar_info_path, 'r') as f:
                self.avatar_info = json.load(f)

            print(f'已加载{hand_recorder_path} 和 {avatar_info_path}')
        except Exception as e:
            print(e)

    def load_base_state_info(self):
        """
        从avatar_info读取所有基础状态信息，并为每个NormalBaseState枚举值创建对应的变量
        Returns:
            包含所有基础状态信息的字典
        """

        # 首先确定finger_positions的数量
        if self.avatar_info and len(self.avatar_info["base_states"]) > 0:
            finger_data = self.avatar_info["base_states"][0].get("position_balls", {}).get(
                "finger_positions", {}).get("names", {})
            self.finger_count = len(finger_data)

        # 创建一个字典来存储所有基础状态信息
        base_states_data = {
            "base_state_params": [],
            "finger_positions": {i: [] for i in range(self.finger_count)},
            "left_hand_target": [],
            "right_hand_target": []
        }

        # 遍历NormalBaseState枚举中的每个元素
        for enum_member in NormalBaseState:
            base_state = enum_member.value

            # 构造用于匹配JSON数据的标识符
            left_hand_note = base_state.left_hand_note
            right_hand_note = base_state.right_hand_note
            key_type = base_state.key_type.value

            # 在JSON数据中查找匹配的条目
            for data_entry in self.avatar_info["base_states"]:
                base_state_params = data_entry.get('base_state_params')
                if base_state_params and base_state_params.get('left_hand_note') == left_hand_note and \
                        base_state_params.get('right_hand_note') == right_hand_note and \
                        base_state_params.get('key_type') == key_type:

                    # 添加基础状态参数
                    base_states_data["base_state_params"].append(
                        data_entry.get("base_state_params"))

                    # 添加位置球信息
                    position_balls = data_entry.get("position_balls", {})

                    # 添加手指位置信息
                    finger_positions = position_balls.get(
                        "finger_positions", {}).get("names", {})
                    for i in range(self.finger_count):
                        finger_key = str(i)
                        if finger_key in finger_positions:
                            base_states_data["finger_positions"][i].append(
                                finger_positions[finger_key])
                        else:
                            base_states_data["finger_positions"][i].append(
                                None)

                    # 添加手部目标点信息
                    hand_targets = data_entry.get("hand_targets", {})
                    base_states_data["left_hand_target"].append(
                        hand_targets.get("left_hand_target"))
                    base_states_data["right_hand_target"].append(
                        hand_targets.get("right_hand_target"))

                    break

        self.base_states = base_states_data
        self.use_quaternion = self.avatar_info['base_states'][0][
            'hand_targets']['left_hand_target']['rotation_mode'] == 'QUATERNION'

    def generate_animation_info(self):
        coefficients = self.get_all_coefficients()

        animation_data = []
        recorder_number = len(self.hand_recorder)

        for i in range(recorder_number):
            item = self.hand_recorder[i]
            next_item = self.hand_recorder[i +
                                           1] if i+1 < recorder_number else None
            current_frame = item.get("frame")
            next_frame = next_item.get("frame") if next_item else None

            # 这个意思表示按键耗时为0.1秒，以帧为单位
            key_press_duration = self.fps / 10
            # 这个表示手会提前移动，提前的时间，也是以帧为单位
            ready_duration = self.fps / 5

            left_hand_item = item.get("left_hand")
            right_hand_item = item.get("right_hand")

            # 添加预备动作
            hand_ready_info = self.cacluate_hand_info(
                left_hand_item, right_hand_item, coefficients, True)
            animation_data.append({
                "frame": current_frame if i == 0 else current_frame - key_press_duration,
                "hand_infos": hand_ready_info
            })

            # 添加按键动作
            hand_finished_info = self.cacluate_hand_info(
                left_hand_item, right_hand_item, coefficients, False)
            animation_data.append({
                "frame": current_frame,
                "hand_infos": hand_finished_info
            })

            # 在时间允许的情况下添加保持动作
            if next_frame and next_frame - current_frame > ready_duration + key_press_duration:
                animation_data.append({
                    "frame": next_frame - key_press_duration-ready_duration,
                    "hand_infos": hand_ready_info
                })

            # 在间隔时间非常长的情况下要考虑不用的手回到休息位置

        file_path = f"output/animation_recorders/{self.midi_name}_{self.avatar_name}.animation"
        with open(file_path, "w") as f:
            json.dump(animation_data, f)

        print(f"动画数据已保存到{file_path}")

    def get_all_coefficients(self) -> dict:
        result = {}
        self.load_base_state_info()
        if self.base_states is None:
            raise Exception("未能成功加载人物状态数据")

        # 构建动画空间中的四个基准点
        animation_plane_base_points: dict = {}
        left_hand_base_points: list[np.ndarray] = []
        right_hand_base_points: list[np.ndarray] = []

        for i in range(3):
            base_state_param = self.base_states["base_state_params"][i]
            left_hand_note = base_state_param.get("left_hand_note")
            right_hand_note = base_state_param.get("right_hand_note")
            key_type = base_state_param.get("key_type")
            white_key_value = 1 if key_type == 'white' else 0
            left_hand_base_points.append(
                np.array([left_hand_note, white_key_value]))
            right_hand_base_points.append(
                np.array([right_hand_note, white_key_value]))

        animation_plane_base_points['left_hand_base_points'] = left_hand_base_points
        animation_plane_base_points['right_hand_base_points'] = right_hand_base_points

        # 准备各部位位置数据，确保格式正确

        # 处理手指位置
        result['finger_position_ball_2d_coefficients'] = {}
        for finger_index in range(self.finger_count):
            finger_positions = np.array([
                self.base_states["finger_positions"][finger_index][i].get(
                    'location')
                for i in range(3)
            ])
            if finger_index < 5:
                result['finger_position_ball_2d_coefficients'][str(
                    finger_index)] = calculate_2d_coefficients(left_hand_base_points, finger_positions)
            else:
                result['finger_position_ball_2d_coefficients'][str(
                    finger_index)] = calculate_2d_coefficients(right_hand_base_points, finger_positions)

        # 左手目标点位置
        left_hand_target_locs = np.array([
            self.base_states["left_hand_target"][i].get('location')
            for i in range(3)
        ])

        # 右手目标点位置
        right_hand_target_locs = np.array([
            self.base_states["right_hand_target"][i].get('location')
            for i in range(3)
        ])

        # 左手目标点旋转
        left_hand_target_rots = np.array([
            self.base_states["left_hand_target"][i].get('rotation')
            for i in range(3)
        ])

        # 右手目标点旋转
        right_hand_target_rots = np.array([
            self.base_states["right_hand_target"][i].get('rotation')
            for i in range(3)
        ])

        # 计算手部目标点的二维插值系数
        result['left_hand_target_2d_coefficients'] = calculate_2d_coefficients(
            left_hand_base_points, left_hand_target_locs)
        result['right_hand_target_2d_coefficients'] = calculate_2d_coefficients(
            right_hand_base_points, right_hand_target_locs)
        # 不使用四元数时，计算插值系数，因为如果使用四元数，到时候会直接使用slerp求解
        if not self.use_quaternion:
            result['left_hand_target_rotation_2d_coefficients'] = calculate_2d_coefficients(
                left_hand_base_points, left_hand_target_rots)
            result['right_hand_target_rotation_2d_coefficients'] = calculate_2d_coefficients(
                right_hand_base_points, right_hand_target_rots)

        return result

    def cacluate_hand_info(self, left_hand_item, right_hand_item, coefficients, ready: bool = False) -> dict:
        # 先初始化数据
        result = {}
        left_hand_note = left_hand_item.get("hand_note")
        right_hand_note = right_hand_item.get("hand_note")
        left_finger_pressed_count = 0
        right_finger_pressed_count = 0
        left_hand_white_key_value = 0
        right_hand_white_key_value = 0
        pressed_fingers = {}

        H_L_target_point = np.array(
            [left_hand_note, left_hand_white_key_value])
        H_R_target_point = np.array(
            [right_hand_note, right_hand_white_key_value])

        lowset_key_location = np.array(self.avatar_info["piano_info"][
            "lowest_white_key"].get('location'))
        highest_key_location = np.array(self.avatar_info["piano_info"][
            "highest_white_key"].get('location'))
        black_key_location = np.array(self.avatar_info["piano_info"][
            "black_key"].get('location'))
        press_distance = (highest_key_location - black_key_location)[2]

        # 统计哪些手指被按下，是黑键还是白键，以便于确实左右手的黑白键值
        for left_finger in left_hand_item.get("fingers"):
            if left_finger.get("pressed"):
                left_finger_pressed_count += 1
                pressed_fingers[left_finger["finger_index"]] = {
                    "position": left_finger["key_note"]["position"],
                    "note": left_finger["key_note"]["note"],
                    "is_black": left_finger["key_note"]["is_black"]
                }
                if left_finger["key_note"]["is_black"]:
                    left_hand_white_key_value = 1

        for right_finger in right_hand_item.get("fingers"):
            if right_finger.get("pressed"):
                right_finger_pressed_count += 1
                pressed_fingers[right_finger["finger_index"]] = {
                    "position": right_finger["key_note"]["position"],
                    "note": right_finger["key_note"]["note"],
                    "is_black": right_finger["key_note"]["is_black"]
                }
                if not right_finger["key_note"]["is_black"]:
                    right_hand_white_key_value = 1

        # 左手目标点位置
        Tar_H_L = evaluate_2d_point(
            coefficients["left_hand_target_2d_coefficients"], H_L_target_point)
        if left_finger_pressed_count > 0 and ready:
            Tar_H_L[2] += 0.5*press_distance
        result["Tar_H_L"] = Tar_H_L.tolist()

        # 右手目标点位置
        Tar_H_R = evaluate_2d_point(
            coefficients["right_hand_target_2d_coefficients"], H_R_target_point)
        if right_finger_pressed_count > 0 and ready:
            Tar_H_R[2] += 0.5*press_distance
        result["Tar_H_R"] = Tar_H_R.tolist()

        # 旋转值如果是euler，使用当前方法；如果是四元数，使用quaternion_interpolation_from_3_points
        if not self.use_quaternion:
            Tar_H_rotation_L = evaluate_2d_point(
                coefficients["left_hand_target_rotation_2d_coefficients"], H_L_target_point)

            Tar_H_rotation_R = evaluate_2d_point(
                coefficients["right_hand_target_rotation_2d_coefficients"], H_R_target_point)

        else:
            # 基于正弦值的插值方法
            left_hand_target_quaternions = [
                # 24位置，65度
                self.base_states['left_hand_target'][0]['rotation'],
                self.base_states['left_hand_target'][1]['rotation'],  # 52位置，0度
                # 76位置，-55度
                self.base_states['left_hand_target'][2]['rotation']
            ]

            if left_hand_note < 52:
                # 24位置(65度)到52位置(0度)
                # 手位置与sin值成线性关系
                sin_max = np.sin(np.radians(65))  # 24位置对应的sin值
                sin_current = (52 - left_hand_note) / \
                    (52 - 24) * sin_max  # 当前位置对应的sin值
                # 反推角度
                angle_rad = np.arcsin(sin_current)
                max_angle_rad = np.radians(65)
                left_hand_weight = angle_rad / max_angle_rad if max_angle_rad != 0 else 0
                Tar_H_rotation_L = slerp(
                    left_hand_target_quaternions[1], left_hand_target_quaternions[0], left_hand_weight)
            else:
                # 52位置(0度)到76位置(-55度)
                # 手位置与sin值成线性关系
                sin_max = np.sin(np.radians(55))  # 76位置对应的sin值
                sin_current = (left_hand_note - 52) / \
                    (76 - 52) * sin_max  # 当前位置对应的sin值
                # 反推角度
                angle_rad = np.arcsin(sin_current)
                max_angle_rad = np.radians(55)
                left_hand_weight = angle_rad / max_angle_rad if max_angle_rad != 0 else 0
                Tar_H_rotation_L = slerp(
                    left_hand_target_quaternions[1], left_hand_target_quaternions[2], left_hand_weight)

            # 这里计算Tar_H_R的旋转值，基于实际测量的角度值进行插值
            # 右手使用52-76-105三个位置，其中52位置为-55度，76位置为0度，105位置为65度
            right_hand_target_quaternions = [
                # 52位置，-55度
                self.base_states['right_hand_target'][0]['rotation'],
                # 76位置，0度
                self.base_states['right_hand_target'][1]['rotation'],
                # 105位置，65度
                self.base_states['right_hand_target'][2]['rotation']
            ]

            if right_hand_note < 76:
                # 52位置(-55度)到76位置(0度)
                # 手位置与sin值成线性关系
                sin_max = np.sin(np.radians(55))  # 52位置对应的sin值
                sin_current = (76 - right_hand_note) / \
                    (76 - 52) * sin_max  # 当前位置对应的sin值
                # 反推角度
                angle_rad = np.arcsin(sin_current)
                max_angle_rad = np.radians(55)
                right_hand_weight = angle_rad / max_angle_rad if max_angle_rad != 0 else 0
                Tar_H_rotation_R = slerp(
                    right_hand_target_quaternions[1], right_hand_target_quaternions[0], right_hand_weight)
            else:
                # 76位置(0度)到105位置(65度)
                # 手位置与sin值成线性关系
                sin_max = np.sin(np.radians(65))  # 105位置对应的sin值
                sin_current = (right_hand_note - 76) / \
                    (105 - 76) * sin_max  # 当前位置对应的sin值
                # 反推角度
                angle_rad = np.arcsin(sin_current)
                max_angle_rad = np.radians(65)
                right_hand_weight = angle_rad / max_angle_rad if max_angle_rad != 0 else 0
                Tar_H_rotation_R = slerp(
                    right_hand_target_quaternions[1], right_hand_target_quaternions[2], right_hand_weight)

        result["Tar_H_rotation_L"] = Tar_H_rotation_L.tolist()
        result["Tar_H_rotation_L"] = Tar_H_rotation_L.tolist()
        result["Tar_H_rotation_R"] = Tar_H_rotation_R.tolist()
        result["Tar_H_rotation_R"] = Tar_H_rotation_R.tolist()

        for finger_index in range(self.finger_count):
            if finger_index < 5:
                finger_position = evaluate_2d_point(
                    coefficients["finger_position_ball_2d_coefficients"][str(finger_index)], H_L_target_point)
            else:
                finger_position = evaluate_2d_point(
                    coefficients["finger_position_ball_2d_coefficients"][str(finger_index)], H_R_target_point)

            # 这一步是计算实际按键的手指位置
            if finger_index in pressed_fingers:
                note = pressed_fingers[finger_index]["note"]
                is_black = pressed_fingers[finger_index]["is_black"]

                key_location = get_key_location(
                    note, is_black, self.piano, lowset_key_location, highest_key_location, black_key_location)
                touch_point = get_touch_point(finger_position, key_location)
                if not ready:  # 如果不是ready说明是已经按键下去了，需要在z轴上添加一段移动距离，也许实际按键的方向并不是z轴，以后可以再修改
                    touch_point[2] += press_distance
                result[f"{finger_index}"] = touch_point.tolist()
            else:
                result[f"{finger_index}"] = finger_position.tolist()

        return result
