import sys
import os, shutil
import time
import subprocess
import json

import pyautogui as ag

DETACHED_PROCESS = 0x00000008
CREATE_NEW_PROCESS_GROUP = 0x00000200

CRNT_DIR = os.path.dirname(__file__)
SAVE_FILE = os.path.join(CRNT_DIR, "clients.json")

REL_POINT_RUNCH_BTN = (1000, 700)

TITLE_LAUNCHER = "RagoriJP"
TITLE_CLIENT = "ラグオリ"

PATH_TO_LAUNCHER = r'C:\Game\ragori_JP\RagoriJP.exe'

def load():
    if not os.path.exists(SAVE_FILE):
        print("Failed to load {SAVE_FILE}")
        return

    with open(SAVE_FILE, 'r') as f:
        data = json.load(f)
    nb_client = len(data)

    nb_crnt = len(ag.getWindowsWithTitle(TITLE_CLIENT))
    for i in range(nb_crnt, nb_client):
        # ランチャー起動
        subprocess.Popen(
            [PATH_TO_LAUNCHER],
            creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL
        )

        # 起動終了待ち
        while True:
            apps = ag.getWindowsWithTitle(TITLE_LAUNCHER)
            if len(apps) > 0:
                time.sleep(1)
                break
        app = apps[0]
        
        # 全面に持ってくる
        ag.press('alt') # おまじない:ALTを事前におすとForegroundがうまくいく
        app.activate()
        time.sleep(1)

        # 起動ボタン押下
        dx, dy = REL_POINT_RUNCH_BTN
        x, y = app.topleft
        ag.click(x + dx, y + dy)
        time.sleep(1)

    while len(ag.getWindowsWithTitle(TITLE_CLIENT)) < nb_client:
        time.sleep(1)

    apps = sorted(ag.getWindowsWithTitle(TITLE_CLIENT), key=lambda x: x._hWnd)
    for i, (x, y, w, h) in enumerate(data):
        app = apps[i]
        app.activate()
        time.sleep(0.5)
        
        # ALT+ENTERを2回押してウィンドモードにする
        ag.hotkey('alt', 'enter')
        ag.hotkey('alt', 'enter')
        time.sleep(0.5)
        
        app.moveTo(x, y)
        app.resizeTo(w, h)

def save():
    apps = ag.getWindowsWithTitle(TITLE_CLIENT)

    data = []
    for app in apps:
        x, y = app.topleft
        w, h = app.size
        data.append([x, y, w, h])

    if os.path.exists(SAVE_FILE):
        shutil.move(SAVE_FILE, f"{SAVE_FILE}.old")

    with open(SAVE_FILE, 'w') as f:
        json.dump(data, f)

if __name__ == "__main__":
    argv = sys.argv

    is_saved = False
    if len(argv) > 1:
        is_saved = argv[1] == "save"

    if is_saved:
        save()
    else:
        load()
