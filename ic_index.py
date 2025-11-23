import sys
import re
import os
import pickle
from pathlib import Path
import shlex
import hashlib

from PIL import Image
import subprocess
from fuzzysearch import find_near_matches
from nicegui import ui

FLAG_HELP, FLAG_HELP_S     = "--help", "-h"
FLAG_INDEX, FLAG_INDEX_S   = "--index", "-i"
FLAG_INDEX_AND_SEARCH, FLAG_INDEX_AND_SEARCH_S = "--index-and-search", "-x"
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
MSG_SEARCH_IMPOSSIBLE = f"Cannot search unindexed files. Use '{FLAG_INDEX}' to start an indexing."

MSG_UNKNOWN_COMMAND     = lambda flag: f"Unknown flag '{flag}'. {MSG_HELP}"
MSG_SET_DISTANCE        = lambda n: f"Set Levenshtein distance to {n}."
MSG_FOUND_MATCHES       = lambda n,fs,d: f"Found {n} matches in {fs} files with distance={d}:"
MSG_PATH_DOESNT_EXIST   = lambda path: f"'{path}' is not a directory."
MSG_INDEX_ING           = lambda path: f"Indexing '{path}' recursively."
MSG_INDEX_PROCESSING    = lambda path: f".. Processing image '{path}'."
MSG_INDEX_SKIPPING      = lambda path: f".. Skipping '{path}' (not an recognized image)."
MSG_INDEX_ALREADY       = lambda path: f".. Skipping '{path}' (already indexed)."
MSG_INDEX_EXISTING      = lambda path: f"Found existing index file '{path}'."
MSG_SEARCH_NO_INDEX     = lambda path: f"Index file '{path}' not found. Run indexing now? [{CMD_YES}/n] "

def fancy_print(printer, text):
    printer(text)

def get_dictionary_path(path):
    return Path(path) / ".ici.pkl"

# source: https://docs.vultr.com/python/examples/find-hash-of-file
def get_sha256_hash(file_path):
    hash_sha256 = hashlib.sha256() 
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()
    
def ocr_image(path):
    #img    = Image.open(subpath)
    #text   = pytesseract.image_to_string(img)
    #return text
    result = subprocess.run(["tesseract", path, "stdout"], capture_output=True, text=True)
    print(result.stdout)
    return str(result.stdout)

def index_texts(path, printer=print, status_printer=None):
    if not os.path.exists(path) or not Path(path).is_dir():
        printer(MSG_PATH_DOESNT_EXIST(path))
        return
    texts_path   = get_dictionary_path(path)
    texts_hashed = None
    if os.path.exists(texts_path):
        printer(MSG_INDEX_EXISTING(texts_path))
        # TODO: doesnt pick up on nested .ici files
        with open(texts_path, "rb") as texts_file:
            texts_hashed = pickle.load(texts_file)
    texts_hashed_new = {}
    texts            = {}
    subpaths     = sorted(Path(path).rglob("*"))
    len_subpaths = len(subpaths)
    for i in range(0,len_subpaths):
        if status_printer:
            status_printer(f"{i}/{len_subpaths-1}")
        subpath = subpaths[i].resolve()
        if not Path(subpath).suffix in Image.registered_extensions():
            if not Path(subpath).is_dir():
                printer(MSG_INDEX_SKIPPING(subpath))
        else:
            str_subpath = str(subpath)
            if texts_hashed:
                sha256 = get_sha256_hash(str_subpath)
                if str_subpath in texts_hashed:
                    _,h = texts_hashed[str_subpath]
                    if h == sha256:
                        printer(MSG_INDEX_ALREADY(str_subpath))
                        texts_hashed_new[str_subpath] = texts_hashed[str_subpath]
                        continue
            printer(MSG_INDEX_PROCESSING(str_subpath))
            text   = ocr_image(subpath)
            sha256 = get_sha256_hash(subpath)
            texts_hashed_new[str_subpath] = (text,sha256)
            texts[str_subpath]            = text
    with open(texts_path, "wb") as file:
        pickle.dump(texts_hashed_new, file)
    return {k:t for k,(t,h) in texts_hashed_new.items()}
    
def start_index_cli(path):
    print(MSG_INDEX_ING(path))
    index_texts(path)

