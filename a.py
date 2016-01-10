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

    def __repr__(self):
        return "Position({}, {})".format(self.char_position, self.word_position)

def min_dist(xpositions, ypositions):
    d = 1337
    top, bottom = xpositions, ypositions
    topi, bottomi = 0, 0
    switched = False

    while topi < len(top):
        topx = top[topi].word_position
        bottomx = bottom[bottomi].word_position
        diff = bottomx - topx

        # increase the top row while its elements are smaller than element at
        # bottom position. Then swap top and bottom
        if topx > bottomx:
            top, bottom = bottom, top
            topi, bottomi = bottomi, topi
            diff = -diff
            switched = not switched

        # if first token doesn't precede the second token in the result, add a penalty to the score
        if switched:
            diff += 1

        # set min_dist if better found
        if diff < d:
            # if minimum reached, return it immediately
            if diff <= 0:
                return 0
            d = diff

        topi += 1

    return d


class Index:
    def __init__(self, records):
        self.records = records
        self.index = self._index(records)

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

    def search(self, query):
        candidates = self._find_phrase(query)
        highlighted_docs = self.retrieve_records_and_highlight(candidates)
        return sorted(highlighted_docs)


    def _group_occurrences(self, occurrences):
        d = collections.defaultdict(list)
        for word, record_position in occurrences:
            d[word].append(record_position)
        return d

    def _index(self, records):
        index = collections.defaultdict(list)
        for doc_id, record in enumerate(records):
            tokens = self.tokenize(record)
            occurrences = self.add_token_offsets(record, tokens)
            for word, record_positions in self._group_occurrences(occurrences).items():
                index[word].append((doc_id, record_positions))
        return index

    def _find_one(self, word):
        docs_found = self.index.get(word, [])
        result = []
        for doc_id, record_positions in docs_found:
            highlights = [
                (rp.char_position, rp.char_position + len(word))
                for rp in record_positions
            ]
            result.append(Candidate(doc_id, record_positions, highlights))
        return result

    def _find_phrase(self, query):
        tokens = self.tokenize(query)
        if not tokens:
            return []

        candidates = self._find_one(tokens[0])
        for token in tokens[1:]:
            new_candidates = self._find_one(token)
            candidates = self._merge(candidates, new_candidates)

        return candidates

    def _merge(self, xs, ys):
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

    def _merge_highlights(self, highlights):
        highlights = sorted(highlights)
        result = []
        hlstart, hlend = 0, 0
        for start, end in highlights:
            if start <= hlend:
                hlend = end
            else:
                result.append( (hlstart, hlend) )
                hlstart, hlend = start, end

        # also include the last one
        result.append( (hlstart, hlend) )

        return highlights

    def _highlight_record(self, record, highlights):
        normal = "\033[m"
        bold = "\033[1m"

        yellow_back = "\033[103m"
        normal_back = "\033[49m"

        result = []
        last = 0
        for start, end in highlights:
            result.append(record[last:start])
            result.append(yellow_back + record[start:end] + normal_back)
            last = end
        result.append(record[end:])
        return "".join(result)

    def retrieve_records_and_highlight(self, candidates):
        r = []
        for candidate in candidates:
            record = self.records[candidate.doc_id]
            highlights = self._merge_highlights(candidate.highlights)
            highlighted_record = self._highlight_record(record, highlights)
            r.append( (candidate.min_dist, highlighted_record) )
        return r



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

    index = Index(records)
    found = index.search("seste hodine")
    for score, f in found:
        print(score, f)
