import heapq
from src.recorder.recorder import Recorder
from src.midi.midiToNotes import NotesMap
from src.hand.hand import Hand

# 定义堆中元素的类型
HeapElement = tuple[float, int, Recorder]


class RecorderPool():
    def __init__(self, recorders: list[Recorder], pool_size: int, max_entropy: int):
        self.pool_size = pool_size
        self.max_entropy = max_entropy
        # 堆用于快速查找最大熵值记录器
        self.recorder_heap: list[HeapElement] = []
        # 列表维护插入顺序
        self.recorder_list: list[Recorder] = []

        # 初始化
        for recorder in recorders:
            self._add_recorder(recorder)

    def _add_recorder(self, recorder: Recorder):
        # 添加到维护顺序的列表
        self.recorder_list.append(recorder)

        # 添加到堆（用于快速查找）
        heapq.heappush(self.recorder_heap,
                       (-recorder.current_entropy, id(recorder), recorder))

        # 更新最大熵值
        if recorder.current_entropy > self.max_entropy:
            self.max_entropy = recorder.current_entropy

    def update_recorder_pool(self, notes_map: NotesMap, hand_range: int, finger_range: float, finger_distribution: list[int]):
        new_recorder_list = []
        new_recorder_heap = []
        current_notes = notes_map['notes']
        current_frame: float = notes_map['frame']

        for recorder in self.recorder_list:
            for next_generation_recorder in recorder.next_generation_recorders_generator(notes_map, hand_range, finger_range, finger_distribution):
                # 检查是否应该添加新记录器
                if len(new_recorder_heap) < self.pool_size:
                    # 如果池未满，直接添加
                    new_recorder_list.append(next_generation_recorder)
                    heapq.heappush(new_recorder_heap,
                                   (-next_generation_recorder.current_entropy,
                                    id(next_generation_recorder),
                                    next_generation_recorder))
                elif next_generation_recorder.current_entropy < -new_recorder_heap[0][0]:
                    # 如果池已满且新记录器熵值小于当前最大熵，则替换
                    heapq.heapreplace(new_recorder_heap,
                                      (-next_generation_recorder.current_entropy,
                                       id(next_generation_recorder),
                                       next_generation_recorder))
                    # 注意：这里需要同步更新列表，但因为列表无序，直接清空重建更简单
                    new_recorder_list = []  # 重建列表

        # 如果没有生成任何新的记录器，则保持原状态并输出信息
        if not new_recorder_heap:
            print(
                f"警告：没能生成新的记录器，当前frame为：{current_frame},当前音符为：{current_notes}")
            print("只保留原最佳记录，并且更新frame")
            self.repeat_self(current_frame)
            return

        # 重建列表以匹配堆中的元素
        for _, _, recorder in new_recorder_heap:
            new_recorder_list.append(recorder)

        # 更新实例变量
        self.recorder_list = new_recorder_list
        self.recorder_heap = new_recorder_heap

        # 更新最大熵值为堆顶元素的熵值
        if new_recorder_heap:
            self.max_entropy = -new_recorder_heap[0][0]

    def repeat_self(self, current_frame: float):
        """
        当无法生成新的记录器时，复制最佳记录器,添加一个和最后手型相似但所有手指pressed都相反的手型，并更新frame值

        Args:
            real_tick: 新的时间戳
        """
        if not self.recorder_list:
            return

        # 找到熵值最小（最佳）的记录器
        best_recorder = min(self.recorder_list,
                            key=lambda r: r.current_entropy)

        # 创建新的Recorder实例，复制所有属性但更新frame和frames
        new_frames = best_recorder.frames[:]
        new_frame = current_frame

        new_left_hands = best_recorder.left_hands[:]
        latest_left_hand = best_recorder.left_hands[-1]
        new_left_fingers = latest_left_hand.fingers[:]
        for left_finger in new_left_fingers:
            left_finger.pressed = not left_finger.pressed
        new_left_hand = Hand(new_left_fingers,
                             latest_left_hand.piano,
                             True,
                             max_distance=latest_left_hand.max_distance,
                             finger_number=latest_left_hand.finger_number)
        new_left_hands.append(new_left_hand)

        new_right_hands = best_recorder.right_hands[:]
        latest_right_hand = best_recorder.right_hands[-1]
        new_right_fingers = latest_right_hand.fingers[:]
        for right_finger in new_right_fingers:
            right_finger.pressed = not right_finger.pressed
        new_right_hand = Hand(new_right_fingers,
                              latest_right_hand.piano,
                              False,
                              max_distance=latest_right_hand.max_distance,
                              finger_number=latest_right_hand.finger_number)
        new_right_hands.append(new_right_hand)

        repeated_recorder = Recorder(
            piano=best_recorder.piano,
            left_hands=new_left_hands,
            right_hands=new_right_hands,
            current_entropy=best_recorder.current_entropy,
            frame=new_frame,
            frames=new_frames
        )

        # 清空现有记录器列表和堆
        self.recorder_list = [repeated_recorder]
        self.recorder_heap = []

        # 重新构建堆
        heapq.heappush(self.recorder_heap,
                       (-repeated_recorder.current_entropy, id(repeated_recorder), repeated_recorder))

    def export_pool_info(self, file_path: str):
        best_recorder: Recorder = min(self.recorder_list,
                                      key=lambda r: r.current_entropy)

        print(f'最优记录的熵值为：{best_recorder.current_entropy}')

        best_recorder.export_recorders(file_path)
        print(f'已保存至{file_path}')
