#!/usr/bin/python3

import sys
import index
import shutil

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

    term_size = shutil.get_terminal_size((80, 20))
    clear()

    records = []
    n_records = 0
    with open(index_file, "r") as f:
        for line in f:
            n_records += 1
            records.append(line.strip())

    idx = index.Index(records)
    print("indexed %s records!" % n_records)

    n = term_size.lines + 1
    for remaining_line in range(n - n_records):
        print()
    for record in records[:n]:
        print(record)
    print(">>")

    query = ""
    while True:
        c = getch()
        if c == "q":
            break
        if c == "\x08" or c == "\x7f":
            query = query[:-1]
        else:
            query += c

        clear()
        if not query:
            for remaining_line in range(n - n_records):
                print()
            for record in records[:n]:
                print(record)
        else:
            found = list(idx.search(query, topn=n-1, fuzzy=True))
            for remaining_line in range(n - len(found)):
                print()
            for d, wd, record in found[:n][::-1]:
                print(d, wd, record)

        print(">>", query)

