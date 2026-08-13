"""Reference: B-tree (CLRS) with insert and full delete (borrow/merge)."""


class _Node:
    __slots__ = ("keys", "children", "leaf")

    def __init__(self, leaf=True):
        self.keys = []
        self.children = []
        self.leaf = leaf


class BTree:
    def __init__(self, min_degree: int = 2):
        if min_degree < 2:
            raise ValueError("min_degree must be >= 2")
        self.t = min_degree
        self.root = _Node(leaf=True)

    # ── search ──────────────────────────────────────────────────────────────
    def search(self, key: int) -> bool:
        node = self.root
        while True:
            i = 0
            while i < len(node.keys) and key > node.keys[i]:
                i += 1
            if i < len(node.keys) and key == node.keys[i]:
                return True
            if node.leaf:
                return False
            node = node.children[i]

    # ── insert (split on the way down) ──────────────────────────────────────
    def insert(self, key: int) -> None:
        if self.search(key):
            raise ValueError("duplicate key")
        root = self.root
        if len(root.keys) == 2 * self.t - 1:
            new_root = _Node(leaf=False)
            new_root.children.append(root)
            self._split_child(new_root, 0)
            self.root = new_root
        self._insert_nonfull(self.root, key)

    def _split_child(self, parent: _Node, i: int) -> None:
        t = self.t
        child = parent.children[i]
        mid = t - 1
        median = child.keys[mid]
        right = _Node(leaf=child.leaf)
        right.keys = child.keys[mid + 1:]
        if not child.leaf:
            right.children = child.children[mid + 1:]
        child.keys = child.keys[:mid]
        child.children = child.children[:mid + 1] if not child.leaf else []
        parent.keys.insert(i, median)
        parent.children.insert(i + 1, right)

    def _insert_nonfull(self, node: _Node, key: int) -> None:
        t = self.t
        i = len(node.keys) - 1
        if node.leaf:
            node.keys.append(None)
            while i >= 0 and key < node.keys[i]:
                node.keys[i + 1] = node.keys[i]
                i -= 1
            node.keys[i + 1] = key
        else:
            while i >= 0 and key < node.keys[i]:
                i -= 1
            i += 1
            if len(node.children[i].keys) == 2 * t - 1:
                self._split_child(node, i)
                if key > node.keys[i]:
                    i += 1
            self._insert_nonfull(node.children[i], key)

    # ── delete (CLRS: borrow left, borrow right, merge) ─────────────────────
    def delete(self, key: int) -> bool:
        if not self.search(key):
            return False
        self._delete(self.root, key)
        if len(self.root.keys) == 0 and not self.root.leaf:
            self.root = self.root.children[0]
        return True

    def _delete(self, node: _Node, key: int) -> None:
        t = self.t
        i = 0
        while i < len(node.keys) and key > node.keys[i]:
            i += 1
        if i < len(node.keys) and key == node.keys[i]:
            if node.leaf:
                node.keys.pop(i)
            else:
                self._delete_internal(node, i)
        else:
            if node.leaf:
                return  # not found (should not happen)
            child = node.children[i]
            if len(child.keys) < t:
                self._fill(node, i)
                # re-locate the child index after merge/borrow
                i = 0
                while i < len(node.keys) and key > node.keys[i]:
                    i += 1
            self._delete(node.children[i], key)

    def _delete_internal(self, node: _Node, i: int) -> None:
        t = self.t
        key = node.keys[i]
        left = node.children[i]
        right = node.children[i + 1]
        if len(left.keys) >= t:
            pred = self._max_key(left)
            node.keys[i] = pred
            self._delete(left, pred)
        elif len(right.keys) >= t:
            succ = self._min_key(right)
            node.keys[i] = succ
            self._delete(right, succ)
        else:
            self._merge(node, i)
            self._delete(left, key)

    @staticmethod
    def _max_key(node: _Node) -> int:
        while not node.leaf:
            node = node.children[-1]
        return node.keys[-1]

    @staticmethod
    def _min_key(node: _Node) -> int:
        while not node.leaf:
            node = node.children[0]
        return node.keys[0]

    def _fill(self, node: _Node, i: int) -> None:
        t = self.t
        if i > 0 and len(node.children[i - 1].keys) >= t:
            self._borrow_prev(node, i)
        elif i < len(node.children) - 1 and len(node.children[i + 1].keys) >= t:
            self._borrow_next(node, i)
        else:
            if i < len(node.children) - 1:
                self._merge(node, i)
            else:
                self._merge(node, i - 1)

    def _borrow_prev(self, node: _Node, i: int) -> None:
        child = node.children[i]
        left = node.children[i - 1]
        child.keys.insert(0, node.keys[i - 1])
        node.keys[i - 1] = left.keys.pop()
        if not left.leaf:
            child.children.insert(0, left.children.pop())

    def _borrow_next(self, node: _Node, i: int) -> None:
        child = node.children[i]
        right = node.children[i + 1]
        child.keys.append(node.keys[i])
        node.keys[i] = right.keys.pop(0)
        if not right.leaf:
            child.children.append(right.children.pop(0))

    def _merge(self, node: _Node, i: int) -> None:
        left = node.children[i]
        right = node.children[i + 1]
        left.keys.append(node.keys.pop(i))
        left.keys.extend(right.keys)
        if not left.leaf:
            left.children.extend(right.children)
        node.children.pop(i + 1)

    # ── traversal ───────────────────────────────────────────────────────────
    def keys(self) -> list[int]:
        out = []

        def walk(n: _Node):
            if n.leaf:
                out.extend(n.keys)
                return
            for idx, k in enumerate(n.keys):
                walk(n.children[idx])
                out.append(k)
            walk(n.children[len(n.keys)])

        walk(self.root)
        return out
