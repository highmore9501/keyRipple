"""
这里所有方法成立的前提是假设键盘横方向正好是x轴，键盘放置在xy平面内,键盘演奏者的朝向是y轴正方向
"""

import numpy as np
from src.piano.keyNote import KeyNote
from src.piano.piano import Piano
from typing import Any


def get_touch_point(finger_position: np.ndarray, key_position: np.ndarray) -> np.ndarray:
    """
    获取手指在按键上的接触点
    param finger_position: 手指位置
    param key_position: 按键中点位置    
    """
    # 检测参数是否合法
    if len(finger_position) != 3 or len(key_position) != 3:
        raise ValueError("位置参数长度错误")

    return np.array([key_position[0], min(finger_position[1], key_position[1]), key_position[2]])


def get_key_location(note: int, is_black: bool, piano: Piano, lowest_key_position: np.ndarray, highest_key_position: np.ndarray, black_key_position: np.ndarray) -> np.ndarray:
    """
    获取按键的位置
    param key_note: 按键的keyNote信息
    param piano: 钢琴的Piano信息
    param lowest_key_position: 最低按键的位置，正常情况下这是个白键
    param highest_key_position: 最高按键的位置，正常情况下这也是个白键
    param: black_key_position: 这是任意一个黑键的位置，用它来确定其它黑键的yz轴坐标
    """
    number_of_white_keys = piano.numberOfWhiteKeys
    white_key_distance = (highest_key_position -
                          lowest_key_position) / number_of_white_keys
    white_keys = piano.white_keys

    if not is_black:
        key_index = white_keys.index(note)
        key_position = lowest_key_position + white_key_distance * key_index
    else:
        pre_key_index = white_keys.index(note - 1)
        key_position = lowest_key_position + white_key_distance * \
            pre_key_index + white_key_distance / 2
        key_position[1] = black_key_position[1]
        key_position[2] = black_key_position[2]

    return key_position


def twiceLerp(low_white: np.ndarray, high_white: np.ndarray, low_black: np.ndarray, high_black: np.ndarray, hand_weight: float, black_key_weight: float) -> np.ndarray:
    if len(low_white) != len(high_white) or len(low_white) != len(low_black) or len(low_white) != len(high_black):
        raise ValueError("参数长度不一致")

    white = low_white + (high_white - low_white) * hand_weight
    black = low_black + (high_black - low_black) * hand_weight

    return white + (black - white) * black_key_weight


def calculate_3d_coefficients(points: list[np.ndarray], values: np.ndarray) -> np.ndarray:
    """
    根据四个不共面的点和对应的属性值，计算线性方程的系数

    参数:
    points: 4个点的坐标，格式为 [(x1,y1,z1), (x2,y2,z2), (x3,y3,z3), (x4,y4,z4)]
    values: 4个点对应的属性值，格式为 [s1, s2, s3, s4]，每个s可以是多维数组

    返回:
    coefficients: 系数矩阵，形状为 (n, 4)，其中n是属性值的维度
    """

    # 构建矩阵 M
    M = []
    for x, y, z in points:
        M.append([x, y, z, 1])
    M = np.array(M)

    # 将values转换为numpy数组并检查维度
    values_array = np.array(values)

    # 如果values是一维数组（原始情况），则扩展为二维
    if values_array.ndim == 1:
        values_array = values_array.reshape(-1, 1)

    # 获取属性值的维度
    n_dims = values_array.shape[1]

    # 存储每个维度的系数
    coefficients_list = []

    # 对每个维度分别求解
    for i in range(n_dims):
        S = values_array[:, i]

        # 求解线性方程组 M * X = S
        try:
            # 使用最小二乘法求解，更稳定
            coef = np.linalg.lstsq(M, S, rcond=None)[0]
            coefficients_list.append(coef)
        except np.linalg.LinAlgError:
            raise ValueError("四个点共面，无法确定唯一的三维线性函数")

    # 将系数组合成矩阵，形状为 (n_dims, 4)
    coefficients = np.array(coefficients_list)

    # 检测系数的形状
    if coefficients.shape[0] != n_dims:
        raise ValueError("系数矩阵的维度与属性值的维度不一致")

    return coefficients


