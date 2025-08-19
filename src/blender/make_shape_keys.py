"""
为所有钢琴键创建shape keys
"""

import bpy  # type: ignore
from math import radians


def create_shape_keys_for_selected():
    # 获取当前场景和选中的物体
    context = bpy.context
    selected_objects = context.selected_objects

    if not selected_objects:
        raise Exception("没有选中任何物体")

    # 获取3D视图区域（确保在3D视图中运行）
    view_3d = None
    for area in context.screen.areas:
        if area.type == 'VIEW_3D':
            view_3d = area.spaces[0]
            break

    if not view_3d:
        raise Exception("请在3D视图中运行此脚本")

    # 保存原始选中状态
    original_selection = [obj for obj in context.selected_objects]
    original_active = context.view_layer.objects.active

    bpy.context.scene.transform_orientation_slots[0].type = 'VIEW'
    bpy.context.scene.tool_settings.transform_pivot_point = 'CURSOR'

    for obj in selected_objects:
        if obj.type != 'MESH':
            print(f"跳过非网格物体: {obj.name}")
            continue

        # 取消所有物体的选中状态
        bpy.ops.object.select_all(action='DESELECT')

        # 选中当前处理的物体并设置为活动物体
        obj.select_set(True)
        context.view_layer.objects.active = obj

        # 1. 创建Basis形状键
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.context.object.use_shape_key_edit_mode = True
        if not obj.data.shape_keys:
            bpy.ops.object.shape_key_add(from_mix=False)
            obj.data.shape_keys.key_blocks[0].name = "Basis"

        # 2. 复制当前状态创建Pressed形状键
        bpy.ops.object.shape_key_add(from_mix=True)
        pressed_key_name = f"{obj.name}_pressed"
        obj.data.shape_keys.key_blocks[-1].name = pressed_key_name

        # 3. 进入编辑模式并全选顶点
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')

        obj.data.shape_keys.key_blocks[-1].value = 1.0

        # 4. 执行旋转操作（模拟手动操作）
        bpy.ops.transform.rotate(
            value=radians(-5),
            orient_axis='X',
            orient_type='LOCAL',
            center_override=obj.location,
            mirror=True,
            use_proportional_edit=False,
            proportional_edit_falloff='SMOOTH',
            proportional_size=1,
            use_proportional_connected=False,
            use_proportional_projected=False,
            snap=False,
            snap_elements={'INCREMENT'},
            use_snap_project=False,
            snap_target='CLOSEST',
            use_snap_self=True,
            use_snap_edit=True,
            use_snap_nonedit=True,
            use_snap_selectable=False
        )

        # 5. 回到对象模式
        bpy.ops.object.mode_set(mode='OBJECT')

        # 6. 将Pressed形状键的权重设置回0，恢复到Basis状态
        obj.data.shape_keys.key_blocks[-1].value = 0.0

        print(f"已为 {obj.name} 创建形状键: Basis 和 {pressed_key_name}")

    # 恢复原始选中状态
    bpy.ops.object.select_all(action='DESELECT')
    for obj in original_selection:
        obj.select_set(True)
    context.view_layer.objects.active = original_active


create_shape_keys_for_selected()
