class MinHeap:
    """
    手写的最小堆（Min-Heap），用于实现优先队列（Priority Queue）。
    这是数据结构大作业考核要求的核心基础数据结构之一！
    """
    def __init__(self):
        self.heap = []

    def parent(self, index):
        return (index - 1) // 2

    def left_child(self, index):
        return 2 * index + 1

    def right_child(self, index):
        return 2 * index + 2

    def push(self, weight, item):
        """插入一个元素 (weight, item)"""
        self.heap.append((weight, item))
        self._sift_up(len(self.heap) - 1)

    def pop(self):
        """弹出权重最小的元素"""
        if self.is_empty():
            return None
        
        if len(self.heap) == 1:
            return self.heap.pop()

        min_elem = self.heap[0]
        # 将末尾元素移到根节点，然后下沉
        self.heap[0] = self.heap.pop()
        self._sift_down(0)
        
        return min_elem

    def is_empty(self):
        return len(self.heap) == 0

    def _sift_up(self, index):
        while index > 0:
            p_idx = self.parent(index)
            # 如果当前节点权重小于父节点，则交换
            if self.heap[index][0] < self.heap[p_idx][0]:
                self.heap[index], self.heap[p_idx] = self.heap[p_idx], self.heap[index]
                index = p_idx
            else:
                break

    def _sift_down(self, index):
        size = len(self.heap)
        while True:
            smallest = index
            left = self.left_child(index)
            right = self.right_child(index)

            # 找出左右子节点中最小的那个
            if left < size and self.heap[left][0] < self.heap[smallest][0]:
                smallest = left
            if right < size and self.heap[right][0] < self.heap[smallest][0]:
                smallest = right

            if smallest != index:
                self.heap[index], self.heap[smallest] = self.heap[smallest], self.heap[index]
                index = smallest
            else:
                break
