from typing import Any, Iterator, List, Optional, Tuple


class _Entry:
    def __init__(self, key: Any, value: Any):
        self.key = key
        self.value = value


class SimpleHashMap:
    """
    课程设计用手写哈希表（拉链法）。
    """

    def __init__(self, initial_capacity: int = 16):
        capacity = 16
        while capacity < initial_capacity:
            capacity *= 2
        self._buckets: List[List[_Entry]] = [[] for _ in range(capacity)]
        self._size = 0

    def _bucket_index(self, key: Any) -> int:
        return hash(key) & (len(self._buckets) - 1)

    def _resize_if_needed(self):
        if self._size * 10 < len(self._buckets) * 7:
            return
        old_buckets = self._buckets
        self._buckets = [[] for _ in range(len(old_buckets) * 2)]
        self._size = 0
        for bucket in old_buckets:
            for entry in bucket:
                self.put(entry.key, entry.value)

    def put(self, key: Any, value: Any):
        idx = self._bucket_index(key)
        bucket = self._buckets[idx]
        for entry in bucket:
            if entry.key == key:
                entry.value = value
                return
        bucket.append(_Entry(key, value))
        self._size += 1
        self._resize_if_needed()

    def get(self, key: Any, default: Any = None) -> Any:
        idx = self._bucket_index(key)
        for entry in self._buckets[idx]:
            if entry.key == key:
                return entry.value
        return default

    def contains(self, key: Any) -> bool:
        idx = self._bucket_index(key)
        for entry in self._buckets[idx]:
            if entry.key == key:
                return True
        return False

    def remove(self, key: Any) -> bool:
        idx = self._bucket_index(key)
        bucket = self._buckets[idx]
        for i, entry in enumerate(bucket):
            if entry.key == key:
                del bucket[i]
                self._size -= 1
                return True
        return False

    def items(self) -> Iterator[Tuple[Any, Any]]:
        for bucket in self._buckets:
            for entry in bucket:
                yield entry.key, entry.value

    def keys(self) -> Iterator[Any]:
        for key, _ in self.items():
            yield key

    def values(self) -> Iterator[Any]:
        for _, value in self.items():
            yield value

    def __len__(self) -> int:
        return self._size


class SimpleHashSet:
    """
    课程设计用手写集合（基于手写哈希表）。
    """

    def __init__(self, initial_values: Optional[List[Any]] = None):
        self._map = SimpleHashMap()
        if initial_values:
            for value in initial_values:
                self.add(value)

    def add(self, value: Any):
        self._map.put(value, True)

    def contains(self, value: Any) -> bool:
        return self._map.contains(value)

    def remove(self, value: Any) -> bool:
        return self._map.remove(value)

    def is_empty(self) -> bool:
        return len(self._map) == 0

    def values(self) -> List[Any]:
        return [key for key in self._map.keys()]

    def __len__(self) -> int:
        return len(self._map)


class FrequencyTable:
    """
    字符词频表（基于手写哈希表）。
    """

    def __init__(self):
        self._counter = SimpleHashMap()

    def add(self, token: str):
        current = self._counter.get(token, 0)
        self._counter.put(token, current + 1)

    def items(self) -> Iterator[Tuple[str, int]]:
        return self._counter.items()
