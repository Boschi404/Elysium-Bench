"""Reference: iterative segment tree for range sum + range min."""
class SegmentTree:
    def __init__(self, values: list[int]):
        self.n = len(values)
        size = 1
        while size < self.n:
            size <<= 1
        self.size = size
        INF = float("inf")
        self.sum = [0] * (2 * size)
        self.mn = [INF] * (2 * size)
        for i, v in enumerate(values):
            self.sum[size + i] = v
            self.mn[size + i] = v
        for i in range(size - 1, 0, -1):
            self.sum[i] = self.sum[2 * i] + self.sum[2 * i + 1]
            self.mn[i] = min(self.mn[2 * i], self.mn[2 * i + 1])

    def _check_range(self, left, right):
        if left > right:
            raise ValueError("left must be <= right")
        if left < 0 or right >= self.n:
            raise IndexError("index out of range")

    def range_sum(self, left: int, right: int) -> int:
        self._check_range(left, right)
        l = left + self.size
        r = right + self.size
        total = 0
        while l <= r:
            if l % 2 == 1:
                total += self.sum[l]
                l += 1
            if r % 2 == 0:
                total += self.sum[r]
                r -= 1
            l //= 2
            r //= 2
        return total

    def range_min(self, left: int, right: int) -> int:
        self._check_range(left, right)
        l = left + self.size
        r = right + self.size
        best = float("inf")
        while l <= r:
            if l % 2 == 1:
                best = min(best, self.mn[l])
                l += 1
            if r % 2 == 0:
                best = min(best, self.mn[r])
                r -= 1
            l //= 2
            r //= 2
        return best

    def update(self, index: int, value: int) -> None:
        if index < 0 or index >= self.n:
            raise IndexError("index out of range")
        i = index + self.size
        self.sum[i] = value
        self.mn[i] = value
        i //= 2
        while i >= 1:
            self.sum[i] = self.sum[2 * i] + self.sum[2 * i + 1]
            self.mn[i] = min(self.mn[2 * i], self.mn[2 * i + 1])
            i //= 2
