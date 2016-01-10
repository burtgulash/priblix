#!/usr/bin/python3


def levenshtein(x, y):
    d = [[0 for j in range(len(y) + 1)] for i in range(len(x) + 1)]
    for i in range(1, len(x) + 1):
        d[i][0] = i
    for j in range(1, len(y) + 1):
        d[0][j] = j
    for i in range(1, len(x) + 1):
        for j in range(1, len(y) + 1):
            if x[i - 1] == y[j - 1]:
                d[i][j] = d[i - 1][j - 1]
            else:
                d[i][j] = min(d[i - 1][j] + 1,
                              d[i][j - 1] + 1,
                              d[i - 1][j - 1] + 1)
    return d[len(x)][len(y)]


class BKNode:
    def __init__(self, word):
        self.word = word
        self.children = {}

    def add_child(self, word, d):
        assert d not in self.children
        if d != 0:
            self.children[d] = BKNode(word)

    def find(self, word, distance_fn, limit):
        d = distance_fn(self.word, word)
        if d <= limit:
            yield self.word
        for x in range(d - limit, d + limit + 1):
            if x in self.children:
                yield from self.children[x].find(word, distance_fn, limit)

    def print(self, indent):
        print(indent + self.word)
        for d, child in self.children.items():
            print(indent + str(d))
            child.print(indent + "  ")


class BKTree:
    def __init__(self):
        self.roots = {}

    def insert(self, word, distance_fn):
        if not word:
            return

        initial = word[0]
        if initial in self.roots:
            cur = self.roots[initial]
            d = distance_fn(cur.word, word)
            while d in cur.children:
                if d == 0:
                    return
                cur = cur.children[d]
                d = distance_fn(cur.word, word)
            cur.add_child(word, d)
        else:
            self.roots[initial] = BKNode(word)

    def find(self, word, distance_fn, limit):
        if not word:
            return
        initial = word[0]
        if initial in self.roots:
            yield from self.roots[initial].find(word, distance_fn, limit)

    def print(self):
        for initial, root in self.roots.items():
            print(initial)
            root.print("  ")



if __name__ == "__main__":
    t = BKTree()
    words = ["autobus", "auto", "amerka", "amero", "amora", "amkaro", "autaro", "autora", "aurora", "autari", "au", "auvejs", "autau",
            "bekadika", "beka", "betakaroten", "beta", "betynka"]
    for w in words:
        t.insert(w, levenshtein)

    t.print()

    search = t.find("amera", levenshtein, 1)
    for s in search:
        print(s)
