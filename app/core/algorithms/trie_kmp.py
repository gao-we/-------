from typing import List, Dict

class TrieNode:
    def __init__(self):
        self.children: Dict[str, 'TrieNode'] = {}
        self.is_end_of_word = False
        # 记录包含该关键字的日记ID列表（用于粗略的倒排索引功能）
        self.diary_ids: set = set()

class Trie:
    """
    字典树(Trie)，用于日记关键词的结构化存储和快速前缀/精确搜索。
    不仅用于匹配，还能作为简单的倒排索引映射关键词到对应的日记ID。
    """
    def __init__(self):
        self.root = TrieNode()

    def insert(self, word: str, diary_id: str):
        node = self.root
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
            # 路径上的前缀也可以挂载日记，实现某些前缀搜索
            node.diary_ids.add(diary_id)
        node.is_end_of_word = True

    def search_prefix(self, prefix: str) -> set:
        """根据前缀搜索相关日记 ID"""
        node = self.root
        for char in prefix:
            if char not in node.children:
                return set()
            node = node.children[char]
        return node.diary_ids

def build_kmp_lps(pattern: str) -> List[int]:
    """计算 KMP 算法的 LPS (Longest Proper Prefix which is also Suffix) 数组"""
    m = len(pattern)
    lps = [0] * m
    length = 0
    i = 1
    while i < m:
        if pattern[i] == pattern[length]:
            length += 1
            lps[i] = length
            i += 1
        else:
            if length != 0:
                length = lps[length - 1]
            else:
                lps[i] = 0
                i += 1
    return lps

def kmp_search(text: str, pattern: str) -> bool:
    """
    KMP (Knuth-Morris-Pratt) 字符串匹配算法。
    用于在长短文日记内容中进行 O(N+M) 复杂度的全文精确检索。
    """
    n = len(text)
    m = len(pattern)
    if m == 0:
        return True

    lps = build_kmp_lps(pattern)
    i = 0  # text index
    j = 0  # pattern index

    while i < n:
        if pattern[j] == text[i]:
            i += 1
            j += 1

        if j == m:
            return True  # 找到了匹配
            # j = lps[j - 1] # 如果要找所有匹配，解开注释
        elif i < n and pattern[j] != text[i]:
            if j != 0:
                j = lps[j - 1]
            else:
                i += 1
    return False
