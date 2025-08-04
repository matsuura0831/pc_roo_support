import sys
import os
import glob
import time
import datetime
from enum import Flag, auto
import pickle

import threading
from queue import Queue

import keyboard

import pynput
import pyautogui as ag
import pyperclip

CRNT_DIR = os.path.dirname(__file__)
SAVE_DIR = os.path.join(CRNT_DIR, "saved")

WINDOW_TITLE_CLIENT = "ラグオリ"

HOTKEY_REGISTER_WINDOW_ALL = pynput.keyboard.Key.f12
HOTKEY_REGISTER_WINDOW_TRIGGER = pynput.keyboard.Key.f11
HOTKEY_OPERATION_RECORD_AND_PLAY = pynput.keyboard.Key.f5
HOTKEY_OPERATION_RECORD = pynput.keyboard.Key.f6
HOTKEY_OPERATION_PLAY = pynput.keyboard.Key.f7
HOTKEY_OPERATION_PLAY_ALL = pynput.keyboard.Key.f8
HOTKEY_SAVE = pynput.keyboard.Key.f9
HOTKEY_LOAD = pynput.keyboard.Key.f10

class Operation(Flag):
    MOUSE = auto()
    MOVE = auto()
    SCROLL = auto()
    LEFT = auto()
    RIGHT = auto()
    MIDDLE = auto()
    KEYBOARD = auto()
    CHAR = auto()
    SPECIAL = auto()
    PRESS = auto()
    RELEASE = auto()

    MOUSE_MOVE              = MOUSE | MOVE
    MOUSE_SCROLL            = MOUSE | SCROLL
    MOUSE_LEFT_PRESS        = MOUSE | PRESS | LEFT
    MOUSE_LEFT_RELEASE      = MOUSE | RELEASE | LEFT
    MOUSE_RIGHT_PRESS       = MOUSE | PRESS | RIGHT
    MOUSE_RIGHT_RELEASE     = MOUSE | RELEASE | RIGHT
    MOUSE_MIDDLE_PRESS      = MOUSE | PRESS | MIDDLE
    MOUSE_MIDDLE_RELEASE    = MOUSE | RELEASE | MIDDLE

    KEYBOARD_CHAR_PRESS     = KEYBOARD | PRESS | CHAR
    KEYBOARD_CHAR_RELEASE   = KEYBOARD | RELEASE | CHAR
    KEYBOARD_SPECIAL_PRESS  = KEYBOARD | PRESS | SPECIAL
    KEYBOARD_SPECIAL_RELEASE= KEYBOARD | RELEASE | SPECIAL

    START_OPERATION = auto()
    STOP_OPERATION = auto()

GLOBAL_QUEUE = Queue()

def on_mouse_move(x, y):
    GLOBAL_QUEUE.put([Operation.MOUSE_MOVE, time.time(), (x, y)])
    return

def on_mouse_click(x, y, button, pressed):
    op = None
    if button == pynput.mouse.Button.left:
        op = Operation.MOUSE_LEFT_PRESS if pressed else Operation.MOUSE_LEFT_RELEASE
    elif button == pynput.mouse.Button.right:
        op = Operation.MOUSE_RIGHT_PRESS if pressed else Operation.MOUSE_RIGHT_RELEASE
    elif button == pynput.mouse.Button.middle:
        op = Operation.MOUSE_MIDDLE_PRESS if pressed else Operation.MOUSE_MIDDLE_RELEASE

    if op is not None:
        GLOBAL_QUEUE.put([op, time.time(), [x, y]])
    return

def on_mouse_scroll(x, y, dx, dy):
    GLOBAL_QUEUE.put([Operation.MOUSE_SCROLL, time.time(), [x, y, dx, dy]])
    return

def on_keyboard_press(key):
    try:
        GLOBAL_QUEUE.put([Operation.KEYBOARD_CHAR_PRESS, time.time(), [key.char]])
    except AttributeError:
        GLOBAL_QUEUE.put([Operation.KEYBOARD_SPECIAL_PRESS, time.time(), [key]])

def on_keyboard_release(key):
    try:
        GLOBAL_QUEUE.put([Operation.KEYBOARD_CHAR_RELEASE, time.time(), [key.char]])
    except AttributeError:
        GLOBAL_QUEUE.put([Operation.KEYBOARD_SPECIAL_RELEASE, time.time(), [key]])

