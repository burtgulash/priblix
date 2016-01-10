#!/usr/bin/python3

import a
import re
import sys


class UrlIndex(a.Index):
    def tokenize(self, record):
        ws = [w for w in re.split("[-_/.?+&:\W]+|(\d+)", record) if w]
        return ws


if __name__ == "__main__":
    records = []
    for line in sys.stdin:
        records.append(line.strip())

    index = UrlIndex(records)

    if len(sys.argv) != 2:
        print("wrong sys.argv. len:", len(sys.argv))
        sys.exit(1)

    result = index.search(sys.argv[1])
    for score, doc in result:
        print(score, doc)
