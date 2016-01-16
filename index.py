#!/usr/bin/python3

import collections
import re
from trees.bktree import BKTree, levenshtein, hamming
from trees.trie import Trie


class Candidate:
    __slots__ = "doc_id", "edit_distance", "last_occurrences", "min_dist", "highlights"

    def __init__(self, doc_id, edit_distance, word_occurrences, highlights):
        self.doc_id = doc_id
        self.edit_distance = edit_distance
        self.last_occurrences = word_occurrences
        self.min_dist = 0
        self.highlights = highlights

    def __repr__(self):
        return "Cand({}, {})".format(self.doc_id, self.edit_distance)

class RecordPosition:
    __slots__ = "char_position", "word_position"

    def __init__(self, char_position, word_position):
        self.char_position = char_position
        self.word_position = word_position

def min_dist(xpositions, ypositions):
    d = 1337
    ix = iy = 0
    penalty = 1
    while ix < len(xpositions) and iy < len(ypositions):
        x = xpositions[ix].word_position
        y = ypositions[iy].word_position
        if x < y:
            diff = y - x - 1
            ix += 1
        else:
            diff = x - y - 1 + penalty
            iy += 1

        if diff <= 0:
            return 0
        if diff < d:
            d = diff

    return d



class Index:

    def __init__(self, records):
        self.records = records
        self.index = {}
        self.edits_lev = BKTree(levenshtein)
        self.edits_3 = BKTree(hamming)
        self.word_trie = Trie()

        self.word_set = set()

        self._index(records)

    def tokenize(self, record):
        #return re.split("\W+", record)
        return [w for w in re.split("[-_/.?+&:\W]+|(\d+)", record) if w]

    def filter(self, token):
        return token.lower()

    def add_token_offsets(self, record, tokens):
        terms = []
        char_i = 0
        for tok_i, token in enumerate(tokens):
            assert char_i < len(record)
            while not record[char_i:].startswith(token):
                char_i += 1
            token = self.filter(token)
            terms.append( (token, RecordPosition(char_i, tok_i)) )
            char_i += len(token)
        return terms

    def search(self, query, topn=10, fuzzy=False):
        if fuzzy:
            candidates = self._find_phrase_fuzzy(query)
        else:
            candidates = self._find_phrase(query)

        candidates.sort(key=lambda c: (c.edit_distance, c.min_dist))
        candidates = candidates[:topn]

        for c in candidates:
            record = self.records[c.doc_id]
            highlights = self._merge_highlights(c.highlights)
            highlighted_record = self._highlight_record(record, highlights)
            yield (c.edit_distance, c.min_dist, highlighted_record)


    def _group_occurrences(self, occurrences):
        d = collections.defaultdict(list)
        for word, record_position in occurrences:
            d[word].append(record_position)
        return d

    def _index(self, records):
        for doc_id, record in enumerate(records):
            tokens = self.tokenize(record)
            occurrences = self.add_token_offsets(record, tokens)
            for token, record_positions in self._group_occurrences(occurrences).items():
                for i in range(1, len(token)):
                    prefix = token[:i + 1]
                    if not self.word_trie.is_prefix(prefix):
                        self.edits_lev.insert(prefix)
                        if len(prefix) == 3:
                            self.edits_3.insert(prefix)

                if token not in self.index:
                    self.word_trie.insert(token)
                    self.index[token] = []
                self.index[token].append((doc_id, record_positions))

    def _find_derived_words(self, word, is_prefix):
        use_levenshtein = True
        if is_prefix:
            if len(word) <= 2:
                return ((0, w) for w in self.word_trie.descendants_or_self(word))
            if len(word) == 3:
                derived_words = self.edits_3.find(word, 1)
                use_levenshtein = False

        if use_levenshtein:
            if len(word) <= 4:
                d = 1
            elif len(word) <= 7:
                d = 2
            else:
                d = 3

            derived_words = self.edits_lev.find(word, d)

        if is_prefix:
            min_dists = {}
            for d, w in derived_words:
                descs = self.word_trie.descendants_or_self(w)
                for desc in descs:
                    if desc not in min_dists:
                        min_dists[desc] = d
                    else:
                        min_dists[desc] = min(min_dists[desc], d)
            derived_words = ((d, desc) for desc, d in min_dists.items())

        return derived_words

    def _find_one(self, word, prefix, edit_distance):
        docs_found = self.index.get(word, [])
        result = []
        for doc_id, record_positions in docs_found:
            highlights = [
                (rp.char_position, rp.char_position + len(prefix))
                for rp in record_positions
            ]
            cnd = Candidate(doc_id, edit_distance, record_positions, highlights)
            result.append(cnd)

        return result

    def _find_one_fuzzy(self, word, is_prefix=False):
        derived_words = self._find_derived_words(word, is_prefix)

        result = []
        for d, w in derived_words:
            candidates = self._find_one(w, word, d)
            result.extend(candidates)

        d = collections.defaultdict(list)
        for cnd in result:
            d[cnd.doc_id].append(cnd)

        # group candidates by doc_id
        result = []
        for doc_id, cnds in d.items():
            edit_distance = min(c.edit_distance for c in cnds)
            last_occurrences = sum([c.last_occurrences for c in cnds], []) # TODO remove duplicate occurrences? are there any?
            highlights = sum([c.highlights for c in cnds], [])
            c = Candidate(doc_id, edit_distance, last_occurrences, highlights)
            result.append(c)

        result.sort(key=lambda cnd: cnd.doc_id)

        return result

    def _find_phrase(self, query):
        tokens = self.tokenize(query)
        if not tokens:
            return []

        candidates = self._find_one(tokens[0], tokens[0], 0)
        for token in tokens[1:]:
            new_candidates = self._find_one(token, token, 0)
            candidates = self._merge(candidates, new_candidates)

        return candidates

    def _find_phrase_fuzzy(self, query):
        tokens = self.tokenize(query)
        if not tokens:
            return []


        is_last_prefix = query[-1] != " "
        candidates = self._find_one_fuzzy(tokens[0], is_prefix=is_last_prefix and len(tokens) == 1)
        for i, token in enumerate(tokens[1:]):
            new_candidates = self._find_one_fuzzy(token, is_prefix=is_last_prefix and i == len(tokens) - 2)
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
                edit_distance = cndx.edit_distance + cndy.edit_distance

                c = Candidate(cndx.doc_id, edit_distance, ypositions, cndx.highlights + cndy.highlights)
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
                if hlend > hlstart:
                    result.append( (hlstart, hlend) )
                hlstart, hlend = start, end

        # also include the last one
        result.append( (hlstart, hlend) )

        return result

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

    def _highlight_candidates(self, candidates):
        r = []
        for candidate in candidates:
            #record = self.records[candidate.doc_id]
            highlights = self._merge_highlights(candidate.highlights)
            highlighted_record = self._highlight_record(record, highlights)
            r.append( (candidate.edit_distance, candidate.min_dist, highlighted_record) )
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
        "po mesici tezce vysralo sestou",
        "na sestou se podivame na auto, to bude podivana",
        "ono je to taky ono auto",
        "neslo se mi tezce ze se mi sralo na mesici v seste",
        "to je mesici se pozde jede a jelo taky",
        "vysrat se na to",
        "jelo se mi v seste auto opravit na mesici po nem",
        "kravate se vysralo taky auto",
        "tezce se mi sere po silnici",
        "ono na mesici je auto seste",
        "podivana na mesici je mimo provoz srani",
        "taky jsem tezce vstaval kdyz mi sralo auto",
        "vstavat tezce po ranu a auto u toho",
        "sestou ranu u hospody na kravate po mesici me nasralo",
        "jede na mesici auto",
        "na to bych musel mit taky auto",
        "musel bych tezce nest hodiny mimo seste",
        "hodiny a auto me nasralo kdyz jsem sel po mesici na podivanou",
        "po silnici se spatne sere i jede autem",
        "ono se i podivame v auto mechanikove silnici",
        "taky bych musel vstavat a to by se mi neslo po silnici taky tak lehce",
        "na kravate jsem nasel flek a to me nasralo tak moc, ze z toho byla podivana, ale pozde",
        "jsem byl srat",
        "a ty taky",
        "taky mi to neslo se vysrat, vsichni ze me meli podivanou",
        "auto autem neni sralo srackou",
        "tezce bys sral a ja bych auto tezce nesl k silnici",
        "pak se mi taky vysralo silnici i auto",
    ]

    index = Index(records)
    found = index.search("taky i vysralis si", fuzzy=True)
    for edits, wd, f in found:
        print(edits, wd, f)
