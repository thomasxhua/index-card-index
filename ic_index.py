import sys
import re
import os
import pickle
from PIL import Image
from pathlib import Path

import pytesseract
from fuzzysearch import find_near_matches

FLAG_HELP, FLAG_HELP_S     = "--help", "-h"
FLAG_INDEX, FLAG_INDEX_S   = "--index", "-i"
FLAG_SEARCH, FLAG_SEARCH_S = "--search", "-s"

CMD_SEARCH_EXIT      = "exit()"
CMD_SEARCH_DISTANCEN = "distance(n)"
CMD_YES              = "y"

SEARCH_RGX_DISTANCE  = r"distance\(([0-9]+)\)"

MSG_MANUAL_IC_INDEX = f"""\
Usage:
  python ic_index.py                    Open graphical interface.
  python ic_index.py {FLAG_INDEX} <path>     Index a directory <path>.
  python ic_index.py {FLAG_SEARCH} <path>    Search an indexed directory <path>.
  python ic_index.py {FLAG_HELP}             Display usages.\
"""
MSG_MANUAL_SEARCH = f"""\
Entering search. Usage:
  {CMD_SEARCH_EXIT}         Exit search.
  {CMD_SEARCH_DISTANCEN}    Set max Levenhstein distance to n (default=1).
  <term>         Search for any <term>.\
"""

MSG_HELP              = f"Use '{FLAG_HELP}' for help."
MSG_NO_PATH           = f"No path specified. {MSG_HELP}"
MSG_NO_MATCHES        = "No matches found."
MSG_SEARCH_IMPOSSIBLE = f"Cannot search unindexed files. Use '{FLAG_INDEX}' to start an indexing."

MSG_UNKNOWN_COMMAND     = lambda flag: f"Unknown flag '{flag}'. {MSG_HELP}"
MSG_SET_DISTANCE        = lambda n: f"Set Levenshtein distance to {n}."
MSG_FOUND_MATCHES       = lambda n,fs,d: f"Found {n} matches in {fs} files with distance={d}:"
MSG_PATH_DOESNT_EXIST   = lambda path: f"Couldn't find '{path}'."
MSG_INDEX_ING           = lambda path: f"Indexing '{path}' recursively."
MSG_INDEX_PROCESSING    = lambda path: f".. Processing image '{path}'."
MSG_INDEX_SKIPPING      = lambda path: f".. Skipping '{path}'."
MSG_SEARCH_NO_INDEX     = lambda path: f"Index file '{path}' not found. Run indexing now? [{CMD_YES}/n] "

def start_gui():
    print("NOT IMPLEMENTED")

def get_dictionary_path(path):
    return Path(path)/".ici.pkl"

def start_index_cli(path):
    if not os.path.exists(path):
        print(MSG_PATH_DOESNT_EXIST(path))
        return
    print(MSG_INDEX_ING(path))
    texts = {}
    for subpath in Path(path).rglob("*"):
        if not Path(subpath).suffix in Image.registered_extensions():
            if not Path(subpath).is_dir():
                print(MSG_INDEX_SKIPPING(subpath))
        else:
            print(MSG_INDEX_PROCESSING(subpath))
            img                 = Image.open(subpath)
            texts[str(subpath)] = pytesseract.image_to_string(img)
    with open(get_dictionary_path(path), "wb") as file:
        pickle.dump(texts, file)
    
def start_search_cli(path):
    texts_path = get_dictionary_path(path)
    if not os.path.exists(texts_path):
        answer = input(MSG_SEARCH_NO_INDEX(texts_path))
        if answer == CMD_YES:
            start_index_cli(path)
        else:
            print(MSG_SEARCH_IMPOSSIBLE)
            return
    with open(texts_path, "rb") as texts_file:
        texts = pickle.load(texts_file)
        print(MSG_MANUAL_SEARCH)
        l_dist = 1
        while True:
            term = input("> ")
            if term == CMD_SEARCH_EXIT:
                break
            distance = re.search(SEARCH_RGX_DISTANCE, term)
            if distance:
                l_dist = int(distance.group(1))
                print(MSG_SET_DISTANCE(l_dist))
            elif term:
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
    return None

def main():
    if len(sys.argv) <= 1:
        return
    flag = sys.argv[1]
    if flag in [FLAG_HELP, FLAG_HELP_S]:
        print(MSG_MANUAL)
    elif flag in [FLAG_INDEX, FLAG_INDEX_S]:
        path = get_path()
        if path:
            start_index_cli(path)
        else:
            print(MSG_NO_PATH)
    elif flag in [FLAG_SEARCH, FLAG_SEARCH_S]:
        path = get_path()
        if path:
            start_search_cli(path)
        else:
            print(MSG_NO_PATH)
    else:
        print(MSG_UNKNOWN_COMMAND(flag))

if __name__ == "__main__":
    main()

