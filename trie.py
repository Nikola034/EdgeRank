class TrieNode:
    def __init__(self, char):
        self.char = char
        self.is_end = False
        self.children = {}
        self.count = 0


class Trie:
    def __init__(self):
        self.root = TrieNode("")

    def insert(self, word):
        node = self.root

        for char in word:
            if char in node.children:
                node = node.children[char]
            else:
                new_node = TrieNode(char)
                node.children[char] = new_node
                node = new_node

        node.is_end = True
        node.count += 1

    def dfs(self, node, pre):
        if node.is_end:
            self.output.append((pre + node.char, node.count))

        for child in node.children.values():
            self.dfs(child, pre + node.char)

    def search(self, word):
        node = self.root

        for char in word:
            if char in node.children:
                node = node.children[char]
            else:
                return []

        if node.is_end:
            return [(word, node.count)]
        else:
            return []

    def prefix(self, x):
        node = self.root
        for char in x:
            if char in node.children:
                node = node.children[char]
            else:
                return []

        self.output = []
        self.dfs(node, x[:-1])

        return self.output