def search_texts(texts, terms, l_dist=1):
    if not terms:
        return {}
    terms = shlex.split(terms)
    matches = {}
    for i in range(0, len(terms)):
        term = terms[i]
        for text_name,text in texts.items():
            current_matches = find_near_matches(term, text, max_l_dist=l_dist)
            for match in current_matches:
                # ignore adding file for in non-first matches
                if i == 0 and text_name not in matches:
                    matches[text_name] = { term: [] }
                if text_name in matches:
                    if term not in matches[text_name]:
                        matches[text_name][term] = []
                    matches[text_name][term].append(match.matched)
        # clean up files after further searches
        matches = {k:v for k,v in matches.items() if term in v}
    return matches

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
        texts_hashed = pickle.load(texts_file)
        texts        = {k:ts for k,(ts,h) in texts_hashed}
        print(MSG_MANUAL_SEARCH)
        l_dist = 1
        while True:
            terms = input("> ")
            if terms == CMD_SEARCH_EXIT:
                break
            distance = re.search(SEARCH_RGX_DISTANCE, terms)
            if distance:
                l_dist = int(distance.group(1))
                print(MSG_SET_DISTANCE(l_dist))
            elif terms:
                matches = search_texts(texts, terms, l_dist)
                for text_name,ms in matches.items():
                    print(f"{text_name}: {ms}")

GUI_TITLE  = "Index Card Index"
GUI_INPUT_PATH   = "Enter path..."
GUI_INPUT_SEARCH = "Search..."
GUI_BUTTON_INDEX = "Index"
GUI_LABEL_INDEX  = "Index status: "

GUI_LOG_LINE_LIMIT = 100

def gui(index_folder=None):
    dark  = ui.dark_mode()
    texts = None
    def gui_printer(s):
        lines = gui_log.value.splitlines()
        lines.insert(0, s)
        if len(lines) > GUI_LOG_LINE_LIMIT:
            lines = lines[:GUI_LOG_LINE_LIMIT]
        gui_log.value = "\n".join(lines)
    def index_path():
        nonlocal texts
        texts = index_texts(input_path.value, gui_printer, ui_status.set_text)
    def search_terms():
        nonlocal results
        nonlocal preview
        for child in results.descendants():
            child.delete()
        matches = search_texts(texts, input_search.value)
        def change_image(src):
            preview.set_source(src)
        for k,v in matches.items():
            with results:
                ui.item(f"{k}", on_click=lambda k=k: change_image(k))
    # top bar
    with ui.row().classes("w-full items-center"):
        # title
        ui.label(GUI_TITLE).classes("text-xl")
        ui.space()
        # dark mode switch
        switch = ui.switch("Night",
                           on_change=lambda e: dark.enable() if e.value else dark.disable())
        switch.set_value(True)
    # path select
    with ui.row().classes("w-full items-center gap-4"):
        input_path = ui.input(placeholder=GUI_INPUT_PATH).on("keydown.enter", index_path).style("flex: 1;")
        if index_folder:
            input_path.value = index_folder
        ui.button(GUI_BUTTON_INDEX, on_click=index_path)
    # program
    with ui.row().classes("w-full h-full no-wrap"):
        with ui.column().classes("w-1/2 gap-2 items-start"):
            with ui.row().classes("w-full items-center gap-4"):
                ui.label(GUI_LABEL_INDEX)
                ui_status = ui.label()
            #gui_printer = ui.label("Currently").classes("italic")
            gui_log = ui.textarea().props("readonly").classes("w-full italic")
            with ui.row().classes("w-full items-center gap-4"):
                input_search = ui.input(placeholder=GUI_INPUT_SEARCH).on("keydown.enter", search_terms).style("flex: 1;")
                ui.button(icon="search", on_click=search_terms)
            with ui.scroll_area():
                results = ui.list().props('dense separator')
        with ui.column().classes("w-1/2 items-start"):
            ui.label("Image Preview:")
            preview = ui.image()
    ui.run()

def get_path():
    if len(sys.argv) > 2:
        return sys.argv[2]
    return None

def main():
    if len(sys.argv) <= 1:
        gui()
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
    elif flag in [FLAG_INDEX_AND_SEARCH, FLAG_INDEX_AND_SEARCH_S]:
        path = get_path()
        if path:
            index_texts(path)
            gui(path)
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

if __name__ in ["__main__", "__mp_main__"]:
    main()


