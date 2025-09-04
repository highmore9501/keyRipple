import json
from src.utils import lerp_with_key_type_and_position, get_key_location, get_touch_point, get_actual_press_depth
from src.piano.piano import Piano
import numpy as np
from mathutils import Vector, Quaternion
from typing import Any
from enum import Enum


class ActionPhase(Enum):
    REST = "rest"
    READY = "ready"
    ATTACK = "attack"
    HOLD = "hold"


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
                self.config = self.avatar_info.get("config", {})

            print(f'已加载{hand_recorder_path} 和 {avatar_info_path}')
        except Exception as e:
            print(e)

    def determine_hand_white_key_value(self, hand_fingers: list, is_left: bool = True) -> int:
        """
        确定手部的white_key_value，用于动画计算

        Args:
            hand_fingers: 手部手指列表
            is_left: 是否为左手，默认为True

        Returns:
            int: white_key_value (0或1)
        """
        thumb_finger_index = 4 if is_left else 5
        white_key_value = 1

        for finger in hand_fingers:
            if finger.get("pressed"):
                # 检查是否为拇指且按的是黑键
                if (finger["key_note"]["is_black"] and
                        finger.get("finger_index") == thumb_finger_index):
                    white_key_value = 0
                    break

        return white_key_value

    def prossess_hand_data(self, recorders: list[Any], press_duration: float = 0.1, up_duration: float = 0.1, hand_move_duration: float = 0.1):
        animation_data = []

        for i in range(len(recorders)):
            recorder = recorders[i]
            next_recorder = recorders[i +
                                      1] if i + 1 < len(recorders) else None
            current_frame = recorder.get("frame")

            current_is_left = recorder.get(
                "left_hand", None) is not None
            hand_item = recorder.get(
                "left_hand") if current_is_left else recorder.get("right_hand")
            hand_white_key_value = self.determine_hand_white_key_value(
                hand_item.get("fingers"), current_is_left)

            final_hand_white_key_value = hand_white_key_value
            next_rest_info = None
            next_ready_info = None
            next_frame = None

            if next_recorder is not None:
                next_frame = next_recorder.get("frame")
                next_hand_item = next_recorder.get(
                    "left_hand") if current_is_left else next_recorder.get("right_hand")
                next_hand_white_key_value = self.determine_hand_white_key_value(
                    next_hand_item.get("fingers"), current_is_left)
                final_hand_white_key_value = hand_white_key_value * \
                    next_hand_white_key_value
                next_hand_info = self.cacluate_hand_info(
                    next_hand_item, current_is_left, next_hand_white_key_value)
                next_rest_info = next_hand_info[ActionPhase.REST]
                next_ready_info = next_hand_info[ActionPhase.READY]

            # 预备或抬起动作
            current_hand_info = self.cacluate_hand_info(
                hand_item, current_is_left, final_hand_white_key_value)
            ready_info = current_hand_info[ActionPhase.READY]

            # 按下动作
            attack_info = current_hand_info[ActionPhase.ATTACK]

            # 保持按下动作
            hold_info = current_hand_info[ActionPhase.HOLD]

            # 休息动作
            rest_info = current_hand_info[ActionPhase.REST]

            #  如果是第一个手型，需要添加一个预备动作
            if i == 0:
                # 预备动作 - 提前press_duration秒到达预备位置（如果时间允许）
                rest_frame = current_frame - press_duration
                animation_data.append({
                    "frame": rest_frame,
                    "hand_infos": ready_info
                })

            # 按下动作 - 在当前帧按下（必须有）
            animation_data.append({
                "frame": current_frame,
                "hand_infos": attack_info
            })

            if next_frame is None:  # 如果没有下一个手型，就跳过
                continue

            # 如果两个手型之间的时间小于等于移动+按下，也就是press_duration，那就干脆不要有中间动作
            if next_frame-current_frame <= press_duration:
                continue

            # 能运行到这里就是有足够的时间移动+按下，那么就在下一个指法之前插入一个预备帧，时间为next_frame - press_duration
            next_ready_frame = next_frame - press_duration
            # 如果没有 enough time to insert prepare frame, skip it
            if next_ready_frame is not None and next_ready_info is not None:
                animation_data.append({
                    "frame": next_ready_frame,
                    "hand_infos": next_ready_info
                })

            # 如果时间不够插入下一个手型的休息帧，那么到这里就结束
            if next_frame-current_frame <= press_duration+up_duration:
                continue

            rest_frame = next_frame - \
                press_duration - up_duration

            if rest_frame is not None:
                animation_data.append({
                    "frame": rest_frame,
                    "hand_infos": next_rest_info
                })

            # 如果时间不够再多插入保持按下状态的帧，那么到这里也结束
            if next_frame-current_frame <= hand_move_duration + press_duration + up_duration:
                continue

            # 时间仍然充足，添加一个hold状态的帧

            hold_end_frame = next_frame - press_duration - hand_move_duration - up_duration
            animation_data.append({
                "frame": hold_end_frame,
                "hand_infos": hold_info
            })

            # 时间再够的话，再添加一个hold开始的帧
            if next_frame-current_frame <= hand_move_duration + press_duration + 2 * up_duration:
                continue

            hold_start_frame = current_frame + up_duration
            animation_data.append({
                "frame": hold_start_frame,
                "hand_infos": hold_info
            })

        return animation_data

    def generate_animation_info(self):
        # 定义时间参数（以帧为单位）
        press_duration = self.fps / 20          # 按下耗时
        up_duration = press_duration * 1.2       # 抬起耗时
        hand_move_duration = press_duration * 4  # 手掌移动时间

        left_hand_recorders = []
        right_hand_recorders = []

        # 先分成左右手两个列表
        for item in self.hand_recorder:
            left_hand_item = item.get("left_hand", None)
            right_hand_item = item.get("right_hand", None)
            if left_hand_item is not None:
                left_hand_recorders.append(item)
            elif right_hand_item is not None:
                right_hand_recorders.append(item)
            else:
                print("Error: hand_item is None")

        left_hand_animation_data = self.prossess_hand_data(
            left_hand_recorders, press_duration, up_duration, hand_move_duration)

        right_hand_animation_data = self.prossess_hand_data(
            right_hand_recorders, press_duration, up_duration, hand_move_duration)

        animation_data = left_hand_animation_data + right_hand_animation_data
        # 按帧号排序
        animation_data.sort(key=lambda x: x["frame"])

        file_path = f"output/animation_recorders/{self.midi_name}_{self.avatar_name}.animation"
        with open(file_path, "w") as f:
            json.dump(animation_data, f)

        print(f"动画数据已保存到{file_path}")

    def cacluate_hand_info(self, hand_item: Any, is_left: bool = True, hand_white_key_value: int = 1) -> dict:
        # 先初始化数据
        result = {}
        result[ActionPhase.REST] = {}
        result[ActionPhase.READY] = {}
        result[ActionPhase.ATTACK] = {}
        result[ActionPhase.HOLD] = {}

        hand_note = hand_item.get("hand_note")
        hand_span = max(8, hand_item.get("hand_span"))

        span_offset = np.array(self.avatar_info["key_board_positions"]["wide_expand_hand_position"].get(
            'location')) - np.array(self.avatar_info["key_board_positions"]["normal_hand_expand_position"].get('location'))
        span_offset[0] = 0.0  # 去掉手掌扩张时在x轴方向上的位移

        lowset_key_location = np.array(self.avatar_info["key_board_positions"][
            "lowest_white_key_position"].get('location'))
        highest_key_location = np.array(self.avatar_info["key_board_positions"][
            "highest_white_key_position"].get('location'))
        black_key_location = np.array(self.avatar_info["key_board_positions"][
            "black_key_position"].get('location'))
        press_distance = (black_key_location-highest_key_location)[2]

        leftest_position: int = self.avatar_info['config']['leftest_position']
        left_position: int = self.avatar_info['config']['left_position']
        middle_left_position: int = self.avatar_info['config']['middle_left_position']
        middle_right_position: int = self.avatar_info['config']['middle_right_position']
        right_position: int = self.avatar_info['config']['right_position']
        rightest_position: int = self.avatar_info['config']['rightest_position']

        high_position = right_position if is_left else rightest_position
        middle_position = middle_left_position if is_left else middle_right_position
        low_position = leftest_position if is_left else left_position

        suffix = "L" if is_left else "R"
        # 手掌位置
        hand_recorder = self.avatar_info['hand_recorders'][
            'left_hand_recorders'] if is_left else self.avatar_info['hand_recorders']['right_hand_recorders']

        high_white = np.array(
            hand_recorder[f'high_white_H_{suffix}'].get('location'))
        high_black = np.array(
            hand_recorder[f'high_black_H_{suffix}'].get('location'))
        middle_white = np.array(
            hand_recorder[f'middle_white_H_{suffix}'].get('location'))
        middle_black = np.array(
            hand_recorder[f'middle_black_H_{suffix}'].get('location'))
        low_white = np.array(
            hand_recorder[f'low_white_H_{suffix}'].get('location'))
        low_black = np.array(
            hand_recorder[f'low_black_H_{suffix}'].get('location'))
        hand_position = lerp_with_key_type_and_position(
            hand_white_key_value,
            hand_note,
            high_position,
            middle_position,
            low_position,
            high_white,
            high_black,
            middle_white,
            middle_black,
            low_white, low_black
        )

        # 根据当前左手跨度，判断是否要调整位置
        hand_span_weight = (hand_span - 8) / (12 - 8)
        hand_position += hand_span_weight * span_offset
        attack_hand_position = hand_position.copy()
        attack_hand_position[2] += 0.5 * press_distance
        hold_hand_position = hand_position.copy()
        hold_hand_position[2] += 0.25 * press_distance
        # 生成四个阶段不同的手掌位置
        result[ActionPhase.REST][f"H_{suffix}"] = hand_position.tolist()
        result[ActionPhase.READY][f"H_{suffix}"] = hand_position.tolist()
        result[ActionPhase.ATTACK][f"H_{suffix}"] = attack_hand_position.tolist(
        )
        result[ActionPhase.HOLD][f"H_{suffix}"] = hold_hand_position.tolist()

        # 左手pivot位置
        HP_high_white = np.array(
            hand_recorder[f'high_white_HP_{suffix}'].get('location'))
        HP_high_black = np.array(
            hand_recorder[f'high_black_HP_{suffix}'].get('location'))
        HP_middle_white = np.array(
            hand_recorder[f'middle_white_HP_{suffix}'].get('location'))
        HP_middle_black = np.array(
            hand_recorder[f'middle_black_HP_{suffix}'].get('location'))
        HP_low_white = np.array(
            hand_recorder[f'low_white_HP_{suffix}'].get('location'))
        HP_low_black = np.array(
            hand_recorder[f'low_black_HP_{suffix}'].get('location'))
        HP = lerp_with_key_type_and_position(
            hand_white_key_value,
            hand_note,
            high_position,
            middle_position,
            low_position,
            HP_high_white,
            HP_high_black,
            HP_middle_white,
            HP_middle_black,
            HP_low_white,
            HP_low_black
        )
        result[ActionPhase.REST][f"HP_{suffix}"] = HP.tolist()
        result[ActionPhase.READY][f"HP_{suffix}"] = HP.tolist()
        result[ActionPhase.ATTACK][f"HP_{suffix}"] = HP.tolist()
        result[ActionPhase.HOLD][f"HP_{suffix}"] = HP.tolist()

        # 左手旋转值
        H_rotation_high_white = np.array(
            hand_recorder[f'high_white_H_rotation_{suffix}'].get('rotation_quaternion'))
        H_rotation_high_black = np.array(
            hand_recorder[f'high_black_H_rotation_{suffix}'].get('rotation_quaternion'))
        H_rotation_middle_white = np.array(
            hand_recorder[f'middle_white_H_rotation_{suffix}'].get('rotation_quaternion'))
        H_rotation_middle_black = np.array(
            hand_recorder[f'middle_black_H_rotation_{suffix}'].get('rotation_quaternion'))
        H_rotation_low_white = np.array(
            hand_recorder[f'low_white_H_rotation_{suffix}'].get('rotation_quaternion'))
        H_rotation_low_black = np.array(
            hand_recorder[f'low_black_H_rotation_{suffix}'].get('rotation_quaternion'))
        H_rotation = lerp_with_key_type_and_position(
            hand_white_key_value,
            hand_note,
            high_position,
            middle_position,
            low_position,
            H_rotation_high_white,
            H_rotation_high_black,
            H_rotation_middle_white,
            H_rotation_middle_black,
            H_rotation_low_white,
            H_rotation_low_black
        )

        result[ActionPhase.REST][f"H_rotation_{suffix}"] = H_rotation.tolist()
        result[ActionPhase.READY][f"H_rotation_{suffix}"] = H_rotation.tolist()
        result[ActionPhase.ATTACK][f"H_rotation_{suffix}"] = H_rotation.tolist(
        )
        result[ActionPhase.HOLD][f"H_rotation_{suffix}"] = H_rotation.tolist()

        finger_recorders = self.avatar_info['finger_recorders'][
            'left_finger_recorders'] if is_left else self.avatar_info['finger_recorders']['right_finger_recorders']

        fingers = hand_item.get("fingers", [])

        for finger in fingers:
            finger_index = finger.get("finger_index")
            finger_high_white_key = f'high_white_{finger_index}_{suffix}'
            finger_high_white = np.array(
                finger_recorders[finger_high_white_key].get('location'))
            finger_high_black_key = f'high_black_{finger_index}_{suffix}'
            finger_high_black = np.array(
                finger_recorders[finger_high_black_key].get('location'))
            finger_middle_white_key = f'middle_white_{finger_index}_{suffix}'
            finger_middle_white = np.array(
                finger_recorders[finger_middle_white_key].get('location'))
            finger_middle_black_key = f'middle_black_{finger_index}_{suffix}'
            finger_middle_black = np.array(
                finger_recorders[finger_middle_black_key].get('location'))
            finger_low_white_key = f'low_white_{finger_index}_{suffix}'
            finger_low_white = np.array(
                finger_recorders[finger_low_white_key].get('location'))
            finger_low_black_key = f'low_black_{finger_index}_{suffix}'
            finger_low_black = np.array(
                finger_recorders[finger_low_black_key].get('location'))
            finger_position = lerp_with_key_type_and_position(
                hand_white_key_value, hand_note, high_position, middle_position, low_position, finger_high_white, finger_high_black, finger_middle_white, finger_middle_black, finger_low_white, finger_low_black)

            # 这一步是计算实际按键的手指位置
            note = finger["key_note"]["note"]
            is_black = finger["key_note"]["is_black"]
            is_pressed = finger["pressed"]

            key_location = get_key_location(
                note, finger_index, is_pressed, is_black, self.piano, lowset_key_location, highest_key_location, black_key_location)
            touch_point = get_touch_point(
                finger_position, key_location)

            base_vector = Vector((0, 0, 1))
            press_key_direction_q = self.avatar_info['guidelines']['press_key_direction'].get(
                'rotation_quaternion')
            press_key_direction = Quaternion(
                press_key_direction_q) @ base_vector
            # 确保方向向量单位化
            press_key_direction = press_key_direction / \
                np.linalg.norm(press_key_direction)

            is_keep_pressed = finger["is_keep_pressed"]
            actual_press_depth = get_actual_press_depth(
                lowset_key_location, finger_position)
            finger_key = f"{finger_index}_{suffix}"

            ready_touch_point = touch_point - 0.75 * \
                actual_press_depth * press_key_direction
            attack_touch_point = touch_point + actual_press_depth * press_key_direction

            if not is_keep_pressed and is_pressed:  # 普通按键
                result[ActionPhase.REST][finger_key] = touch_point.tolist()
                result[ActionPhase.READY][finger_key] = ready_touch_point.tolist()
                result[ActionPhase.ATTACK][finger_key] = attack_touch_point.tolist()
                result[ActionPhase.HOLD][finger_key] = attack_touch_point.tolist()
            elif is_keep_pressed:  # 保留指按键
                result[ActionPhase.REST][finger_key] = attack_touch_point.tolist()
                result[ActionPhase.READY][finger_key] = attack_touch_point.tolist()
                result[ActionPhase.ATTACK][finger_key] = attack_touch_point.tolist()
                result[ActionPhase.HOLD][finger_key] = attack_touch_point.tolist()
            else:  # 不按键
                result[ActionPhase.REST][finger_key] = touch_point.tolist()
                result[ActionPhase.READY][finger_key] = touch_point.tolist()
                result[ActionPhase.ATTACK][finger_key] = touch_point.tolist()
                result[ActionPhase.HOLD][finger_key] = touch_point.tolist()

        return result
