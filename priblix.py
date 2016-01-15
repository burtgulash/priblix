#!/usr/bin/python3

import sys
import index

def _find_getch():
    try:
        import termios
    except ImportError:
        # Non-POSIX. Return msvcrt's (Windows') getch.
        import msvcrt
        return msvcrt.getch

    # POSIX system. Create and return a getch that manipulates the tty.
    import sys, tty
    def _getch():
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

    return _getch

getch = _find_getch()

def clear():
    sys.stderr.write("\x1b[2J\x1b[H")
    sys.stderr.flush()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("need index_file argument!")
        sys.exit(1)

    index_file = sys.argv[1]
    clear()

    records = []
    n_records = 0
    with open(index_file, "r") as f:
        for line in f:
            n_records += 1
            records.append(line.strip())

    idx = index.Index(records)
    print("indexed %s records!" % n_records)

    n = 30
    for record in records[:n]:
        print(record)

    query = ""
    print(">>")
    while True:
        c = getch()
        if c == "q":
            break
        if c == "\x08" or c == "\x7f":
            query = query[:-1]
        else:
            query += c
        clear()
        print(">>", query)

        if not query:
            for record in records[:n]:
                print(record)
        else:
            found = idx.search(query, fuzzy=True)
            for d, wd, record in found[:n]:
                print(d, wd, record)

