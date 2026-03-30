from typing import List, Any, Callable
from app.core.algorithms.heap_pq import MinHeap

def get_top_k(items: List[Any], k: int, key_func: Callable[[Any], float]) -> List[Any]:
    """
    核心算法：基于最小堆实现 Top-K 近似排序。
    满足讲义要求：“不经过完全排序可以排好前10 (Top-K问题)”
    时间复杂度: O(N log K)，空间复杂度: O(K)
    """
    if not items or k <= 0:
        return []

    heap = MinHeap()
    
    for item in items:
        score = key_func(item)
        # 用堆维持当前最大的 K 个元素
        # 注意：此处要求得最大的前K个元素，所以我们用一个容量为K的最小堆。
        # 当堆未满时，直接推入。
        # 当堆已满时，只有当前新元素的得分大于堆顶（堆内最小）的元素时，才替换它。
        if len(heap.heap) < k:
            heap.push(score, item)
        else:
            if score > heap.heap[0][0]:
                heap.pop()
                heap.push(score, item)
                
    # 此时最小堆里装的是排名前 K 的元素，但堆顶是这K个中最小的。
    # 依次弹出，得到升序序列，反转后即为降序 Top-K。
    result = []
    while not heap.is_empty():
        result.append(heap.pop()[1])
    
    result.reverse()
    return result

def edit_distance(s1: str, s2: str) -> int:
    """
    核心算法：字符串的编辑距离（Levenshtein Distance），使用动态规划(DP)实现。
    用于美食或景点名称/包含关键字的模糊查找。
    返回的距离越小，两字符串越相似。对于部分匹配，我们允许子串的最短距离。
    """
    m, n = len(s1), len(s2)
    # db[i][j] 表示 s1 的前 i 个字符与 s2 的前 j 个字符的编辑距离
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
        
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i - 1] == s2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = min(
                    dp[i - 1][j] + 1,    # 删除
                    dp[i][j - 1] + 1,    # 插入
                    dp[i - 1][j - 1] + 1 # 替换
                )
    return dp[m][n]

def fuzzy_search_filter(items: List[Any], keyword: str, text_selector: Callable[[Any], str], threshold: int = 5) -> List[Any]:
    """
    使用编辑距离过滤出与关键字相似的项。
    改进逻辑：如果关键字直接是某个item的目标子串，直接返回距离0，否则走编辑距离计算。
    """
    res = []
    kw_len = len(keyword)
    for item in items:
        text = text_selector(item)
        if keyword in text:
            # 精确子串包含给予直接匹配特权
            res.append((0, item))
        else:
            # 防止长文本对短关键词导致极大的编辑距离，我们滑动窗口求最小编辑距离近似
            min_dist = float('inf')
            # 若文本较短，直接比对
            if len(text) <= kw_len:
                min_dist = edit_distance(keyword, text)
            else:
                # 文本较长，按关键字长度分段比较求最小距离
                for i in range(len(text) - kw_len + 1):
                    sub_str = text[i : i + kw_len]
                    dist = edit_distance(keyword, sub_str)
                    if dist < min_dist:
                        min_dist = dist
            
            if min_dist <= threshold:
                res.append((min_dist, item))
    return res
