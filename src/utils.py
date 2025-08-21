"""
这里所有方法成立的前提是假设键盘横方向正好是x轴，键盘放置在xy平面内,键盘演奏者的朝向是y轴正方向
"""

import numpy as np
from src.piano.keyNote import KeyNote
from src.piano.piano import Piano


def get_touch_point(finger_position: np.ndarray, key_position: np.ndarray) -> np.ndarray:
    """
    获取手指在按键上的接触点
    param finger_position: 手指位置
    param key_position: 按键中点位置    
    """
    # 检测参数是否合法
    if len(finger_position) != 3 or len(key_position) != 3:
        raise ValueError("位置参数长度错误")

    return np.array([key_position[0], max(finger_position[1], key_position[1]), key_position[2]])


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
            raise ValueError("三个点共线，无法确定唯一的二维平面函数")

    # 将系数组合成矩阵，形状为 (n_dims, 3)
    coefficients = np.array(coefficients_list)

    # 检测系数的形状
    if coefficients.shape[0] != n_dims:
        raise ValueError("系数矩阵的维度与属性值的维度不一致")

    return coefficients


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
