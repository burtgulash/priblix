#!/usr/bin/python3

import a
import re
import sys

class Iurl(a.I):
    def analyse(self, record):
        ws = [w for w in re.split("[_/.?+\-&:\W]+|(\d+)", record) if w]
        xs = [(word, pos) for pos, word in enumerate(ws)]
        return xs


if __name__ == "__main__":
    records = []
    for line in sys.stdin:
        records.append(line.strip())

    a = Iurl()
    a.index(records)
    if len(sys.argv) != 2:
        print("wrong sys.argv. len:", len(sys.argv))
        sys.exit(1)

    result = a.find(sys.argv[1])
    result = a.translate_docs(result, records)
    for score, doc in result:
        print(score, doc)