def calculate_2d_coefficients(points: list[np.ndarray], values: np.ndarray) -> np.ndarray:
    """
    根据三个不共线的点和对应的属性值，计算二维平面方程的系数

    参数:
    points: 3个点的坐标，格式为 [(x1,y1), (x2,y2), (x3,y3)]
    values: 3个点对应的属性值，格式为 [s1, s2, s3]，每个s可以是多维数组

    返回:
    coefficients: 系数矩阵，形状为 (n, 3)，其中n是属性值的维度
    """

    # 检查点的数量
    if len(points) != 3:
        raise ValueError("需要恰好3个点来确定一个二维平面")

    # 构建矩阵 M
    M = []
    for x, y in points:
        M.append([x, y, 1])
    M = np.array(M)

    # 将values转换为numpy数组并检查维度
    values_array = np.array(values)

    # 如果values是一维数组（原始情况），则扩展为二维
    if values_array.ndim == 1:
        values_array = values_array.reshape(-1, 1)

    # 获取属性值的维度
    n_dims = values_array.shape[1]

    # 存储每个维度的系数
    coefficients_list = []

    # 对每个维度分别求解
    for i in range(n_dims):
        S = values_array[:, i]

        # 求解线性方程组 M * X = S
        try:
            # 使用最小二乘法求解，更稳定
            coef = np.linalg.lstsq(M, S, rcond=None)[0]
            coefficients_list.append(coef)
        except np.linalg.LinAlgError:
            print(points)
            print(values)
            raise ValueError("三个点共线，无法确定唯一的二维平面函数")

    # 将系数组合成矩阵，形状为 (n_dims, 3)
    coefficients = np.array(coefficients_list)

    # 检测系数的形状
    if coefficients.shape[0] != n_dims:
        raise ValueError("系数矩阵的维度与属性值的维度不一致")

    return coefficients


def calculate_quaternion_2d_coefficients(points: list[np.ndarray], quaternions: list[Any]) -> Any:
    """
    根据三个不共线的点和对应的四元数，计算用于四元数插值的参考数据

    参数:
    points: 3个点的坐标，格式为 [(x1,y1), (x2,y2), (x3,y3)]
    quaternions: 3个点对应的四元数，格式为 [[w1,x1,y1,z1], [w2,x2,y2,z2], [w3,x3,y3,z3]]

    返回:
    reference_data: 包含参考点和四元数的列表，用于后续插值
    """
    if len(points) != 3 or len(quaternions) != 3:
        raise ValueError("需要恰好3个点和对应的四元数")

    # 确保所有四元数在同一半球
    q0 = np.array(quaternions[0])
    q1 = np.array(quaternions[1])
    q2 = np.array(quaternions[2])

    if np.dot(q0, q1) < 0:
        q1 = -q1
    if np.dot(q0, q2) < 0:
        q2 = -q2

    # 返回参考数据，包括点坐标和对应的四元数
    reference_data = [
        (np.array(points[0]), q0),
        (np.array(points[1]), q1),
        (np.array(points[2]), q2)
    ]

    return reference_data


def interpolate_quaternion_from_coefficients(reference_data: Any, target_point: np.ndarray) -> np.ndarray:
    """
    使用参考数据为二维平面上的任意点插值四元数

    参数:
    reference_data: 由calculate_quaternion_2d_coefficients生成的参考数据
    target_point: 目标点坐标，格式为 [x, y]

    返回:
    插值后的四元数，格式为 [w, x, y, z]
    """
    # 提取参考点和四元数
    points = [data[0] for data in reference_data]
    quaternions = [data[1] for data in reference_data]

    # 使用现有的quaternion_interpolation_from_3_points方法
    return quaternion_interpolation_from_3_points(points, quaternions,
                                                  np.array([target_point[0], target_point[1], 0]))


