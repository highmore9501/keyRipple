import json
from src.utils import lerp_with_key_type_and_position, get_key_location, get_touch_point, get_actual_press_depth
from src.piano.piano import Piano
import numpy as np
from mathutils import Vector, Quaternion
from typing import Any


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

    def generate_animation_info(self):
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

            # 这里是判断当前手型是否要使用黑键手型，只要当前是或者下一个手型是，那就使用黑键手型
            hand_item = item.get("left_hand", None) if item.get(
                "left_hand", None) is not None else item.get("right_hand")
            current_is_left = item.get(
                "left_hand", None) is not None
            next_is_left = next_item.get(
                "left_hand", None) is not None if next_item else None
            next_hand_item = next_item.get(
                "left_hand") if next_item is not None and next_item.get(
                "left_hand") is not None else next_item.get("right_hand") if next_item is not None else None

            hand_white_key_value = self.determine_hand_white_key_value(
                hand_item.get("fingers"), current_is_left)

            #  这一步是判断下面的手是否是同一个手，而且当前手和下一个手中只要一个有黑键状态，那么当前手就使用黑键，这样可以减少手的抖动
            if next_hand_item is not None and current_is_left == next_is_left:
                next_hand_white_key_value = self.determine_hand_white_key_value(
                    next_hand_item.get("fingers"), current_is_left)
                hand_white_key_value = hand_white_key_value * \
                    next_hand_white_key_value

            # 预备动作 - 提前press_duration秒到达预备位置（如果时间允许）
            prepare_frame = current_frame - press_duration
            # 只有当不是第一个音符或者距离上一个音符有足够时间时才添加预备动作
            if prepare_frame > 0 and (current_frame - self.hand_recorder[i-1].get("frame")) >= press_duration:
                prepare_info = self.cacluate_hand_info(
                    hand_item, current_is_left, True, hand_white_key_value)
                animation_data.append({
                    "frame": prepare_frame,
                    "hand_infos": prepare_info
                })

            # 按下动作 - 在当前帧按下（必须有）
            press_info = self.cacluate_hand_info(
                hand_item, current_is_left, False, hand_white_key_value)
            animation_data.append({
                "frame": current_frame,
                "hand_infos": press_info
            })

            # 处理抬起动作和保持动作
            if next_frame is not None and current_is_left == next_is_left:
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
                    hand_item, current_is_left, True, hand_white_key_value)

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
                    hand_item, current_is_left, True, hand_white_key_value)
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

        file_path = f"output/animation_recorders/{self.midi_name}_{self.avatar_name}.animation"
        with open(file_path, "w") as f:
            json.dump(animation_data, f)

        print(f"动画数据已保存到{file_path}")

    def cacluate_hand_info(self, hand_item: Any, is_left: bool = True, ready: bool = False, hand_white_key_value: int = 1) -> dict:
        # 先初始化数据
        result = {}
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
        press_distance = (highest_key_location - black_key_location)[2]

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
        # 根据当前左手是否按下，判断是否要调整位置
        if ready:
            hand_position[2] += 0.5 * press_distance
        result[f"H_{suffix}"] = hand_position.tolist()

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
        result[f"HP_{suffix}"] = HP.tolist()

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

        result[f"H_rotation_{suffix}"] = H_rotation.tolist()

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
            if (not ready and is_pressed) or is_keep_pressed:  # 如果不是ready说明是已经按键下去了，需要在z轴上添加一段按键距离
                touch_point += actual_press_depth * press_key_direction
                result[finger_key] = touch_point.tolist()
            else:
                touch_point -= actual_press_depth * \
                    press_key_direction  # 没有按键的时候，手指抬起来
                result[finger_key] = touch_point.tolist()

        return result
