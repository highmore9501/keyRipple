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

        # 定义时间参数（以帧为单位）
        press_duration = self.fps / 10           # 0.1秒按下耗时
        up_duration = press_duration * 1.5       # 0.15秒抬起耗时
        hand_move_duration = press_duration * 2  # 0.2秒手掌移动时间

        for i in range(recorder_number):
            item = self.hand_recorder[i]
            next_item = self.hand_recorder[i +
                                           1] if i + 1 < recorder_number else None
            current_frame = item.get("frame")
            next_frame = next_item.get("frame") if next_item else None

            left_hand_item = item.get("left_hand")
            right_hand_item = item.get("right_hand")

            # 预备动作 - 提前press_duration秒到达预备位置（如果时间允许）
            prepare_frame = current_frame - press_duration
            # 只有当不是第一个音符或者距离上一个音符有足够时间时才添加预备动作
            if i == 0 or (current_frame - self.hand_recorder[i-1].get("frame")) >= press_duration:
                prepare_info = self.cacluate_hand_info(
                    left_hand_item, right_hand_item, coefficients, True)
                animation_data.append({
                    "frame": prepare_frame,
                    "hand_infos": prepare_info
                })

            # 按下动作 - 在当前帧按下（必须有）
            press_info = self.cacluate_hand_info(
                left_hand_item, right_hand_item, coefficients, False)
            animation_data.append({
                "frame": current_frame,
                "hand_infos": press_info
            })

            # 处理抬起动作和保持动作
            if next_frame:
                # 计算抬起开始时间（下一帧前up_duration+hand_move_duration秒）
                release_start_frame = next_frame - up_duration - hand_move_duration

                # 如果有足够时间保持按下状态
                if current_frame + press_duration <= release_start_frame:
                    # 保持动作 - 保持按下状态（优先级：低）
                    hold_frame = release_start_frame - press_duration  # 在抬起前保持一小段时间
                    animation_data.append({
                        "frame": hold_frame,
                        "hand_infos": press_info
                    })

                # 抬起动作 - 使用up_duration时间抬起（必须有）
                # 抬起过程中使用预备状态（手抬起）
                release_info = self.cacluate_hand_info(
                    left_hand_item, right_hand_item, coefficients, True)

                # 抬起开始帧
                animation_data.append({
                    "frame": release_start_frame,
                    "hand_infos": release_info
                })

                # 抬起结束帧
                release_end_frame = release_start_frame + up_duration
                animation_data.append({
                    "frame": release_end_frame,
                    "hand_infos": release_info
                })
            else:
                # 最后一个音符的处理
                # 保持一小段时间后抬起
                hold_frame = current_frame + press_duration * 2
                animation_data.append({
                    "frame": hold_frame,
                    "hand_infos": press_info
                })

                # 抬起动作
                release_start_frame = hold_frame + press_duration
                release_info = self.cacluate_hand_info(
                    left_hand_item, right_hand_item, coefficients, True)
                animation_data.append({
                    "frame": release_start_frame,
                    "hand_infos": release_info
                })

                # 抬起结束
                release_end_frame = release_start_frame + up_duration
                animation_data.append({
                    "frame": release_end_frame,
                    "hand_infos": release_info
                })

        # 按帧号排序
        animation_data.sort(key=lambda x: x["frame"])

        # 合并相同帧的数据，保留最后一个
        final_animation_data = []
        if animation_data:
            current_frame_data = animation_data[0]
            for i in range(1, len(animation_data)):
                if animation_data[i]["frame"] == current_frame_data["frame"]:
                    # 合并相同帧的数据
                    current_frame_data = animation_data[i]
                else:
                    final_animation_data.append(current_frame_data)
                    current_frame_data = animation_data[i]
            final_animation_data.append(current_frame_data)

        file_path = f"output/animation_recorders/{self.midi_name}_{self.avatar_name}.animation"
        with open(file_path, "w") as f:
            json.dump(final_animation_data, f)

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
                finger_position[2] = black_key_location[2]  # 不参与演奏的手指，高度不能低于黑键
                result[f"{finger_index}"] = finger_position.tolist()

        return result
