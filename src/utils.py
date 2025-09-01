"""
这里所有方法成立的前提是假设键盘横方向正好是x轴，键盘放置在xy平面内,键盘演奏者的朝向是y轴正方向
"""

import numpy as np
from src.piano.piano import Piano
from typing import Any
import math


def generate_finger_distribution(num_fingers: int) -> list[int]:
    """   
    Args:
        num_fingers: 手指总数

    Returns:
        list: 每个手指的坐标位置，从左到右排列
    """
    if num_fingers <= 0:
        return []

    positions = []

    if num_fingers % 2 == 1:  # 奇数个手指
        center = num_fingers // 2
        for i in range(num_fingers):
            distance_from_center = i - center
            if distance_from_center == 0:
                positions.append(0)
            elif distance_from_center > 0:
                positions.append(distance_from_center * 2)
            else:
                positions.append(distance_from_center * 2)
    else:  # 偶数个手指
        left_center = num_fingers // 2 - 0.5
        for i in range(num_fingers):
            distance_from_center = i - left_center
            positions.append(int(distance_from_center * 2))

    return positions


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
    return: 按键的最靠演奏者处的位置
    """
    white_key_distance = (highest_key_position[0] -
                          lowest_key_position[0]) / (piano.numberOfWhiteKeys-1)
    white_keys = piano.white_keys

    if not is_black:
        key_index = white_keys.index(note)
        key_position_x = lowest_key_position[0] + \
            white_key_distance * key_index
        # 如果是白键，返回的位置x坐标是经过计算的，y和z坐标直接都是读取的highest_key_position的值
        key_position = np.array(
            [key_position_x, highest_key_position[1], highest_key_position[2]])
    else:
        pre_key_index = white_keys.index(note - 1)
        key_position_x = lowest_key_position[0] + \
            white_key_distance * (pre_key_index + 0.5)
        # 如果是黑键，返回的位置x坐标是经过计算的，y和z坐标直接都是读取的black_key_position的值
        key_position = np.array(
            [key_position_x, black_key_position[1], black_key_position[2]])

    return key_position


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


def tan_weight_transform(q0: np.ndarray, q1: np.ndarray, t: float):
    """
    基于tangent值的权重变换函数示例

    参数:
    q0: 第一个点的旋转值
    q1: 第二个点的旋转值
    t: 原始权重值 [0, 1]

    返回:
    变换后的权重值
    """
    # 计算两个旋转值的夹角大小
    angle = np.arccos(np.dot(q0, q1))
    # 如果夹角大小为0，则返回原始权重值
    if angle == 0:
        return t
    # 计算夹角的tangent值
    tangent = np.tan(angle)
    # 计算插值点的tangent值
    t_interpolated = tangent * t
    # 计算插值点的旋转角度
    angle_interpolated = np.arctan(t_interpolated)

    return angle_interpolated / angle


def evaluate_2d_point(coefficients, point) -> np.ndarray:
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


def get_actual_press_depth(lowest_key_position: np.ndarray, touch_position: np.ndarray) -> float:
    """
    计算实际按键深度

    参数:
    is_black: 是否为黑键
    lowest_key_position: 最低键的坐标    
    touch_position: 触摸点的坐标

    返回:
    实际按键深度
    """
    diff_y: float = abs(touch_position[1] - lowest_key_position[1])

    return diff_y * math.sin(math.radians(15))


def lerp(a: np.ndarray, b: np.ndarray, t: float) -> np.ndarray:
    if t <= 0:
        return a
    if t >= 1:
        return b

    if len(a) != len(b):
        raise ValueError("Arrays must have the same length")

    if len(a) != 4:
        return a + t * (b - a)
    else:
        t = tan_weight_transform(a, b, t)
        return slerp(a, b, t)


def lerp_with_key_type_and_position(white_key_value: int, position: int, high_position: int, middle_position: int, low_position: int, high_white: np.ndarray, high_black: np.ndarray, middle_white: np.ndarray, middle_black: np.ndarray, low_white: np.ndarray, low_black: np.ndarray) -> np.ndarray:
    middle_value = middle_white if white_key_value == 1 else middle_black
    high_value = high_white if white_key_value == 1 else high_black
    low_value = low_white if white_key_value == 1 else low_black

    if position < middle_position:
        t = (position - low_position) / (middle_position - low_position)
        return lerp(low_value, middle_value, t)
    else:
        t = (position-middle_position) / (high_position - middle_position)
        return lerp(middle_value, high_value, t)
