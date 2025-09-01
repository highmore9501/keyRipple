import json
from src.utils import lerp_with_key_type_and_position, get_key_location, get_touch_point, get_actual_press_depth
from src.piano.piano import Piano
import numpy as np
from mathutils import Vector, Quaternion


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
            left_hand_item = item.get("left_hand")
            left_hand_white_key_value = self.determine_hand_white_key_value(
                left_hand_item.get("fingers"))
            next_left_hand_item = next_item.get(
                "left_hand") if next_item else None
            if next_left_hand_item:
                next_left_hand_white_key_value = self.determine_hand_white_key_value(
                    next_left_hand_item.get("fingers"))
                left_hand_white_key_value = left_hand_white_key_value * \
                    next_left_hand_white_key_value

            right_hand_item = item.get("right_hand")
            right_hand_white_key_value = self.determine_hand_white_key_value(
                right_hand_item.get("fingers"))
            next_right_hand_item = next_item.get(
                "right_hand") if next_item else None

            if next_right_hand_item:
                next_right_hand_white_key_value = self.determine_hand_white_key_value(
                    next_right_hand_item.get("fingers"))
                right_hand_white_key_value = right_hand_white_key_value * \
                    next_right_hand_white_key_value

            # 预备动作 - 提前press_duration秒到达预备位置（如果时间允许）
            prepare_frame = current_frame - press_duration
            # 只有当不是第一个音符或者距离上一个音符有足够时间时才添加预备动作
            if i == 0 or (current_frame - self.hand_recorder[i-1].get("frame")) >= press_duration:
                prepare_info = self.cacluate_hand_info(
                    left_hand_item, right_hand_item, True, left_hand_white_key_value, right_hand_white_key_value)
                animation_data.append({
                    "frame": prepare_frame,
                    "hand_infos": prepare_info
                })

            # 按下动作 - 在当前帧按下（必须有）
            press_info = self.cacluate_hand_info(
                left_hand_item, right_hand_item, False, left_hand_white_key_value, right_hand_white_key_value)
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
                    left_hand_item, right_hand_item, True, left_hand_white_key_value, right_hand_white_key_value)

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
                    left_hand_item, right_hand_item, True, left_hand_white_key_value, right_hand_white_key_value)
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

    def cacluate_hand_info(self, left_hand_item, right_hand_item, ready: bool = False, left_hand_white_key_value: int = 1, right_hand_white_key_value: int = 1) -> dict:
        # 先初始化数据
        result = {}
        left_hand_note = left_hand_item.get("hand_note")
        left_hand_span = max(8, left_hand_item.get("hand_span"))
        right_hand_note = right_hand_item.get("hand_note")
        right_hand_span = max(8, right_hand_item.get("hand_span"))

        span_offset = np.array(self.avatar_info["key_board_positions"]["wide_expand_hand_position"].get(
            'location')) - np.array(self.avatar_info["key_board_positions"]["normal_hand_expand_position"].get('location'))
        span_offset[0] = 0.0  # 去掉手掌扩张时在x轴方向上的位移

        left_finger_pressed_count = 0
        right_finger_pressed_count = 0
        all_fingers = {}

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

        # 统计哪些手指被按下，是黑键还是白键，以便于确实左右手的黑白键值
        for left_finger in left_hand_item.get("fingers"):
            all_fingers[left_finger["finger_index"]] = {
                "position": left_finger["key_note"]["position"],
                "note": left_finger["key_note"]["note"],
                "is_black": left_finger["key_note"]["is_black"],
                "is_pressed": left_finger.get("pressed"),
                "is_keep_pressed": left_finger.get("is_keep_pressed")
            }

        for right_finger in right_hand_item.get("fingers"):
            all_fingers[right_finger["finger_index"]] = {
                "position": right_finger["key_note"]["position"],
                "note": right_finger["key_note"]["note"],
                "is_black": right_finger["key_note"]["is_black"],
                "is_pressed": right_finger.get("pressed"),
                "is_keep_pressed": right_finger.get("is_keep_pressed")
            }

        # 左手位置
        left_hand_recorder = self.avatar_info['hand_recorders']['left_hand_recorders']
        HL_high_white = np.array(
            left_hand_recorder['high_white_H_L'].get('location'))
        HL_high_black = np.array(
            left_hand_recorder['high_black_H_L'].get('location'))
        HL_middle_white = np.array(
            left_hand_recorder['middle_white_H_L'].get('location'))
        HL_middle_black = np.array(
            left_hand_recorder['middle_black_H_L'].get('location'))
        HL_low_white = np.array(
            left_hand_recorder['low_white_H_L'].get('location'))
        HL_low_black = np.array(
            left_hand_recorder['low_black_H_L'].get('location'))
        H_L = lerp_with_key_type_and_position(left_hand_white_key_value, left_hand_note,  right_position, middle_left_position,
                                              leftest_position, HL_high_white, HL_high_black, HL_middle_white, HL_middle_black, HL_low_white, HL_low_black)

        # 根据当前左手跨度，判断是否要调整位置
        left_hand_span_weight = (left_hand_span - 8) / (12 - 8)
        H_L += left_hand_span_weight*span_offset
        # 根据当前左手是否按下，判断是否要调整位置
        if left_finger_pressed_count > 0 and ready:
            H_L[2] += 0.5*press_distance
        result["H_L"] = H_L.tolist()

        # 左手pivot位置
        HP_L_high_white = np.array(
            left_hand_recorder['high_white_HP_L'].get('location'))
        HP_L_high_black = np.array(
            left_hand_recorder['high_black_HP_L'].get('location'))
        HP_L_middle_white = np.array(
            left_hand_recorder['middle_white_HP_L'].get('location'))
        HP_L_middle_black = np.array(
            left_hand_recorder['middle_black_HP_L'].get('location'))
        HP_L_low_white = np.array(
            left_hand_recorder['low_white_HP_L'].get('location'))
        HP_L_low_black = np.array(
            left_hand_recorder['low_black_HP_L'].get('location'))
        HP_L = lerp_with_key_type_and_position(left_hand_white_key_value, left_hand_note, right_position, middle_left_position,
                                               leftest_position, HP_L_high_white, HP_L_high_black, HP_L_middle_white, HP_L_middle_black, HP_L_low_white, HP_L_low_black)
        result["HP_L"] = HP_L.tolist()

        # 左手旋转值
        H_rotation_L_high_white = np.array(
            left_hand_recorder['high_white_H_rotation_L'].get('rotation_quaternion'))
        H_rotation_L_high_black = np.array(
            left_hand_recorder['high_black_H_rotation_L'].get('rotation_quaternion'))
        H_rotation_L_middle_white = np.array(
            left_hand_recorder['middle_white_H_rotation_L'].get('rotation_quaternion'))
        H_rotation_L_middle_black = np.array(
            left_hand_recorder['middle_black_H_rotation_L'].get('rotation_quaternion'))
        H_rotation_L_low_white = np.array(
            left_hand_recorder['low_white_H_rotation_L'].get('rotation_quaternion'))
        H_rotation_L_low_black = np.array(
            left_hand_recorder['low_black_H_rotation_L'].get('rotation_quaternion'))
        H_rotation_L = lerp_with_key_type_and_position(white_key_value=left_hand_white_key_value, position=left_hand_note, high_position=right_position, middle_position=middle_left_position, low_position=leftest_position,
                                                       high_white=H_rotation_L_high_white, high_black=H_rotation_L_high_black, middle_white=H_rotation_L_middle_white, middle_black=H_rotation_L_middle_black, low_white=H_rotation_L_low_white, low_black=H_rotation_L_low_black)

        result["H_rotation_L"] = H_rotation_L.tolist()

        # 右手位置
        right_hand_recorder = self.avatar_info['hand_recorders']['right_hand_recorders']
        HR_high_white = np.array(
            right_hand_recorder['high_white_H_R'].get('location'))
        HR_high_black = np.array(
            right_hand_recorder['high_black_H_R'].get('location'))
        HR_middle_white = np.array(
            right_hand_recorder['middle_white_H_R'].get('location'))
        HR_middle_black = np.array(
            right_hand_recorder['middle_black_H_R'].get('location'))
        HR_low_white = np.array(
            right_hand_recorder['low_white_H_R'].get('location'))
        HR_low_black = np.array(
            right_hand_recorder['low_black_H_R'].get('location'))
        H_R = lerp_with_key_type_and_position(right_hand_white_key_value, right_hand_note, rightest_position, middle_right_position,
                                              left_position, HR_high_white, HR_high_black, HR_middle_white, HR_middle_black, HR_low_white, HR_low_black)
        right_hand_span_weight = (right_hand_span - 8) / (12 - 8)
        H_R += right_hand_span_weight*span_offset
        if right_finger_pressed_count > 0 and ready:
            H_R[2] += 0.5*press_distance
        result["H_R"] = H_R.tolist()

        # 右手pivot位置
        HP_R_high_white = np.array(
            right_hand_recorder['high_white_HP_R'].get('location'))
        HP_R_high_black = np.array(
            right_hand_recorder['high_black_HP_R'].get('location'))
        HP_R_middle_white = np.array(
            right_hand_recorder['middle_white_HP_R'].get('location'))
        HP_R_middle_black = np.array(
            right_hand_recorder['middle_black_HP_R'].get('location'))
        HP_R_low_white = np.array(
            right_hand_recorder['low_white_HP_R'].get('location'))
        HP_R_low_black = np.array(
            right_hand_recorder['low_black_HP_R'].get('location'))
        HP_R = lerp_with_key_type_and_position(right_hand_white_key_value, right_hand_note, rightest_position, middle_right_position,
                                               left_position, HP_R_high_white, HP_R_high_black, HP_R_middle_white, HP_R_middle_black, HP_R_low_white, HP_R_low_black)
        result["HP_R"] = HP_R.tolist()

        # 右手旋转值
        H_rotation_R_high_white = np.array(
            right_hand_recorder['high_white_H_rotation_R'].get('rotation_quaternion'))
        H_rotation_R_high_black = np.array(
            right_hand_recorder['high_black_H_rotation_R'].get('rotation_quaternion'))
        H_rotation_R_middle_white = np.array(
            right_hand_recorder['middle_white_H_rotation_R'].get('rotation_quaternion'))
        H_rotation_R_middle_black = np.array(
            right_hand_recorder['middle_black_H_rotation_R'].get('rotation_quaternion'))
        H_rotation_R_low_white = np.array(
            right_hand_recorder['low_white_H_rotation_R'].get('rotation_quaternion'))
        H_rotation_R_low_black = np.array(
            right_hand_recorder['low_black_H_rotation_R'].get('rotation_quaternion'))
        H_rotation_R = lerp_with_key_type_and_position(right_hand_white_key_value, right_hand_note, rightest_position, middle_right_position,
                                                       left_position, H_rotation_R_high_white, H_rotation_R_high_black, H_rotation_R_middle_white, H_rotation_R_middle_black, H_rotation_R_low_white, H_rotation_R_low_black)
        result["H_rotation_R"] = H_rotation_R.tolist()

        # 计算手指位置
        for finger_index in range(self.finger_count):
            if finger_index < 5:
                left_finger_recorders = self.avatar_info['finger_recorders']['left_finger_recorders']
                left_finger_high_white_key = f'high_white_{finger_index}_L'
                left_finger_high_white = np.array(
                    left_finger_recorders[left_finger_high_white_key].get('location'))
                left_finger_high_black_key = f'high_black_{finger_index}_L'
                left_finger_high_black = np.array(
                    left_finger_recorders[left_finger_high_black_key].get('location'))
                left_finger_middle_white_key = f'middle_white_{finger_index}_L'
                left_finger_middle_white = np.array(
                    left_finger_recorders[left_finger_middle_white_key].get('location'))
                left_finger_middle_black_key = f'middle_black_{finger_index}_L'
                left_finger_middle_black = np.array(
                    left_finger_recorders[left_finger_middle_black_key].get('location'))
                left_finger_low_white_key = f'low_white_{finger_index}_L'
                left_finger_low_white = np.array(
                    left_finger_recorders[left_finger_low_white_key].get('location'))
                left_finger_low_black_key = f'low_black_{finger_index}_L'
                left_finger_low_black = np.array(
                    left_finger_recorders[left_finger_low_black_key].get('location'))
                finger_position = lerp_with_key_type_and_position(
                    left_hand_white_key_value, left_hand_note, right_position, middle_left_position, leftest_position, left_finger_high_white, left_finger_high_black, left_finger_middle_white, left_finger_middle_black, left_finger_low_white, left_finger_low_black)
            else:
                right_finger_recorders = self.avatar_info['finger_recorders']['right_finger_recorders']
                right_finger_high_white_key = f'high_white_{finger_index}_R'
                right_finger_high_white = np.array(
                    right_finger_recorders[right_finger_high_white_key].get('location'))
                right_finger_high_black_key = f'high_black_{finger_index}_R'
                right_finger_high_black = np.array(
                    right_finger_recorders[right_finger_high_black_key].get('location'))
                right_finger_middle_white_key = f'middle_white_{finger_index}_R'
                right_finger_middle_white = np.array(
                    right_finger_recorders[right_finger_middle_white_key].get('location'))
                right_finger_middle_black_key = f'middle_black_{finger_index}_R'
                right_finger_middle_black = np.array(
                    right_finger_recorders[right_finger_middle_black_key].get('location'))
                right_finger_low_white_key = f'low_white_{finger_index}_R'
                right_finger_low_white = np.array(
                    right_finger_recorders[right_finger_low_white_key].get('location'))
                right_finger_low_black_key = f'low_black_{finger_index}_R'
                right_finger_low_black = np.array(
                    right_finger_recorders[right_finger_low_black_key].get('location'))
                finger_position = lerp_with_key_type_and_position(
                    right_hand_white_key_value, right_hand_note, rightest_position, middle_right_position, left_position, right_finger_high_white, right_finger_high_black, right_finger_middle_white, right_finger_middle_black, right_finger_low_white, right_finger_low_black)

            # 这一步是计算实际按键的手指位置
            note = all_fingers[finger_index]["note"]
            is_black = all_fingers[finger_index]["is_black"]
            is_pressed = all_fingers[finger_index]["is_pressed"]

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

            # 双手大拇指按的距离要稍短一些
            finger_press_multiplier = 0.5 if finger_index == 4 or finger_index == 5 else 1.0

            is_keep_pressed = all_fingers[finger_index]["is_keep_pressed"]
            actual_press_depth = get_actual_press_depth(
                lowset_key_location, finger_position)
            finger_key = f"{finger_index}_L" if finger_index < self.finger_count / \
                2 else f"{finger_index}_R"
            if (not ready and is_pressed) or is_keep_pressed:  # 如果不是ready说明是已经按键下去了，需要在z轴上添加一段按键距离
                touch_point += actual_press_depth * finger_press_multiplier * press_key_direction
                result[finger_key] = touch_point.tolist()
            else:
                touch_point -= actual_press_depth * finger_press_multiplier * \
                    press_key_direction  # 没有按键的时候，手指抬起来
                result[finger_key] = touch_point.tolist()

        return result