def apply_operation(*args):
    def worker(apps, records):
        q = Queue()
        GLOBAL_QUEUE.put([Operation.START_OPERATION, None, q])

        is_interrupt = False

        for app in apps:
            ag.press("alt")
            app.activate()
            time.sleep(0.2)

            for op, elapsed, args in records:
                if not q.empty():
                    is_interrupt = q.get()

                if is_interrupt:
                    break
                elif op & Operation.MOUSE:
                    win_w, win_h = app.size
                    win_x, win_y = app.topleft

                    per_x, per_y = args[:2]
                    x = int(win_w * per_x) + win_x
                    y = int(win_h * per_y) + win_y

                    if op == Operation.MOUSE_LEFT_PRESS:
                        ag.mouseDown(x, y, duration=elapsed)
                    elif op == Operation.MOUSE_MOVE:
                        ag.moveTo(x, y, duration=elapsed)
                    elif op == Operation.MOUSE_LEFT_RELEASE:
                        ag.mouseUp(x, y, duration=elapsed)
                elif op == Operation.KEYBOARD_CHAR_RELEASE:
                    # クリップボードに追加して貼り付ける
                    pyperclip.copy(args)
                    ag.hotkey('ctrl', 'v')
                elif op == Operation.KEYBOARD_SPECIAL_RELEASE:
                    ag.hotkey(*args)
            if is_interrupt:
                break

        GLOBAL_QUEUE.put([Operation.STOP_OPERATION, None, None])
    
    th = threading.Thread(target=worker, daemon=True, args=args)
    th.start()

def help():
    print(f"HOTKEY_REGISTER_WINDOW_ALL = {HOTKEY_REGISTER_WINDOW_ALL}")
    print(f"HOTKEY_REGISTER_WINDOW_TRIGGER = {HOTKEY_REGISTER_WINDOW_TRIGGER}")
    print(f"HOTKEY_OPERATION_RECORD_AND_PLAY = {HOTKEY_OPERATION_RECORD_AND_PLAY}")
    print(f"HOTKEY_OPERATION_RECORD = {HOTKEY_OPERATION_RECORD}")
    print(f"HOTKEY_OPERATION_PLAY = {HOTKEY_OPERATION_PLAY}")
    print(f"HOTKEY_OPERATION_PLAY_ALL = {HOTKEY_OPERATION_PLAY_ALL}")
    print(f"HOTKEY_SAVE = {HOTKEY_SAVE}")
    print(f"HOTKEY_LOAD = {HOTKEY_LOAD}")
    print(f"HELP = 'h'")
    print(f"EXIT = 'q'")