def evaluate_2d_point(coefficients, point):
    """
    使用计算出的系数为二维平面上的任意点求值

    参数:
    coefficients: 系数矩阵，形状为 (n, 3)
    point: 要评估的点，格式为 (x, y)

    返回:
    s_value: 计算出的属性值数组，形状为 (n,)
    """
    x, y = point
    # coefficients形状为 (n, 3)，分别对应每个维度的 [a, b, c]
    # 计算 a*x + b*y + c 对每个维度
    result = coefficients[:, 0] * x + \
        coefficients[:, 1] * y + coefficients[:, 2]
    return result


def evaluate_3d_point(coefficients, point):
    """
    使用计算出的系数为任意点求值

    参数:
    coefficients: 系数矩阵，形状为 (n, 4)
    point: 要评估的点，格式为 (x, y, z)

    返回:
    s_value: 计算出的属性值数组，形状为 (n,)
    """
    x, y, z = point
    # coefficients形状为 (n, 4)，分别对应每个维度的 [a, b, c, d]
    # 计算 a*x + b*y + c*z + d 对每个维度
    result = coefficients[:, 0] * x + coefficients[:, 1] * \
        y + coefficients[:, 2] * z + coefficients[:, 3]
    return result


def slerp(q1: np.ndarray, q2: np.ndarray, t: float) -> np.ndarray:
    """
    四元数球面线性插值 (Spherical Linear Interpolation)

    参数:
    q1, q2: 四元数，格式为 [w, x, y, z]
    t: 插值参数，范围 [0, 1]

    返回:
    插值后的四元数
    """
    # 标准化四元数
    q1 = q1 / np.linalg.norm(q1)
    q2 = q2 / np.linalg.norm(q2)

    # 计算点积
    dot = np.dot(q1, q2)

    # 如果点积为负，取反一个四元数以选择较短的路径
    if dot < 0.0:
        q2 = -q2
        dot = -dot

    # 如果四元数非常接近，使用线性插值避免数值问题
    if dot > 0.9995:
        result = q1 + t * (q2 - q1)
        return result / np.linalg.norm(result)

    # 计算夹角
    theta_0 = np.arccos(np.clip(dot, -1.0, 1.0))
    theta = theta_0 * t

    # 计算插值
    q3 = q2 - q1 * dot
    q3 = q3 / np.linalg.norm(q3)

    return q1 * np.cos(theta) + q3 * np.sin(theta)


def calculate_barycentric_coordinates(p1: np.ndarray, p2: np.ndarray, p3: np.ndarray, p: np.ndarray) -> tuple[float, float, float]:
    """
    计算点p在三角形p1,p2,p3内的重心坐标

    参数:
    p1, p2, p3: 三角形的三个顶点坐标，格式为 [x, y, z]
    p: 目标点坐标，格式为 [x, y, z]

    返回:
    (u, v, w): 重心坐标，满足 p = u*p1 + v*p2 + w*p3 且 u + v + w = 1
    """
    # 计算向量
    v0 = p2 - p1
    v1 = p3 - p1
    v2 = p - p1

    # 计算点积
    dot00 = np.dot(v0, v0)
    dot01 = np.dot(v0, v1)
    dot02 = np.dot(v0, v2)
    dot11 = np.dot(v1, v1)
    dot12 = np.dot(v1, v2)

    # 计算重心坐标
    inv_denom = 1.0 / (dot00 * dot11 - dot01 * dot01)
    v = (dot11 * dot02 - dot01 * dot12) * inv_denom
    w = (dot00 * dot12 - dot01 * dot02) * inv_denom
    u = 1.0 - v - w

    return (u, v, w)


