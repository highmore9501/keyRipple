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

        # 清除形态键关键帧
        if hasattr(ob.data, "shape_keys"):
            if ob.data.shape_keys and ob.data.shape_keys.animation_data:
                # 调试语句
                print(f"Object {ob.name} has shape keys with animation data")
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
                print(f"警告: 物体 {obj_name} 不存在于场景中")
                continue

            obj = bpy.data.objects[obj_name]

            # 根据物体名称判断是位置还是旋转
            if "rotation" in obj_name.lower():
                # 设置旋转值 (欧拉角)
                obj.rotation_euler = transform_data
                obj.keyframe_insert(
                    data_path="rotation_euler", frame=frame)
            else:
                # 设置位置值
                obj.location = transform_data
                obj.keyframe_insert(data_path="location", frame=frame)


if __name__ == "__main__":
    midi_name = "World is Mine - Hatsune Miku"
    avatar_name = "Kinich"
    track_numbers = [0]
    track_text = str(track_numbers[0]) if len(track_numbers) == 1 else "_".join(
        [str(track_number) for track_number in track_numbers])
    animation_file_path = f"H:/keyRipple/output/animation_recorders/{midi_name}_{track_text}_{avatar_name}.animation"

    clear_all_keyframe(exclude_names=['Tar_B'])
    make_animation(animation_file_path)