def main():
    help()

    mouse_listener = pynput.mouse.Listener(
        on_move=on_mouse_move,
        on_click=on_mouse_click,
        on_scroll=on_mouse_scroll,
    )
    mouse_listener.start()

    keyboard_listener = pynput.keyboard.Listener(
        on_press=on_keyboard_press,
        on_release=on_keyboard_release,
    )
    keyboard_listener.start()

    candidates = []
    records = []
    is_threading = False
    q_stop = None

    while True:
        op, t, args = GLOBAL_QUEUE.get()

        if op == Operation.KEYBOARD_CHAR_RELEASE and args[0] == "q":
            break
        elif op == Operation.KEYBOARD_CHAR_RELEASE and args[0] == "h":
            help()
            continue

        if op == Operation.START_OPERATION:
            print(f"Start Operation ... please input {HOTKEY_OPERATION_RECORD_AND_PLAY} if you want interrupt operation sequence.")
            is_threading = True
            q_stop = args
        elif op == Operation.STOP_OPERATION:
            print("Stop Operation")
            is_threading = False
            q_stop = None
        elif is_threading and (op & Operation.KEYBOARD_SPECIAL_RELEASE) and args[0] == HOTKEY_OPERATION_RECORD_AND_PLAY:
            print("Interrupt Operation")
            if q_stop is not None:
                q_stop.put(True)

        if is_threading:
            continue
        
        if op == Operation.KEYBOARD_SPECIAL_RELEASE:
            key = args[0]
            if key == HOTKEY_REGISTER_WINDOW_ALL:
                print("Register All")
                apps = ag.getWindowsWithTitle(WINDOW_TITLE_CLIENT)
                for app in apps:
                    if app not in candidates:
                        print(f"Register: {app}")
                        candidates.append(app)

            elif key == HOTKEY_REGISTER_WINDOW_TRIGGER:
                print("Register trriger")
                app = ag.getActiveWindow()
                if app.title != WINDOW_TITLE_CLIENT:
                    print(f"Illegal client {app}")
                    continue
                if app in candidates:
                    print(f"Del: {app}")
                    candidates.remove(app)
                else:
                    print(f"Add: {app}")
                    candidates.append(app)

            elif key == HOTKEY_SAVE:
                print("Save records")
                tag = input("ファイル名を入力してください:")

                if tag != "":
                    now = datetime.datetime.now()
                    fname = f"{now.strftime("%Y%m%d-%H%M%S")}_{tag}.pkl"
                    fpath = os.path.join(SAVE_DIR, fname)

                    os.makedirs(SAVE_DIR, exist_ok=True)
                    with open(fpath,  "wb") as f:
                        pickle.dump(records, f)
                else:
                    print("Failed to save pkl")

            elif key == HOTKEY_LOAD:
                print("Load records")
                files = sorted(glob.glob(os.path.join(SAVE_DIR, "*.pkl")))
                for i, f in enumerate(files):
                    print(f"{i}. {f}")

                idx = input("番号を入力してください:")
                try:
                    idx = int(idx)
                    with open(files[idx], "rb") as f:
                        records = pickle.load(f)
                except:
                    print("Failed to load pkl")

            elif key in [HOTKEY_OPERATION_RECORD_AND_PLAY, HOTKEY_OPERATION_RECORD]:
                print(f"Record: {key}")

                if is_threading:
                    print("Already run operations")
                    continue

                app = ag.getActiveWindow()
                if app.title != WINDOW_TITLE_CLIENT:
                    print(f"Illegal client {app}")
                    continue

                GLOBAL_QUEUE.queue.clear()
                records = []

                stop_key = None
                prev_t = None
                while True:
                    op, t, args = GLOBAL_QUEUE.get()

                    if (op == Operation.KEYBOARD_SPECIAL_RELEASE) \
                            and (args[0] in [HOTKEY_OPERATION_RECORD_AND_PLAY, HOTKEY_OPERATION_RECORD]):
                        stop_key = args[0]
                        break

                    elapsed = t - prev_t if prev_t is not None else 0
                    prev_t = t

                    if op & Operation.MOUSE:
                        base_x, base_y = app.topleft
                        base_w, base_h = app.size

                        abs_x, abs_y = args[:2]
                        rel_x, rel_y = (abs_x - base_x), (abs_y - base_y)
                        per_x, per_y = (rel_x / base_w), (rel_y / base_h)

                        if (op & Operation.PRESS) or (op & Operation.RELEASE):
                            records.append([op, elapsed, (per_x, per_y)])
                        elif (op & Operation.MOVE):
                            if len(records) == 0:
                                pass # 何も入ってない場合はSKIPする
                            else:
                                if records[-1][0] == Operation.MOUSE_MOVE:
                                    # 1個前がMOUSE_MOVEだとマージする
                                    # ただしelapsedが0.1秒を超える場合は追加
                                    t = records[-1][1] + elapsed
                                    if t <= 0.1:
                                        records[-1][1] = t
                                        records[-1][2] = (per_x, per_y)
                                    else:
                                        records.append([op, elapsed, (per_x, per_y)])
                                else:
                                    records.append([op, elapsed, (per_x, per_y)])
                        elif op & Operation.SCROLL:
                            records.append([op, elapsed, (per_x, per_y, *args[2:])])
                    elif op == Operation.KEYBOARD_CHAR_RELEASE:
                        char = args[0]

                        if len(records) > 0 and records[-1][0] == Operation.KEYBOARD_CHAR_RELEASE:
                            # 文字を打っていた場合、前のに追加する
                            records[-1][2] += char
                        else:
                            records.append([op, elapsed, char])
                    elif op == Operation.KEYBOARD_SPECIAL_RELEASE:
                        key = args[0]

                        if key == pynput.keyboard.Key.esc:
                            records.append([op, elapsed, [key.name]])

                for i, (op, t, args) in enumerate(records):
                    print(f"{i}. {op}, {t:.3f}, {args}")

                if stop_key == HOTKEY_OPERATION_RECORD_AND_PLAY:
                    cand = [c for c in candidates if c != app]
                    apply_operation(cand, records)

            elif key == HOTKEY_OPERATION_PLAY:
                apply_operation([ag.getActiveWindow()], records)

            elif key == HOTKEY_OPERATION_PLAY_ALL:
                apply_operation(candidates, records)

    mouse_listener.stop()
    keyboard_listener.stop()

if __name__ == "__main__":
    main()