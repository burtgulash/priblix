#!/usr/bin/python3

import collections

class Candidate:
    def __init__(self, doc_id, word_occurrences):
        self.doc_id = doc_id
        self.last_occurrences = word_occurrences
        self.min_dist = 0

    def __repr__(self):
        return "Candidate({}, {}, {})".format(self.doc_id, self.min_dist, self.last_occurrences)

def groupped_occurrences(occurrences):
    d = collections.defaultdict(list)
    for word, pos in occurrences:
        d[word].append(pos)
    return d

def min_dist(xpositions, ypositions):
    m = 1000
    for x in xpositions:
        for y in ypositions:
            if x < y:
                if y - x - 1 < m:
                    m = y - x - 1
            else:
                if x - y < m:
                    m = x - y
            if m <= 0:
                return 0
    return m

class I:
    def __init__(self):
        self._index = collections.defaultdict(list)

    def analyse(self, record):
        words = record.split(" ")
        return [(word, pos) for pos, word in enumerate(words)]

    def index(self, records):
        for doc_id, record in enumerate(records):
            occurrences = self.analyse(record)
            for word, positions in groupped_occurrences(occurrences).items():
                self._index[word].append((doc_id, sorted(positions)))

    def find_one(self, word):
        docs = self._index.get(word, [])
        return [Candidate(doc_id, positions) for doc_id, positions in docs]

    def find(self, query):
        occurrences = self.analyse(query)
        if not occurrences:
            return []

        word, _ = occurrences[0]
        candidates = self.find_one(word)
        for word, pos in occurrences[1:]:
            new_candidates = self.find_one(word)
            candidates = self.merge(candidates, new_candidates)

        return candidates

    def merge(self, xs, ys):
        cs = []
        ix = iy = 0
        print("merging", xs, ys)
        while ix < len(xs) and iy < len(ys):
            cndx, cndy = xs[ix], ys[iy]
            if cndx.doc_id < cndy.doc_id:
                ix += 1
            elif cndx.doc_id > cndy.doc_id:
                iy += 1
            else:
                xpositions = cndx.last_occurrences
                ypositions = cndy.last_occurrences
                c = Candidate(cndx.doc_id, ypositions)
                c.min_dist = cndx.min_dist + min_dist(xpositions, ypositions)
                cs.append(c)
                ix, iy = ix + 1, iy + 1

        return cs

    def translate_docs(self, result, records):
        return [
            (records[cnd.doc_id], cnd.min_dist)
            for cnd in result
        ]



if __name__ == "__main__":
    records = [
        "auto jede po silnici",
        "auto se vysralo na silnici",
        "po seste hodine se podivame",
        "podivame se na podivanou",
        "v seste se vysralo",
        "neserte se na sestou",
        "na silnici se sere velmi tezce",
        "auto se tezce neslo",
        "ono se vysralo po seste",
        "na kravate jelo auto po mesici",
        "no to jsem se mohl vysrat a podivanou taky",
        "taky auto jelo srat",
        "neslo se vysrat mimo silnici",
        "tak to v seste hodine taky",
        "seste hodine se vysralo tezce",
    ]

    x = I()
    x.index(records)
    y = x.find("hodine seste")
    print("found:", x.translate_docs(y, records))
