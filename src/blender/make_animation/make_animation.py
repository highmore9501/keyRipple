import bpy  # type: ignore
import json


def clear_all_keyframe(collection_name=None, exclude_names=None):
    """
    清除关键帧函数

    Args:
        collection_name: 要处理的集合名称
        exclude_names: 要排除的物体名称或集合名称列表
    """
    if exclude_names is None:
        exclude_names = []

    # 选择特定collection下的所有物体
    if collection_name:
        # 取消当前所有选择
        bpy.ops.object.select_all(action='DESELECT')
        # 获取指定collection
        collection = bpy.data.collections.get(collection_name)
        if collection:
            # 递归获取collection及其所有子collection中的物体
            def select_collection_objects(col):
                # 选择当前collection中的所有物体
                for obj in col.objects:
                    # 检查物体是否在排除列表中
                    if obj.name in exclude_names:
                        print(f"Excluding object: {obj.name}")
                        continue
                    obj.select_set(True)
                    print(f"Selected object: {obj.name}")  # 调试语句
                    bpy.context.view_layer.objects.active = obj  # 设置活动对象

                # 递归处理所有子collection
                for child_col in col.children:
                    # 检查子集合是否在排除列表中
                    if child_col.name in exclude_names:
                        print(f"Excluding collection: {child_col.name}")
                        continue
                    select_collection_objects(child_col)

            select_collection_objects(collection)
            # 调试语句
            print(
                f"Total selected objects: {len(bpy.context.selected_objects)}")
        else:
            print(f"Collection '{collection_name}' not found")
            return
    else:
        # 如果没有指定collection，则选择所有物体（原有逻辑）
        bpy.ops.object.select_all(action='SELECT')
        # 但需要取消选择排除列表中的物体
        for obj in bpy.data.objects:
            if obj.name in exclude_names:
                obj.select_set(False)
                print(f"Excluding object: {obj.name}")

    # 清除所有关键帧 - 改进版本
    # 调试语句
    print(
        f"Processing {len(bpy.context.selected_objects)} objects for animation clearing")

    for ob in bpy.context.selected_objects:
        # 额外检查：确保物体不在排除列表中
        if ob.name in exclude_names:
            print(f"Skipping excluded object: {ob.name}")
            continue

        print(f"Processing object: {ob.name}")  # 调试语句

        # 清除对象变换关键帧
        if ob.animation_data:
            print(f"Object {ob.name} has animation_data")  # 调试语句
            if ob.animation_data.action:
                # 调试语句
                print(
                    f"Object {ob.name} has action with {len(ob.animation_data.action.fcurves)} fcurves")
                for fcurve in ob.animation_data.action.fcurves:
                    # 调试语句
                    print(
                        f"Clearing {len(fcurve.keyframe_points)} keyframes from {ob.name}")
                    fcurve.keyframe_points.clear()

         # 清除形态键关键帧并归零形态键值
        if hasattr(ob.data, "shape_keys"):
            if ob.data.shape_keys:
                # 首先归零所有shape key的值
                for shape_key_block in ob.data.shape_keys.key_blocks:
                    shape_key_block.value = 0.0
                    print(f"Reset shape key {shape_key_block.name} to 0.0")

                # 然后清除形态键动画数据
                if ob.data.shape_keys.animation_data:
                    # 调试语句
                    print(
                        f"Object {ob.name} has shape keys with animation data")
                    if ob.data.shape_keys.animation_data.action:
                        for fcurve in ob.data.shape_keys.animation_data.action.fcurves:
                            # 调试语句
                            print(
                                f"Clearing {len(fcurve.keyframe_points)} shape key keyframes from {ob.name}")
                            fcurve.keyframe_points.clear()

        # 尝试清除所有动画数据
        if ob.animation_data:
            print(f"Clearing animation data for {ob.name}")  # 调试语句
            ob.animation_data_clear()
        if hasattr(ob.data, "shape_keys") and ob.data.shape_keys:
            if ob.data.shape_keys.animation_data:
                # 调试语句
                print(f"Clearing shape key animation data for {ob.name}")
                ob.data.shape_keys.animation_data_clear()

    # 取消全选
    bpy.ops.object.select_all(action='DESELECT')


