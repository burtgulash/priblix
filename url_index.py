#!/usr/bin/python3

import index
import re
import sys


class UrlIndex(index.Index):
    def tokenize(self, record):
        ws = [w for w in re.split("[-_/.?+&:\W]+|(\d+)", record) if w]
        return ws


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("wrong sys.argv. len:", len(sys.argv))
        sys.exit(1)

    records = []
    for line in sys.stdin:
        records.append(line.strip())

    index = UrlIndex(records)
    result = index.search(sys.argv[1])
    for score, doc in result:
        print(score, doc)
