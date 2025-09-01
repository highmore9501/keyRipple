import bpy  # type: ignore
import math
import bmesh  # type: ignore

# 配置参数
mesh_name = "hair_wave_curve"    # 您的网格物体名称
amplitude_start = 1.0            # 起始振幅
amplitude_end = 0.1              # 末端振幅
wave_speed = 2.0                 # 波速（控制波向前行进的速度）
wave_frequency = 0.3             # 波频率（控制波的密集程度）
wave_direction = 'X'             # 波行进方向：'X' 或 'Y'
displacement_axis = 'Z'          # 位移方向：'Z'
start_frame = 1                  # 动画开始帧
end_frame = 100                  # 动画结束帧

# 获取网格物体
mesh_obj = bpy.data.objects.get(mesh_name)
if mesh_obj is None:
    raise Exception(f"错误：找不到名为 '{mesh_name}' 的网格物体")

mesh = mesh_obj.data

# 进入编辑模式并创建bmesh实例（为了获取准确的顶点数据）
bpy.context.view_layer.objects.active = mesh_obj
bpy.ops.object.mode_set(mode='EDIT')
bm = bmesh.new()
bm.from_mesh(mesh)

# 获取所有顶点并按位置排序（确保顺序正确）
vertices = []
for vert in bm.verts:
    if wave_direction == 'X':
        sort_key = vert.co.x
    else:  # 'Y'
        sort_key = vert.co.y
    vertices.append((sort_key, vert.index))  # 保存顶点索引而不是顶点对象

# 按行进方向排序顶点
vertices.sort(key=lambda x: x[0])
sorted_vert_indices = [v[1] for v in vertices]  # 保存排序后的顶点索引

# 获取位置范围（用于振幅衰减）
positions = [v[0] for v in vertices]
min_pos = min(positions)
max_pos = max(positions)
pos_range = max_pos - min_pos

print(f"找到 {len(sorted_vert_indices)} 个顶点，位置范围: {min_pos:.2f} 到 {max_pos:.2f}")

# 退出编辑模式
bpy.ops.object.mode_set(mode='OBJECT')
bm.free()  # 释放bmesh

# 存储顶点的初始位置（用于每帧重置）
initial_positions = []
for vert_idx in sorted_vert_indices:
    initial_positions.append(mesh.vertices[vert_idx].co.copy())

# 遍历每一帧，创建行进波动画
for frame in range(start_frame, end_frame + 1):
    bpy.context.scene.frame_set(frame)

    # 重置所有顶点到初始位置
    for i, vert_idx in enumerate(sorted_vert_indices):
        mesh.vertices[vert_idx].co = initial_positions[i].copy()

    # 为每个顶点计算波形位移
    for i, vert_idx in enumerate(sorted_vert_indices):
        # 获取顶点在行进方向上的原始位置
        if wave_direction == 'X':
            original_pos = initial_positions[i].x
        else:  # 'Y'
            original_pos = initial_positions[i].y

        # 计算该点的振幅衰减（基于在行进方向上的位置）
        position_ratio = (original_pos - min_pos) / pos_range
        amplitude = amplitude_start + \
            (amplitude_end - amplitude_start) * position_ratio

        # 行进波公式：振幅 * sin(波数 * 位置 - 角频率 * 时间)
        # 波数 = 2π * 频率
        wave_number = 2 * math.pi * wave_frequency
        angular_frequency = wave_speed * wave_number
        wave_offset = amplitude * \
            math.sin(wave_number * original_pos - angular_frequency * frame)

        # 应用位移到指定轴
        vert = mesh.vertices[vert_idx]  # 获取当前顶点对象
        if displacement_axis == 'X':
            vert.co.x += wave_offset
        elif displacement_axis == 'Y':
            vert.co.y += wave_offset
        else:  # 'Z'
            vert.co.z += wave_offset

    # 为所有顶点插入关键帧
    for vert_idx in sorted_vert_indices:
        mesh.vertices[vert_idx].keyframe_insert(data_path="co", index=-1)

    if frame % 10 == 0:  # 每10帧打印一次进度
        print(f"已创建帧 {frame} 的关键帧")

# 更新网格和视图
mesh.update()
mesh_obj.update_tag()
bpy.context.view_layer.update()

print(f"行进波动画创建完成！从帧 {start_frame} 到 {end_frame}")
print(
    f"参数：波速={wave_speed}, 频率={wave_frequency}, 振幅={amplitude_start}→{amplitude_end}")
