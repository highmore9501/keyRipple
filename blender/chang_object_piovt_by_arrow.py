import bpy  # type: ignore
import mathutils  # type: ignore


def set_pivot_from_arrow(arrow_name: str):
    # 获取当前场景
    context = bpy.context
    scene = context.scene

    # 根据名称查找箭头空物体
    arrow_obj = bpy.data.objects.get(arrow_name)

    # 验证找到的物体
    if not arrow_obj:
        raise Exception(f"未找到名为 '{arrow_name}' 的物体")
    if arrow_obj.type != 'EMPTY' or arrow_obj.empty_display_type != 'SINGLE_ARROW':
        raise Exception(f"物体 '{arrow_name}' 不是箭头类型的空物体")

    # 获取箭头物体的方向向量（全局坐标系）
    arrow_direction = arrow_obj.matrix_world.to_quaternion() @ mathutils.Vector((0, 0, 1))
    arrow_position = arrow_obj.matrix_world.translation

    # 获取选中的物体（排除箭头物体本身）
    selected_objects = [
        obj for obj in context.selected_objects if obj != arrow_obj]

    if not selected_objects:
        raise Exception("没有选中需要修改轴心的物体")

    # 保存原始选中状态
    original_selection = [obj for obj in context.selected_objects]
    original_active = context.view_layer.objects.active

    # 保存原始游标位置
    original_cursor_location = scene.cursor.location.copy()

    try:
        # 对每个选中物体进行处理
        for obj in selected_objects:
            # 取消所有物体的选中状态
            bpy.ops.object.select_all(action='DESELECT')

            # 选中当前处理的物体并设置为活动物体
            obj.select_set(True)
            context.view_layer.objects.active = obj

            # 1. 获取物体当前轴心（全局坐标）
            current_pivot = obj.matrix_world.translation

            # 2. 计算直线与平面的交点
            denominator = arrow_direction.dot(arrow_direction)
            if denominator < 1e-6:
                print(f"警告: 物体 {obj.name} 的箭头方向无效，已跳过")
                continue

            t = (current_pivot - arrow_position).dot(arrow_direction) / denominator
            new_pivot = arrow_position + t * arrow_direction

            # 3. 设置新的轴心
            scene.cursor.location = new_pivot
            bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')

            print(f"已更新物体 {obj.name} 的轴心位置 -> {new_pivot}")

    finally:
        # 恢复原始游标位置
        scene.cursor.location = original_cursor_location

        # 恢复原始选中状态
        bpy.ops.object.select_all(action='DESELECT')
        for obj in original_selection:
            obj.select_set(True)
        context.view_layer.objects.active = original_active


# 执行函数
arrow_name = "black_keys_pivot"
set_pivot_from_arrow(arrow_name)
