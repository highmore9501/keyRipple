import heapq
from recorder.recorder import Recorder
from midi.midiToNotes import NotesMap

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

    def update_recorder_pool(self, notes_map: NotesMap, hand_range: int, finger_range: int):
        new_recorder_list = []
        new_recorder_heap = []
        current_real_tick = notes_map['real_tick']
        current_notes = notes_map['notes']

        for recorder in self.recorder_list:
            for next_generation_recorder in recorder.next_generation_recorders_generator(notes_map, hand_range, finger_range):
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

        # 重建列表以匹配堆中的元素
        for _, _, recorder in new_recorder_heap:
            new_recorder_list.append(recorder)

        # 更新实例变量
        self.recorder_list = new_recorder_list
        self.recorder_heap = new_recorder_heap

        # 更新最大熵值为堆顶元素的熵值
        if new_recorder_heap:
            self.max_entropy = -new_recorder_heap[0][0]
        else:
            raise Exception(
                f"没能生成新的记录器，当前real_tick为：{current_real_tick},当前音符为：{current_notes}")

    def export_pool_info(self, file_path: str):
        best_recorder = min(self.recorder_list,
                            key=lambda r: r.current_entropy)

        print(f'最优记录的熵值为：{best_recorder.current_entropy}')

        best_recorder.export_recorders(file_path)
        print(f'已保存至{file_path}')