def quaternion_interpolation_from_3_points(points: list[np.ndarray], quaternions: list[np.ndarray], target_point: np.ndarray) -> np.ndarray:
    """
    基于三个已知点的四元数，在平面上插值得到目标点的四元数

    参数:
    points: 3个已知点的坐标，格式为 [[x1,y1,z1], [x2,y2,z2], [x3,y3,z3]]
    quaternions: 3个已知点对应的四元数，格式为 [[w1,x1,y1,z1], [w2,x2,y2,z2], [w3,x3,y3,z3]]
    target_point: 目标点坐标，格式为 [x, y, z]

    返回:
    目标点的四元数，格式为 [w, x, y, z]
    """
    if len(points) != 3 or len(quaternions) != 3:
        raise ValueError("需要恰好3个点和对应的四元数")

    # 计算重心坐标
    u, v, w = calculate_barycentric_coordinates(
        np.array(points[0]),
        np.array(points[1]),
        np.array(points[2]),
        np.array(target_point)
    )

    # 使用重心坐标进行四元数插值
    # 首先对前两个四元数进行插值
    if abs(u) < 1e-10:  # u接近0
        q01 = slerp(quaternions[1], quaternions[2], v / (v + w))
    elif abs(v) < 1e-10:  # v接近0
        q01 = slerp(quaternions[0], quaternions[2], u / (u + w))
    elif abs(w) < 1e-10:  # w接近0
        q01 = slerp(quaternions[0], quaternions[1], u / (u + v))
    else:
        # 一般情况：分两步进行SLERP插值
        q0 = slerp(quaternions[0], quaternions[1], v / (u + v))
        q1 = slerp(quaternions[0], quaternions[2], w / (u + w))
        # 根据重心坐标权重进行最终插值
        weights_sum = abs(u) + abs(v) + abs(w)
        if weights_sum > 1e-10:
            normalized_u = abs(u) / weights_sum
            normalized_v = abs(v) / weights_sum
            normalized_w = abs(w) / weights_sum
            # 重新计算插值
            q0 = slerp(quaternions[0], quaternions[1], normalized_v / (
                normalized_u + normalized_v) if (normalized_u + normalized_v) > 1e-10 else 0)
            q1 = slerp(quaternions[0], quaternions[2], normalized_w / (
                normalized_u + normalized_w) if (normalized_u + normalized_w) > 1e-10 else 0)
            q01 = slerp(q0, q1, 0.5)  # 简化处理
        else:
            q01 = quaternions[0]

    # 更准确的实现方式：使用多重SLERP
    # 将三个四元数按照重心坐标进行插值
    # 首先确保所有四元数在同一半球
    q0, q1, q2 = quaternions[0], quaternions[1], quaternions[2]
    if np.dot(q0, q1) < 0:
        q1 = -q1
    if np.dot(q0, q2) < 0:
        q2 = -q2

    # 使用重心坐标进行插值的近似方法
    # 这是一种简化的处理方式，适用于重心坐标都为正的情况
    if u >= 0 and v >= 0 and w >= 0:
        # 当重心坐标都为正时，可以使用多重SLERP
        if abs(u - 1.0) < 1e-10:
            return q0
        elif abs(v - 1.0) < 1e-10:
            return q1
        elif abs(w - 1.0) < 1e-10:
            return q2
        else:
            # 分步插值
            # 先在q0和q1之间插值
            if u + v > 1e-10:
                t1 = v / (u + v)
                q01 = slerp(q0, q1, t1)
            else:
                q01 = q0

            # 再在q01和q2之间插值
            if (u + v) + w > 1e-10:
                t2 = w / ((u + v) + w)
                result = slerp(q01, q2, t2)
            else:
                result = q01

            return result / np.linalg.norm(result)
    else:
        # 处理负的重心坐标（点在三角形外部）
        # 这种情况下使用加权平均的近似方法
        weights = [u, v, w]
        # 确保四元数在同一半球
        qs = [q0, q1, q2]
        for i in range(1, 3):
            if np.dot(qs[0], qs[i]) < 0:
                qs[i] = -qs[i]

        # 加权平均后标准化
        result = u * qs[0] + v * qs[1] + w * qs[2]
        norm = np.linalg.norm(result)
        if norm > 1e-10:
            return result / norm
        else:
            return np.array([1.0, 0.0, 0.0, 0.0])  # 返回单位四元数
