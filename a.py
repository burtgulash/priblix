#!/usr/bin/python3

import collections
import re

class Candidate:
    def __init__(self, doc_id, word_occurrences, highlights):
        self.doc_id = doc_id
        self.last_occurrences = word_occurrences
        self.min_dist = 0
        self.highlights = highlights

    def __repr__(self):
        return "Candidate({}, {}, {})".format(self.doc_id, self.min_dist, self.last_occurrences)

class RecordPosition:
    def __init__(self, char_position, word_position):
        self.char_position = char_position
        self.word_position = word_position

def min_dist(xpositions, ypositions):
    m = 1337
    for x in xpositions:
        x = x.word_position
        for y in ypositions:
            y = y.word_position
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

    def tokenize(self, record):
        words = re.split("\W+", record)
        return words

    def add_token_offsets(self, record, tokens):
        terms = []
        rec_i = 0
        for tok_i, token in enumerate(tokens):
            assert rec_i < len(record)
            while not record[rec_i:].startswith(token):
                rec_i += 1
            terms.append( (token, RecordPosition(rec_i, tok_i)) )
        return terms

    def group_occurrences(self, occurrences):
        d = collections.defaultdict(list)
        for word, record_position in occurrences:
            d[word].append(record_position)
        return d

    def index(self, records):
        for doc_id, record in enumerate(records):
            tokens = self.tokenize(record)
            occurrences = self.add_token_offsets(record, tokens)
            for word, record_positions in self.group_occurrences(occurrences).items():
                self._index[word].append((doc_id, record_positions)) # TODO add compare method to recordpos and sort them. Then change the algorithm for mindist to be linear instead of quadratic

    def find_one(self, word):
        docs_found = self._index.get(word, [])
        result = []
        for doc_id, record_positions in docs_found:
            highlights = [
                (rp.char_position, rp.char_position + len(word))
                for rp in record_positions
            ]
            result.append(Candidate(doc_id, record_positions, highlights))
        return result

    def find(self, query):
        tokens = self.tokenize(query)
        if not tokens:
            return []

        candidates = self.find_one(tokens[0])
        for token in tokens[1:]:
            new_candidates = self.find_one(token)
            candidates = self.merge(candidates, new_candidates)

        return candidates

    def merge(self, xs, ys):
        cs = []
        ix = iy = 0
        while ix < len(xs) and iy < len(ys):
            cndx, cndy = xs[ix], ys[iy]
            if cndx.doc_id < cndy.doc_id:
                ix += 1
            elif cndx.doc_id > cndy.doc_id:
                iy += 1
            else:
                xpositions = cndx.last_occurrences
                ypositions = cndy.last_occurrences
                c = Candidate(cndx.doc_id, ypositions, cndx.highlights + cndy.highlights)
                c.min_dist = cndx.min_dist + min_dist(xpositions, ypositions)
                cs.append(c)
                ix, iy = ix + 1, iy + 1

        return cs

    def translate_docs(self, result, records):
        return sorted(
            (cnd.min_dist, records[cnd.doc_id])
            for cnd in result
        )



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
    y = x.find("na po")
    print("found:", x.translate_docs(y, records))
