from collections import Counter
from app.core.algorithms.heap_pq import MinHeap
from typing import Dict, Tuple

class HuffmanNode:
    def __init__(self, char: str = None, freq: int = 0):
        self.char = char
        self.freq = freq
        self.left = None
        self.right = None

class HuffmanCompressor:
    """
    基于哈夫曼树（Huffman Tree）的无损压缩算法，满足大作业对日记进行压缩存储的考核要求。
    由于没有引入高级序列化包，此处将返回字符与对应的 0/1 编码。
    """
    def __init__(self):
        self.codes: Dict[str, str] = {}
        self.reverse_codes: Dict[str, str] = {}

    def compress(self, text: str) -> Tuple[str, Dict[str, str]]:
        if not text:
            return "", {}

        # 1. 统计词频
        freq_map = Counter(text)
        
        # 2. 构建最小堆 (借助成员A/B复用的堆)
        # 注意：往堆里塞入对象时，由于 MinHeap 按元组第一个元素比较
        # 我们用 (频率, 递增ID, 节点对象) 来防止频率相同时比较对象的报错
        heap = MinHeap()
        for i, (char, freq) in enumerate(freq_map.items()):
            node = HuffmanNode(char, freq)
            heap.push(freq, (i, node))

        # 3. 构建哈夫曼树
        counter_id = len(freq_map)
        while len(heap.heap) > 1:
            freq1, (_, left_node) = heap.pop()
            freq2, (_, right_node) = heap.pop()

            merged_node = HuffmanNode(freq=freq1 + freq2)
            merged_node.left = left_node
            merged_node.right = right_node

            counter_id += 1
            heap.push(merged_node.freq, (counter_id, merged_node))

        # 4. 生成编码映射表
        root = heap.pop()[1][1]
        self.codes = {}
        self.reverse_codes = {}
        self._build_codes(root, "")

        # 5. 压缩文本
        compressed_text = "".join([self.codes[char] for char in text])
        return compressed_text, self.codes

    def _build_codes(self, node: HuffmanNode, current_code: str):
        if not node:
            return
        # 叶子节点
        if node.char is not None:
            self.codes[node.char] = current_code
            self.reverse_codes[current_code] = node.char
            return

        self._build_codes(node.left, current_code + "0")
        self._build_codes(node.right, current_code + "1")

    def decompress(self, compressed_text: str, reverse_codes: Dict[str, str]) -> str:
        """根据 0/1 字符串和反向映射表解压文本"""
        if not compressed_text:
            return ""

        result = []
        current_code = ""
        for bit in compressed_text:
            current_code += bit
            if current_code in reverse_codes:
                result.append(reverse_codes[current_code])
                current_code = ""
        return "".join(result)
