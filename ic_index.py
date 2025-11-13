import sys
import re
from PIL import Image

import pytesseract
from fuzzysearch import find_near_matches

# img  = Image.open("test_data/pierce_shannon/a/000.png")
# text = pytesseract.image_to_string(img)
# match = find_near_matches("composed", text, max_l_dist=3)
# print(match)
# print(text)

FLAG_HELP, FLAG_HELP_S     = "--help", "-h"
FLAG_INDEX, FLAG_INDEX_S   = "--index", "-i"
FLAG_SEARCH, FLAG_SEARCH_S = "--search", "-s"

SEARCH_CMD_EXIT         = "exit()"
SEARCH_CMD_DISTANCEN = "distance(n)"
SEARCH_RGX_DISTANCE  = r"distance\(([0-9]+)\)"

MSG_MANUAL_IC_INDEX = f"""\
Usage:
  python ic_index.py                    Open graphical interface.
  python ic_index.py {FLAG_INDEX} <path>     Index a folder.
  python ic_index.py {FLAG_SEARCH} <path>    Search an indexed folder.
  python ic_index.py {FLAG_HELP}             Display usages.\
"""
MSG_MANUAL_SEARCH = f"""\
Entering search. Usage:
  {SEARCH_CMD_EXIT}         Exit search.
  {SEARCH_CMD_DISTANCEN}    Set max Levenhstein distance to n (default=1).
  <term>         Search for any <term>.\
"""

MSG_HELP            = f"Use '{FLAG_HELP}' for help."
MSG_NO_PATH         = f"No path specified. {MSG_HELP}"
MSG_UNKNOWN_COMMAND = lambda flag: f"Unknown flag '{flag}'. {MSG_HELP}"
MSG_SET_DISTANCE    = lambda n: f"Set Levenshtein distance to {n}."
MSG_NO_MATCHES      = "No matches found."
MSG_FOUND_MATCHES   = lambda n,fs,d: f"Found {n} matches in {fs} files with distance={d}:"

def start_gui():
    print("NOT IMPLEMENTED")

img  = Image.open("test_data/pierce_shannon/a/000.png")
tester = pytesseract.image_to_string(img)

def start_search_cli(path):
    TESTS = ["Hello! This is a test with many words.", MSG_MANUAL_IC_INDEX]
    print(MSG_MANUAL_SEARCH)
    l_dist = 1
    while True:
        term = input("> ")
        if term == SEARCH_CMD_EXIT:
            break
        distance = re.search(SEARCH_RGX_DISTANCE, term)
        if distance:
            l_dist = int(distance.group(1))
            print(MSG_SET_DISTANCE(l_dist))
        elif term:
            texts = {
                "Beispiel": tester,
                "zweites":  "wo simple functions to use: one for in-memory data and one for file Fastest search algorithm is chosen automatically Levenshtein Distance metric with configurable parameters Separately configure the max. allowed distance, substitutions, deletions and/or insertions Advanced algorithms with optional C and Cython optimizations"
            }
            matches = []
            for file_name,text in texts.items():
                matches += [(file_name, m) for m in find_near_matches(term, text, max_l_dist=l_dist)]
            if matches:
                print(MSG_FOUND_MATCHES(len(matches), len(texts), l_dist))
                for file_name,m in sorted(matches, key=lambda pair: pair[1].dist):
                    print(f"  d={m.dist}: '{m.matched}'\t in: '{file_name}', {m.start}-{m.end}")
            else:
                print(MSG_NO_MATCHES)

def get_path():
    if len(sys.argv) > 2:
        return sys.argv[2]
    print(MSG_NO_PATH)
    return None

def main():
    if len(sys.argv) <= 1:
        return
    flag = sys.argv[1]
    if flag in [FLAG_INDEX, FLAG_INDEX_S]:
        flag = sys.argv[1]
    elif flag in [FLAG_HELP, FLAG_HELP_S]:
        print(MSG_MANUAL)
    elif flag in [FLAG_SEARCH, FLAG_SEARCH_S]:
        path = get_path()
        if path:
            start_search_cli(path)
    else:
        print(MSG_UNKNOWN_COMMAND(flag))

if __name__ == "__main__":
    main()

