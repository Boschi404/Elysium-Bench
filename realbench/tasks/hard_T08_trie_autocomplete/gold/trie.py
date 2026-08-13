"""Reference: Trie with distinct-word counts."""
class _Node:
    __slots__ = ("children", "is_word", "count")

    def __init__(self):
        self.children = {}
        self.is_word = False
        self.count = 0  # distinct words in this subtree


class Trie:
    def __init__(self):
        self.root = _Node()

    def insert(self, word: str) -> None:
        node = self.root
        for ch in word:
            if ch not in node.children:
                node.children[ch] = _Node()
            node = node.children[ch]
        if not node.is_word:
            node.is_word = True
            # propagate count increment along the path
            cur = self.root
            for ch in word:
                cur.count += 1
                cur = cur.children[ch]
            cur.count += 1

    def _walk(self, prefix: str):
        node = self.root
        for ch in prefix:
            if ch not in node.children:
                return None
            node = node.children[ch]
        return node

    def search(self, word: str) -> bool:
        node = self._walk(word)
        return node is not None and node.is_word

    def starts_with(self, prefix: str) -> bool:
        if prefix == "":
            return self.root.count > 0
        return self._walk(prefix) is not None

    def count_prefix(self, prefix: str) -> int:
        node = self._walk(prefix)
        return node.count if node else 0

    def autocomplete(self, prefix: str, k: int) -> list[str]:
        if k <= 0:
            raise ValueError("k must be > 0")
        node = self._walk(prefix)
        if node is None:
            return []
        out = []
        stack = [(node, prefix)]
        while stack and len(out) < k:
            nd, path = stack.pop()
            if nd.is_word:
                out.append(path)
                if len(out) == k:
                    break
            for ch in sorted(nd.children, reverse=True):
                stack.append((nd.children[ch], path + ch))
        return out
