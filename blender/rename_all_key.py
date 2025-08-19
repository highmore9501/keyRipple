"""
用于重命名所有钢琴键
"""

import bpy  # type: ignore

# 获取当前选中的物体
selected_objects = bpy.context.selected_objects

# 确保至少选中了一个物体
if not selected_objects:
    raise Exception("没有选中任何物体")

# 根据Y轴坐标对物体进行排序
sorted_objects = sorted(selected_objects, key=lambda obj: obj.location.x)

# 重命名物体
for index, obj in enumerate(sorted_objects, start=0):
    number = index + 21
    obj.name = f"key_{number}"

print(f"已根据x轴顺序重命名了{len(sorted_objects)}个物体")
