import bpy  # type: ignore

# 配置参数 - 根据你的需要修改这些值
START_FRAME = 0        # 开始帧
INTERVAL = 240         # 间隔帧数
CAMERA_NAMES = [       # 摄像机对象名称列表，按顺序循环使用
    "Camera_A",
    "Camera_B",
    "Camera_C",
    "Camera_D",
    "Camera_E"
]


def add_camera_markers_interval():
    """
    从起始帧开始，按指定间隔添加摄像机标记，并循环绑定列表中的摄像机
    """
    # 获取场景
    scene = bpy.context.scene

    # 清除所有现有标记（可选，如果需要全新开始则取消注释下一行）
    scene.timeline_markers.clear()

    # 获取摄像机对象列表
    cameras = []
    for cam_name in CAMERA_NAMES:
        cam_obj = bpy.data.objects.get(cam_name)
        if cam_obj and cam_obj.type == 'CAMERA':
            cameras.append(cam_obj)
        else:
            print(f"警告: 找不到摄像机 '{cam_name}' 或该对象不是摄像机")

    if not cameras:
        print("错误: 没有找到有效的摄像机对象!")
        return

    print(f"找到 {len(cameras)} 个摄像机: {[cam.name for cam in cameras]}")

    # 计算需要添加多少个标记
    frame_range = scene.frame_end - START_FRAME
    num_markers = frame_range // INTERVAL + 1

    print(f"将从第 {START_FRAME} 帧开始，每 {INTERVAL} 帧添加一个标记，共添加 {num_markers} 个标记")

    # 添加标记并绑定摄像机
    for i in range(num_markers):
        frame = START_FRAME + i * INTERVAL

        # 选择当前要绑定的摄像机（循环使用）
        current_camera = cameras[i % len(cameras)]

        # 将当前摄像机设置为场景的活动摄像机
        scene.camera = current_camera

        # 添加标记
        marker = scene.timeline_markers.new(
            name=f"Cam_{current_camera.name}", frame=frame)

        # 将摄像机绑定到标记
        marker.camera = current_camera

        print(f"在第 {frame} 帧添加标记，绑定摄像机: {current_camera.name}")

    print("操作完成!")


# 执行函数
add_camera_markers_interval()
