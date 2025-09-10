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
        if ob.name in exclude_names or ob.name.startswith("Tar"):
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

    # 用于存储每个物体的上一帧四元数
    previous_quaternions = {}

    # 处理每一帧动画数据
    for frame_index, frame_data in enumerate(animation_data):
        frame = int(frame_data.get("frame", 0))
        hand_infos = frame_data.get("hand_infos", {})

        if frame < 0:
            continue

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

                    # 应用四元数一致性处理
                    if obj_name in previous_quaternions:
                        # 计算点积判断是否需要反转
                        dot = sum(
                            a*b for a, b in zip(previous_quaternions[obj_name], transform_data))
                        if dot < 0:
                            # 反转当前四元数
                            transform_data = [-x for x in transform_data]

                    # 更新存储的上一帧四元数
                    previous_quaternions[obj_name] = transform_data

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

                            # 应用四元数一致性处理
                            if rotation_obj_name in previous_quaternions:
                                # 计算点积判断是否需要反转
                                dot = sum(
                                    a*b for a, b in zip(previous_quaternions[rotation_obj_name], rotation_data))
                                if dot < 0:
                                    # 反转当前四元数
                                    rotation_data = [-x for x in rotation_data]

                            # 更新存储的上一帧四元数
                            previous_quaternions[rotation_obj_name] = rotation_data

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


def generate_piano_key_animation(piano_key_animation_path: str):
    """
    根据预先计算好的钢琴键动画数据在Blender中执行插帧操作

    参数:
    piano_key_animation_path: 钢琴键动画数据文件路径
    """

    # 读取钢琴键动画数据
    try:
        with open(piano_key_animation_path, 'r') as f:
            piano_key_animation_data = json.load(f)
    except Exception as e:
        print(f"无法读取钢琴键动画数据文件: {e}")
        return

    def insert_keyframe(obj, shape_key, frame, shape_key_value, is_pressed_value=None):
        """
        为钢琴键物体插入关键帧的辅助函数

        参数:
        obj: 物体对象
        shape_key: 形态键对象
        frame: 帧数
        shape_key_value: 形态键值 (0.0-1.0)
        is_pressed_value: is_pressed属性值 (0.0-1.0)，如果为None则不设置
        """
        # 设置场景帧
        bpy.context.scene.frame_set(frame)

        # 设置并插入shape key关键帧
        shape_key.value = shape_key_value
        shape_key.keyframe_insert(data_path="value", frame=frame)

        # 如果提供了is_pressed值且物体有该属性，则设置并插入关键帧
        if is_pressed_value is not None and "is_pressed" in obj:
            obj["is_pressed"] = is_pressed_value
            obj.keyframe_insert(data_path='["is_pressed"]', frame=frame)

    # 处理每个键的动画数据
    for key_data in piano_key_animation_data:
        key_name = key_data["key_name"]
        shape_key_name = key_data["shape_key_name"]

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

        # 为每个关键帧插入动画
        for keyframe in key_data["keyframes"]:
            frame = keyframe["frame"]
            shape_key_value = keyframe["shape_key_value"]
            is_pressed_value = keyframe["is_pressed_value"]

            insert_keyframe(obj, shape_key, frame,
                            shape_key_value, is_pressed_value)


if __name__ == "__main__":
    avatar_name = "Kinich"
    midi_name = "妖怪之山 - 东方project"
    track_numbers = [1, 2]
    track_text = str(track_numbers[0]) if len(track_numbers) == 1 else "_".join(
        [str(track_number) for track_number in track_numbers])
    animation_file_path = f"H:/keyRipple/output/animation_recorders/{midi_name}_{track_text}_{avatar_name}.animation"
    piano_key_animation_path = f"H:/keyRipple/output/piano_key_animations/{midi_name}_{track_text}_{avatar_name}.piano_key_animation"

    hand_recorder_path = f"H:/keyRipple/output/hand_recorders/{midi_name}_{track_text}.hand"

    collection_name = 'keyboard'
    clear_all_keyframe(collection_name)
    make_animation(animation_file_path)
    generate_piano_key_animation(piano_key_animation_path)