def make_animation(animation_file_path: str):
    # 读取动画文件
    try:
        with open(animation_file_path, 'r') as f:
            animation_data = json.load(f)
    except Exception as e:
        print(f"无法读取动画文件: {e}")
        return

    # 处理每一帧动画数据
    for frame_index, frame_data in enumerate(animation_data):
        frame = int(frame_data.get("frame", 0))
        hand_infos = frame_data.get("hand_infos", {})

        # 设置当前帧
        bpy.context.scene.frame_set(frame)

        # 遍历所有手部信息
        for obj_name, transform_data in hand_infos.items():
            # 检查物体是否存在
            if obj_name not in bpy.data.objects:
                if not obj_name.startswith("Tar_H"):
                    print(f"警告: 物体 {obj_name} 不存在于场景中")
                continue

            obj = bpy.data.objects[obj_name]

            # 根据物体名称判断是位置还是旋转
            if "rotation" in obj_name.lower():
                # 判断旋转数据维度
                if len(transform_data) == 4:
                    # 四元数旋转 (w, x, y, z)
                    obj.rotation_mode = 'QUATERNION'
                    obj.rotation_quaternion = transform_data
                    obj.keyframe_insert(
                        data_path="rotation_quaternion", frame=frame)
                else:
                    # 欧拉角旋转
                    obj.rotation_euler = transform_data
                    obj.keyframe_insert(
                        data_path="rotation_euler", frame=frame)
            else:
                # 设置位置值
                obj.location = transform_data
                obj.keyframe_insert(data_path="location", frame=frame)

                # 特别处理hand_target物体，同时设置旋转值
                # 检查是否是手部目标点物体 (Tar_H_L 或 Tar_H_R)
                if obj_name.startswith("Tar_H_"):
                    # 查找对应的旋转数据
                    rotation_obj_name = obj_name.replace(
                        "Tar_H_", "Tar_H_rotation_")
                    if rotation_obj_name in hand_infos:
                        rotation_data = hand_infos[rotation_obj_name]
                        # 判断旋转数据维度
                        if len(rotation_data) == 4:
                            # 四元数旋转 (w, x, y, z)
                            obj.rotation_mode = 'QUATERNION'
                            obj.rotation_quaternion = rotation_data
                            obj.keyframe_insert(
                                data_path="rotation_quaternion", frame=frame)
                        else:
                            # 欧拉角旋转
                            obj.rotation_euler = rotation_data
                            obj.keyframe_insert(
                                data_path="rotation_euler", frame=frame)
                    else:
                        print(
                            f"警告: 未找到 {obj_name} 对应的旋转数据 {rotation_obj_name}")


def generate_piano_key_animation(hand_recorder_path: str, frames_ahead: int = 3, frames_duration: int = 6):
    """
    根据hand_recorder数据生成钢琴键动画

    参数:
    hand_recorder_path: hand_recorder文件路径
    frames_ahead: 按键提前帧数（在目标帧之前多少帧开始按下）
    frames_duration: 按键持续帧数
    """

    # 读取hand_recorder数据
    try:
        with open(hand_recorder_path, 'r') as f:
            hand_recorder = json.load(f)
    except Exception as e:
        print(f"无法读取hand_recorder文件: {e}")
        return

    # 处理每一帧数据
    for frame_data in hand_recorder:
        frame = int(frame_data.get("frame", 0))

        # 处理左手和右手
        for hand in [frame_data.get("left_hand", {}), frame_data.get("right_hand", {})]:
            fingers = hand.get("fingers", [])

            # 遍历所有手指
            for finger in fingers:
                if finger.get("pressed", False):  # 只处理按下的手指
                    note = finger["key_note"]["note"]
                    key_name = f"key_{note}"
                    shape_key_name = f"{key_name}_pressed"

                    # 检查物体是否存在
                    if key_name not in bpy.data.objects:
                        print(f"警告: 钢琴键物体 {key_name} 不存在")
                        continue

                    obj = bpy.data.objects[key_name]

                    # 检查shape key是否存在
                    if not hasattr(obj.data, "shape_keys") or not obj.data.shape_keys:
                        print(f"警告: 物体 {key_name} 没有shape keys")
                        continue

                    # 查找对应的shape key
                    shape_key = None
                    for block in obj.data.shape_keys.key_blocks:
                        if block.name == shape_key_name:
                            shape_key = block
                            break

                    if not shape_key:
                        print(f"警告: 未找到shape key {shape_key_name}")
                        continue

                    # 设置动画关键帧
                    # 在目标帧之前几帧开始按下
                    press_frame = frame + frames_ahead
                    # 按下状态持续几帧
                    release_frame = press_frame + frames_duration

                    # 设置按下前为0的关键帧
                    bpy.context.scene.frame_set(frame)
                    shape_key.value = 0.0
                    shape_key.keyframe_insert(
                        data_path="value", frame=frame)

                    # 设置按下后的关键帧
                    bpy.context.scene.frame_set(press_frame)
                    shape_key.value = 1.0
                    shape_key.keyframe_insert(
                        data_path="value", frame=press_frame)

                    # 设置释放关键帧
                    bpy.context.scene.frame_set(release_frame)
                    shape_key.value = 0.0
                    shape_key.keyframe_insert(
                        data_path="value", frame=release_frame)


if __name__ == "__main__":
    midi_name = "World is Mine - Hatsune Miku"
    avatar_name = "Kinich"
    track_numbers = [0]
    track_text = str(track_numbers[0]) if len(track_numbers) == 1 else "_".join(
        [str(track_number) for track_number in track_numbers])
    animation_file_path = f"H:/keyRipple/output/animation_recorders/{midi_name}_{track_text}_{avatar_name}.animation"

    hand_recorder_path = f"H:/keyRipple/output/hand_recorders/{midi_name}_{track_text}.hand"

    clear_all_keyframe(exclude_names=['Tar_B'])
    make_animation(animation_file_path)
    generate_piano_key_animation(
        hand_recorder_path, frames_ahead=6, frames_duration=12)
