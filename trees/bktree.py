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

def hamming(x, y):
    assert len(x) == len(y)
    d = 0
    for x_, y_ in zip(x, y):
        if x_ != y_:
            d += 1
    return d



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
    def __init__(self, distance_fn):
        self.distance_fn = distance_fn
        self.roots = {}

    def insert(self, word):
        if not word:
            return

        initial = word[0]
        if initial in self.roots:
            cur = self.roots[initial]
            d = self.distance_fn(cur.word, word)
            while d in cur.children:
                if d == 0:
                    return
                cur = cur.children[d]
                d = self.distance_fn(cur.word, word)
            cur.add_child(word, d)
        else:
            self.roots[initial] = BKNode(word)

    def find(self, word, limit):
        if not word:
            return
        initial = word[0]
        if initial in self.roots:
            yield from self.roots[initial].find(word, self.distance_fn, limit)

    def print(self):
        for initial, root in self.roots.items():
            print(initial)
            root.print("  ")



if __name__ == "__main__":
    t = BKTree(levenshtein)
    words = ["autobus", "auto", "amerka", "amero", "amora", "amkaro", "autaro", "autora", "aurora", "autari", "au", "auvejs", "autau",
            "bekadika", "beka", "betakaroten", "beta", "betynka"]
    for w in words:
        t.insert(w)

    t.print()

    search = t.find("amera", 1)
    for s in search:
        print(s)

    t = BKTree(hamming)
    trigs = ["abc", "bca", "bbb", "abb", "bob", "abe", "acc", "cca", "aca", "cac", "cab", "aaa", "cae", "cea", "ace", "bce", "blb"]
    for w in trigs:
        t.insert(w)

    t.print()
    search = t.find("bob", 1)
    for s in search:
        print(s)

