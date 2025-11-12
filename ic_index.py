import sys
from PIL import Image
import pytesseract

FLAG_HELP, FLAG_HELP_S     = "--help", "-h"
FLAG_INDEX, FLAG_INDEX_S   = "--index", "-i"
FLAG_SEARCH, FLAG_SEARCH_S = "--search", "-s"

MSG_MANUAL = """\
Usage:
  python ic_index.py                    Open graphical interface.
  python ic_index.py --index <path>     Index a folder.
  python ic_index.py --search <path>    Search an indexed folder.
  python ic_index.py --help             Display usages.
"""
MSG_HELP            = f"Use '{FLAG_HELP}' for help."
MSG_NO_PATH         = f"No path specified. {MSG_HELP}"
MSG_UNKNOWN_COMMAND = lambda flag: f"Unknown flag '{flag}'. {MSG_HELP}"

def start_gui():
    print("NOT IMPLEMENTED")

SEARCH_CMD_EXIT = "exit()"

def start_search_cli(path):
    TESTS = ["Hello! This is a test with many words.", MSG_MANUAL]
    print(f"Entering search. Type '{SEARCH_CMD_EXIT}' to exit.")
    while True:
        term = input("> ")
        if term == SEARCH_CMD_EXIT:
            break

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

