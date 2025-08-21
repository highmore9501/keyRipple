"""
以所选的骨骼为原本，创建MCH骨骼，然后将原骨骼的parent设置为MCH骨骼
主要是为所有手指骨骼批量创建MCH骨骼时使用
"""

import bpy  # type: ignore


def create_MCH_bones():

    # 切换到编辑模式
    bpy.ops.object.mode_set(mode='EDIT')
    current_bones = bpy.context.selected_editable_bones

    new_bones = []

    for bone in current_bones:
        # 复制骨骼
        bone_copy = bpy.context.object.data.edit_bones.new("MCH_" + bone.name)
        bone_copy.head = bone.head
        bone_copy.tail = bone.tail
        bone_copy.parent = bone.parent
        bone_copy.use_deform = False
        # 将现骨骼的connected选项去掉
        bone.use_connect = False
        # 将原骨骼的parent设置为新骨骼
        bone.parent = bone_copy
        new_bones.append(bone_copy)

    for copy_bone in new_bones:
        # 检测它的parent是否有MCH前缀的同名骨骼存在
        parent = copy_bone.parent
        if not parent:
            continue
        new_parent_name = "MCH_" + parent.name
        new_parent = bpy.context.object.data.edit_bones.get(new_parent_name)
        if new_parent:
            copy_bone.parent = new_parent


create_MCH_bones()
