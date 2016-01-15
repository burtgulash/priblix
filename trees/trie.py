#!/usr/bin/python3

class TrieNode:
    __slots__ = "word", "is_word", "children"

    def __init__(self, word, is_word):
        self.word = word
        self.is_word = is_word
        self.children = {}

    def descendants_or_self(self):
        if self.is_word:
            yield self.word
        for c, child in self.children.items():
            yield from child.descendants_or_self()

class Trie:

    def __init__(self):
        self.root = TrieNode("", False)

    def descendants_or_self(self, prefix):
        cur = self.root
        for i, c in enumerate(prefix):
            if c in cur.children:
                cur = cur.children[c]
            else:
                return []

        return list(cur.descendants_or_self())

    def find(self, word):
        cur = self.root
        for i, c in enumerate(word):
            if c in cur.children:
                cur = cur.children[c]
            else:
                return None

        if cur.is_word:
            assert cur.word == word
            return cur.word

        return None

    def insert(self, word):
        cur = self.root
        for i, c in enumerate(word[:-1]):
            if c in cur.children:
                cur = cur.children[c]
            else:
                for j, c in enumerate(word[i:-1]):
                    new = TrieNode(None, False)
                    cur.children[c] = new
                    cur = new
                break

        last_char = word[-1]
        if last_char in cur.children:
            cur.children[last_char].is_word = True
            cur.children[last_char].word = word
        else:
            cur.children[last_char] = TrieNode(word, True)

    def __str__(self):
        s = []
        def _s(node, char, res, lvl):
            word = node.word + " +" if node.is_word else char
            res.append(lvl * " " + word)
            for char, child in node.children.items():
                _s(child, char, res, lvl + 1)
        _s(self.root, "", s, 0)
        return "\n".join(s)


if __name__ == "__main__":
    t = Trie()
    t.insert("auto")
    t.insert("autobus")
    t.insert("autaky")
    t.insert("autus")
    t.insert("autusak")
    t.insert("betarozpad")
    t.insert("betakaroten")
    t.insert("aarkvard")
    t.insert("kokolino")
    t.insert("kokino")
    t.insert("kokinko")
    t.insert("kolinko")

    print(t)
    for x in t.descendants_or_self("ko"):
        print(x)
