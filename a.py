#!/usr/bin/python3

class I:
    def __init__(self):
        self._index = {}

    def analyse(self, record):
        words = record.split(" ")
        return [(word, pos) for pos, word in enumerate(words)]

    def index(self, records):
        for doc_id, record in enumerate(records):
            words = self.analyse(record)
            for word, pos in words:
                if word not in self._index:
                    self._index[word] = []
                self._index[word].append((doc_id, pos))

    def find_one(self, word):
        docs = self._index.get(word, [])
        return [doc_id for doc_id, pos in docs]

    def find(self, query):
        words = self.analyse(query)
        if not words:
            return []

        word, pos = words[0]
        docs = self.find_one(word)
        for word, pos in words[1:]:
            new_docs = self.find_one(word)
            docs = self.merge(docs, new_docs)

        return docs

    def merge(self, xs, ys):
        ds = []
        ix = iy = 0
        while ix < len(xs) and iy < len(ys):
            doc_x = xs[ix]
            doc_y = ys[iy]
            if doc_x < doc_y:
                ix += 1
            elif doc_x > doc_y:
                iy += 1
            else:
                ds.append(doc_x)
                ix, iy = ix + 1, iy + 1
        return ds

    def translate_docs(self, result, records):
        return [
            records[doc_id]
            for doc_id
            in result
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
        "sestou hodinu se vysralo tezce",
    ]

    x = I()
    x.index(records)
    y = x.find("po auto kravate")
    print("found:", x.translate_docs(y, records))
