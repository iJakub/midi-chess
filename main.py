#iJ
#refactored using GPT-4

import pygame as p
import pygame.midi
import sys
from multiprocessing import Process, Queue
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import time
import os
import platform

#Local Imports
import ENGINE
import AI


#Chess GUI Configuration
BOARD_WIDTH=BOARD_HEIGHT = 512
MOVE_LOG_PANEL_WIDTH = 245
MOVE_LOG_PANEL_HEIGHT = BOARD_HEIGHT
DIMENSION = 8
SQUARE_SIZE = BOARD_HEIGHT // DIMENSION
MAX_FPS = 15
IMAGES = {}


#Load Piece Images
def loadImages():
    pieces = ["wp", "wR", "wN", "wB", "wK", "wQ", "bp", "bR", "bN", "bB", "bK", "bQ"]
    
    for piece in pieces:
        IMAGES[piece] = p.transform.scale(p.image.load("img/" + piece + ".png"), (SQUARE_SIZE, SQUARE_SIZE))


#MIDI Device Handling
def get_midi_input_devices():
    pygame.midi.init()
    device_count = pygame.midi.get_count()

    devices = []
    for i in range(device_count):
        try:
            info = pygame.midi.get_device_info(i)
            if info:
                interf, name, input_dev, output_dev, opened=info
                name = name.decode("utf-8") if isinstance(name, bytes) else name
                if input_dev and not opened:
                    devices.append((i, name))
                    
        except Exception as e:
            print(f"Error while checking MIDI device #{i}: {e}")
            continue
    return devices


#Open Selected MIDI Device
def open_selected_midi_input():
    selected_name = midi_var.get()
    if not selected_name:
        return None
        
    inputs=get_midi_input_devices()
    for device_id, name in inputs:
        if name == selected_name:
            try:
                midi_in = pygame.midi.Input(device_id)
                print(f"Opened MIDI input: {name}")
                return midi_in
            except Exception as e:
                print(f"Failed to open {name}: {e}")
                continue
    return None


#Pawn Promotion Window
def ask_promotion_choice(root, color, embed, toplevel_data):
    toplevel_data["ignore_updates_promotion"] = True
    
    from PIL import Image, ImageTk
    
    toplevel_data["black_buttons"][1].config(text="♕", font=("Helvetica", 25))
    toplevel_data["black_buttons"][2].config(text="♖", font=("Helvetica", 25))
    toplevel_data["black_buttons"][3].config(text="♗", font=("Helvetica", 25))
    toplevel_data["black_buttons"][4].config(text="♘", font=("Helvetica", 25))
    
    toplevel_data["in_progress"] = True
    promotion_window = tk.Toplevel(root)
    promotion_window.title("Promote pawn to")
    promotion_window.resizable(False, False)
    promotion_window.configure(bg="white")

    win_width = 360
    win_height = 120

    root.update_idletasks()
    root_x = root.winfo_rootx()
    root_y = root.winfo_rooty()
    root_width = root.winfo_width()
    root_height = root.winfo_height()

    offset_y = -40
    x = root_x + (root_width - win_width) // 2
    y = root_y + (root_height - win_height) // 2 + offset_y
    promotion_window.geometry(f"{win_width}x{win_height}+{x}+{y}")
    promotion_window.grab_set()
    
    choice_var = tk.StringVar()
    
    def choose(piece_code):
        choice_var.set(piece_code)
        promotion_window.destroy()

    button_frame = tk.Frame(promotion_window, bg="white")
    button_frame.pack(expand=True, pady=10)

    pieces = [("Q", "Queen"), ("R", "Rook"), ("B", "Bishop"), ("N", "Knight")]
    image_refs = []
    buttons = []

    for code, name in pieces:
        path = f"img/{color}{code}.png"
        
        if not os.path.exists(path):
            print(f"Missing file: {path}")
            continue

        img = Image.open(path).convert("RGBA").resize((64, 64), Image.Resampling.LANCZOS)
        bg = Image.new("RGBA", img.size, "WHITE")
        img = Image.alpha_composite(bg, img).convert("RGB")
        photo = ImageTk.PhotoImage(img)
        image_refs.append(photo)

        btn = tk.Button(button_frame, image=photo, command=lambda c=code: choose(c), bd=1, relief="solid", bg="white", activebackground="#d0e6ff")
        btn.pack(side="left", padx=5)
        buttons.append(btn)
    
    toplevel_data["black_buttons"][1].config(text="♕", font=("Helvetica", 25))
    toplevel_data["black_buttons"][2].config(text="♖", font=("Helvetica", 25))
    toplevel_data["black_buttons"][3].config(text="♗", font=("Helvetica", 25))
    toplevel_data["black_buttons"][4].config(text="♘", font=("Helvetica", 25))

    toplevel_data["buttons"] = buttons
    promotion_window.wait_window()
    
    toplevel_data["buttons"] = None
    toplevel_data["in_progress"] = False
    toplevel_data["ignore_updates_promotion"] = False
    return choice_var.get()


#Custom Yes/No Dialog
def custom_askyesno(root, title, message, toplevel_data, undo_btn, reset_btn, backspace_btn, octave_widget, callback):
    toplevel_data["ignore_updates_askyesno"] = True
    toplevel_data["disable_white_buttons"]()
    toplevel_data["black_buttons"][3].config(bg="green")
    toplevel_data["black_buttons"][4].config(bg="red")
    
    undo_btn.config(state="disabled")
    reset_btn.config(state="disabled")
    backspace_btn.config(state="disabled")
    octave_widget.config(state="disabled")

    toplevel_data["in_progress"] = True

    dialog=tk.Toplevel(root)
    dialog.title(title)
    
    root.update_idletasks()
    root_x = root.winfo_rootx()
    root_y = root.winfo_rooty()
    root_width = root.winfo_width()
    root_height = root.winfo_height()

    win_width = 300
    win_height = 120
    x=root_x + (root_width - win_width) // 2
    y=root_y + (root_height - win_height) // 2

    dialog.geometry(f"{win_width}x{win_height}+{x}+{y}")
    dialog.resizable(False, False)
    dialog.configure(bg="white")
    dialog.grab_set()
    dialog.transient(root)

    label = tk.Label(dialog, text=message, font=("Helvetica", 12), bg="white")
    label.pack(pady=10)

    def finish(result):
        dialog.destroy()
        undo_btn.config(state="normal")
        reset_btn.config(state="normal")
        backspace_btn.config(state="normal")
        octave_widget.config(state="readonly")
        toplevel_data["in_progress"]=False
        toplevel_data["ignore_updates_askyesno"]=False
        callback(result)

    def yes():
        finish(True)

    def no():
        finish(False)

    toplevel_data["yes_fn"] = yes
    toplevel_data["no_fn"] = no

    tk.Button(dialog, text="Yes", width=10, command=yes).pack(side="left", padx=20, pady=10)
    tk.Button(dialog, text="No", width=10, command=no).pack(side="right", padx=20, pady=10)

    dialog.wait_window()
    undo_btn.config(state="normal")
    reset_btn.config(state="normal")
    backspace_btn.config(state="normal")
    octave_widget.config(state="readonly")
    toplevel_data["black_buttons"][3].config(bg="green")
    toplevel_data["black_buttons"][4].config(bg="red")
    toplevel_data["in_progress"] = False
    toplevel_data["enable_white_buttons"]()


midi_var = None
midi_dropdown = None

#Main Function (Setup GUI and Game Logic)
def main():
    global midi_var, midi_dropdown
    import threading

    toplevel_data = {
        "in_progress": False,
        "buttons": None
        }
        
    state_flags = {
        "reset": False,
        "undo": False,
        "player_two": False
        }
    
    
    root = tk.Tk()
    root.title("Chess MIDI")
    root.geometry("1280x621")
    root.resizable(False, False)


    main_frame = tk.Frame(root, bg="white")
    main_frame.place(relwidth=1, relheight=1)


    embed_y = 20
    embed=tk.Frame(main_frame, width=BOARD_WIDTH + MOVE_LOG_PANEL_WIDTH, height=BOARD_HEIGHT, bg="white")
    embed.place(x=514+5, y=embed_y)
    
    
    os.environ["SDL_WINDOWID"] = str(embed.winfo_id())
    os.environ["SDL_VIDEODRIVER"] = "windib" if platform.system() == "Windows" else "x11"
    
    
    p.init()
    
    
    screen = p.display.set_mode((BOARD_WIDTH + MOVE_LOG_PANEL_WIDTH, BOARD_HEIGHT))
    clock = p.time.Clock()
    screen.fill(p.Color("white"))

    
    #Create Chess Board Columns & Rows Labels
    label8 = tk.Label(main_frame, text="8", bg="white", font=("Arial", 20))
    label8.place(x=440+5, y=20, width=64, height=64)
    label7 = tk.Label(main_frame, text="7", bg="white", font=("Arial", 20))
    label7.place(x=440+5, y=84, width=64, height=64)
    label6 = tk.Label(main_frame, text="6", bg="white", font=("Arial", 20))
    label6.place(x=440+5, y=148, width=64, height=64)
    label5 = tk.Label(main_frame, text="5", bg="white", font=("Arial", 20))
    label5.place(x=440+5, y=212, width=64, height=64)
    label4 = tk.Label(main_frame, text="4", bg="white", font=("Arial", 20))
    label4.place(x=440+5, y=276, width=64, height=64)
    label3 = tk.Label(main_frame, text="3", bg="white", font=("Arial", 20))
    label3.place(x=440+5, y=340, width=64, height=64)
    label2 = tk.Label(main_frame, text="2", bg="white", font=("Arial", 20))
    label2.place(x=440+5, y=404, width=64, height=64)
    label1 = tk.Label(main_frame, text="1", bg="white", font=("Arial", 20))
    label1.place(x=440+5, y=468, width=64, height=64)
    labela = tk.Label(main_frame, text="A", bg="white", font=("Arial", 20))
    labela.place(x=514, y=542, width=64, height=64)
    labelb = tk.Label(main_frame, text="B", bg="white", font=("Arial", 20))
    labelb.place(x=514+64, y=542, width=64, height=64)
    labelc = tk.Label(main_frame, text="C", bg="white", font=("Arial", 20))
    labelc.place(x=514+5+64*2, y=542, width=64, height=64)
    labeld = tk.Label(main_frame, text="D", bg="white", font=("Arial", 20))
    labeld.place(x=514+5+64*3, y=542, width=64, height=64)
    labele = tk.Label(main_frame, text="E", bg="white", font=("Arial", 20))
    labele.place(x=514+5+64*4, y=542, width=64, height=64)
    labelf = tk.Label(main_frame, text="F", bg="white", font=("Arial", 20))
    labelf.place(x=514+5+64*5, y=542, width=64, height=64)
    labelg = tk.Label(main_frame, text="G", bg="white", font=("Arial", 20))
    labelg.place(x=514+5+64*6, y=542, width=64, height=64)
    labelh = tk.Label(main_frame, text="H", bg="white", font=("Arial", 20))
    labelh.place(x=514+5+64*7, y=542, width=64, height=64)


    label_dict = {
        "8": label8,
        "7": label7,
        "6": label6,
        "5": label5,
        "4": label4,
        "3": label3,
        "2": label2,
        "1": label1,
        "A": labela,
        "B": labelb,
        "C": labelc,
        "D": labeld,
        "E": labele,
        "F": labelf,
        "G": labelg,
        "H": labelh
    }

    column_row_dict = {
        "A": "1",
        "B": "2",
        "C": "3",
        "D": "4",
        "E": "5",
        "F": "6",
        "G": "7",
        "H": "8"
    }


    #Reset Board Label Colors
    def reset_label_colors():
        for label in label_dict.values():
            label.config(bg="white", fg="black", font=("Arial", 20))


    #Piano GUI Setup
    piano_panel=tk.Frame(main_frame, width=435, height=600, bg="white")
    piano_panel.place(x=0, y=0)


    white_key_width = 50
    white_key_height = 200
    black_key_width = 30
    black_key_height = 120


    total_white_width = white_key_width * 8
    piano_start_x = 29+5
    piano_start_y = 56-9


    def play_C():
        handle_white_keys("A")
        print("C")
    def play_D():
        handle_white_keys("B")
        print("D")
    def play_E():
        handle_white_keys("C")
        print("E")
    def play_F():
        handle_white_keys("D")
        print("F")
    def play_G():
        handle_white_keys("E")
        print("G")
    def play_A():
        handle_white_keys("F")
        print("A")
    def play_B():
        handle_white_keys("G")
        print("B")
    def play_C2():
        handle_white_keys("H")
        print("C2")


    def play_Cs():
        print("C#")
        current_depth = slider.get()
        new_depth = current_depth % 3 + 1
        slider.set(new_depth)
        on_slider_change(new_depth)
        
    def play_Ds():
        if toplevel_data["in_progress"] and toplevel_data.get("buttons"):
            toplevel_data["buttons"][0].invoke()
        else:
            print("D#")
            current_index = player_mode_dropdown.current()
            new_index = 1 if current_index == 0 else 0
            player_mode_dropdown.current(new_index)
            
    def play_Fs():
        if toplevel_data["in_progress"] and toplevel_data.get("buttons"):
            toplevel_data["buttons"][1].invoke()
        else:
            print("F#")
            backspace_button.invoke()
            
    def play_Gs():
        if toplevel_data["in_progress"] and toplevel_data.get("buttons"):
            toplevel_data["buttons"][2].invoke()
        else:
            if toplevel_data.get("in_progress") and toplevel_data.get("yes_fn"):
                toplevel_data["yes_fn"]()
            else:
                print("G#")
                reset_button.invoke()
                
    def play_As():
        if toplevel_data["in_progress"] and toplevel_data.get("buttons"):
            toplevel_data["buttons"][3].invoke()
        else:
            if toplevel_data.get("in_progress") and toplevel_data.get("no_fn"):
                toplevel_data["no_fn"]()
            else:
                print("A#")
                undo_button.invoke()


    #Piano GUI White Keys
    white_buttons = []
    white_key_funcs = [play_C, play_D, play_E, play_F, play_G, play_A, play_B, play_C2]

    for i, func in enumerate(white_key_funcs):
        x = piano_start_x + i * white_key_width
        btn = tk.Button(piano_panel, bg="white", bd=1, relief="solid", activebackground="lightblue", font=("Helvetica", 10), text=func.__name__[5:], command=func)
        btn.place(x=x, y=piano_start_y, width=white_key_width, height=white_key_height)
        white_buttons.append(btn)


    #Piano GUI Black Keys
    black_keys_info = [
        (0, play_Cs),
        (1, play_Ds),
        (3, play_Fs),
        (4, play_Gs),
        (5, play_As)]
    
    
    black_buttons = []
    
    
    for pos, func in black_keys_info:
        x = piano_start_x + (pos + 1) * white_key_width - black_key_width // 2
        btn = tk.Button(piano_panel, bg="black", fg="white", relief="solid", bd=1, activebackground="lightblue", text=func.__name__[5:].replace("s", "#"), command=func)
        btn.place(x=x, y=piano_start_y, width=black_key_width, height=black_key_height)
        black_buttons.append(btn)
    
    
    #Control Panel GUI Setup
    entry_from_var = tk.StringVar()
    entry_to_var = tk.StringVar()
    
    
    label_arrow = tk.Label(main_frame, text="⮕", bg="white", font=("Helvetica", 40)).place(x=125-3, y=330-32)
    entry_from = tk.Entry(main_frame, textvariable=entry_from_var, bg="white", font=("Helvetica", 20), relief="solid", state="readonly", justify="center")
    entry_from.place(x=45-3, y=331-32, width=64, height=64)
    entry_to = tk.Entry(main_frame, textvariable=entry_to_var, bg="white", font=("Helvetica", 20), relief="solid", state="readonly", justify="center")
    entry_to.place(x=195-3, y=331-32, width=64, height=64)

    
    #Limit Entry Length (2 chars)
    def limit_entry_length(new_value):
        return len(new_value) <= 2


    vcmd = root.register(limit_entry_length)
    entry_from.config(validate="key", validatecommand=(vcmd, "%P"))
    entry_to.config(validate="key", validatecommand=(vcmd, "%P"))

    
    #Map MIDI Notes to Keys
    def build_note_to_key(octave):
        base=12 * (octave+1)
        return {
            base + 0:  (white_buttons[0], "C"),
            base + 2:  (white_buttons[1], "D"),
            base + 4:  (white_buttons[2], "E"),
            base + 5:  (white_buttons[3], "F"),
            base + 7:  (white_buttons[4], "G"),
            base + 9:  (white_buttons[5], "A"),
            base + 11: (white_buttons[6], "B"),
            base + 12: (white_buttons[7], "C2"),

            base + 1:  (black_buttons[0], "C#"),
            base + 3:  (black_buttons[1], "D#"),
            base + 6:  (black_buttons[2], "F#"),
            base + 8:  (black_buttons[3], "G#"),
            base + 10: (black_buttons[4], "A#")
        }
    
    
    midi_label = tk.Label(main_frame, text="MIDI", bg="white", font=("Helvetica", 13), anchor="w")
    midi_label.place(x=280-3, y=301-32, width=147)

    midi_var = tk.StringVar()
    midi_dropdown = ttk.Combobox(main_frame, textvariable=midi_var, state="readonly", width=18, font=("Arial", 10))
    midi_dropdown.place(x=280-3, y=331-32,width=147)
    
    midi_inputs = get_midi_input_devices()
    midi_dropdown["values"] = [name for _, name in midi_inputs]
    
    if midi_inputs:
        midi_dropdown.current(0)

    mode_label = tk.Label(main_frame, text="MODE", font=("Helvetica", 13), anchor="w", fg="black", bg="white")
    mode_label.place(x=280-3, y=421-32, width=147)
    
    player_mode_var = tk.StringVar(value="Player vs AI")
    player_mode_dropdown=ttk.Combobox(main_frame, textvariable=player_mode_var, font=("Arial", 10), state="readonly", width=18)
    player_mode_dropdown["values"]=["Player vs AI", "Player vs Player"]
    player_mode_dropdown.place(x=280-3, y=451-32, width=147)
    
    octave_label = tk.Label(main_frame, text="OCTAVE", font=("Helvetica", 13), anchor="w", fg="black", bg="white")
    octave_label.place(x=279-3, y=361-32, width=147)

    octave_var = tk.IntVar(value=4)

    octave_spinbox = ttk.Spinbox(main_frame, from_=0, to=10, textvariable=octave_var, font=("Helvetica", 12), justify="center")
    octave_spinbox.place(x=281-3, y=391-32, width=70, height=20)


    #Handle Octave Change
    def on_octave_change(*args):
        nonlocal NOTE_TO_KEY
        NOTE_TO_KEY = build_note_to_key(octave_var.get())


    octave_var.trace_add("write", on_octave_change)
    NOTE_TO_KEY = build_note_to_key(octave_var.get())
    
    
    #Handle AI Depth Slider Change
    def on_slider_change(val):
        global DEPTH
        val = int(float(val))
        if val == 1:
            DEPTH = 1
        elif val == 2:
            DEPTH = 2
        elif val == 3:
            DEPTH = 3


    depth_label = tk.Label(root, text="AI DEPTH LEVEL", font=("Helvetica", 12), anchor="center", fg="black", bg="white")
    depth_label.place(x=172-3, y=486-32)
        
    slider = tk.Scale(root, from_=1, to=3, orient="horizontal", length=378, showvalue=0, command=on_slider_change, bg="darkgrey", highlightthickness=0, troughcolor="white", sliderrelief="flat", bd=1)
    slider.place(x=45-3, y=519-32)
    slider.set(3)


    #MIDI Listener Thread
    def start_midi_listener():
        nonlocal game_over
        midi_in = open_selected_midi_input()
        
        if midi_in is None:
            print("Failed to open MIDI device.")
            return

        print("Started MIDI listening...")
        
        try:
            while True:
                if midi_in.poll():
                    midi_events = midi_in.read(10)
                    for event in midi_events:
                        status, note, velocity, _ = event[0]
                        
                        if status == 144 and velocity > 0:
                            if note in NOTE_TO_KEY:
                                button, note_name = NOTE_TO_KEY[note]
                                ###print(f"Note pressed: {note_name}")
                                
                                if toplevel_data["in_progress"]:
                                    if note_name in ["C#", "D#", "F#", "G#", "A#"]:
                                        button.invoke()
                                    else:
                                        print("Ignoring white keys while choice window is active.")
                                    continue
                                    
                                if game_over and note_name not in ["F#", "G#"]:
                                    print("Game over – ignoring MIDI")
                                    continue
                                
                                button.invoke()
                                original_color = button.cget("bg")
                                button.config(bg="lightblue")
                                button.after(100, lambda b=button, c=original_color: b.config(bg=c))
                                
                        elif status == 128 or (status == 144 and velocity == 0): 
                            print(f"Note OFF: {note}")
                            
                time.sleep(0.01)
                
        except Exception as e:
            print("Error during MIDI listening:", e)
        finally:
            midi_in.close()
            print("Closed MIDI input.")

    
    #Handle Move Undo
    def request_undo():
        state_flags["undo"] = True
        enable_white_buttons()

    undo_button = tk.Button(main_frame, text="⮌", width=15, command=request_undo, bd="1", bg="white", relief="solid", font=("Helvetica", 25))
    undo_button.place(x=195-3, y=410-32, width=64, height=64)


    #Update Reset Button Label
    def update_reset_button_label():
        mode = player_mode_var.get()
        
        if mode == "Player vs Player" and not game_over:
            reset_button.config(text="1/2", font=("Helvetica", 25)) 
        else:
            reset_button.config(text="⟳", font=("Helvetica", 27))
        update_black_key_labels()

    
    #Handle Reset/Draw Button
    def on_reset_or_draw_click():
        nonlocal game_over
        
        mode = player_mode_var.get()
        
        if mode == "Player vs Player" and not game_over:
            def handle_draw_response(result):
                if result:
                    game_over=True
                    disable_white_buttons()
                    drawGameState(screen, game_state, valid_moves, square_selected)
                    drawMoveLog(screen, game_state, move_log_font)
                    game_state.stalemate=True  
                    game_over=True
                    disable_white_buttons()

            root.after(0, lambda: custom_askyesno(root, "Draw Proposal", "Both players agree to a draw?", toplevel_data, undo_button, reset_button, backspace_button, octave_spinbox, handle_draw_response))
            
        else:
            def handle_restart_response(result):
            
                if result:
                    state_flags["reset"]=True
                    update_reset_button_label()
                    entry_from.config(state="normal")
                    entry_from.delete(0, "end")
                    entry_from.config(state="readonly")

                    entry_to.config(state="normal")
                    entry_to.delete(0, "end")
                    entry_to.config(state="readonly")

                    update_white_key_labels()
                    reset_label_colors()
                    enable_white_buttons()

            root.after(0, lambda: custom_askyesno(root, "Confirm Restart", "Are you sure you want to restart the game?", toplevel_data, undo_button, reset_button, backspace_button, octave_spinbox, handle_restart_response))


    reset_button=tk.Button(main_frame, text="⟳", width=15, bd="1", bg="white", relief="solid", font=("Helvetica", 27), command=on_reset_or_draw_click)
    reset_button.place(x=120-3, y=410-32, width=64, height=64)

    
    #Update MIDI Devices List
    def update_midi_devices():
        prev_devices = []
        while True:
            try:
                new_inputs = get_midi_input_devices()
                new_names = [name for _, name in new_inputs]
                
                if new_names != prev_devices:
                    midi_dropdown["values"] = new_names
                    
                    if new_names and (not midi_var.get() or midi_var.get() not in new_names):
                        midi_var.set(new_names[0])
                        
                    prev_devices = new_names
                    
            except Exception as e:
                print(f"Error while updating MIDI devices: {e}")
            time.sleep(3)

    
    #Handle Delete Last Character (from the entry_from or entry_to)
    def delete_last_char():
        nonlocal square_selected
        to_text = entry_to_var.get()
        from_text = entry_from_var.get()

        if len(to_text) > 0:
            deleted_char = to_text[-1]
            entry_to_var.set(to_text[:-1])
            if deleted_char.upper() in label_dict:
                label_dict[deleted_char.upper()].config(bg="white", fg="black", font=("Arial", 20))

            if len(from_text) == 2:
                from_col = from_text[0].upper()
                from_row = from_text[1]
                if from_col in label_dict:
                    label_dict[from_col].config(bg="blue", fg="white", font=("Arial", 20, "bold"))
                if from_row in label_dict:
                    label_dict[from_row].config(bg="blue", fg="white", font=("Arial", 20, "bold"))

        elif len(from_text) > 0:
            deleted_char = from_text[-1]
            entry_from_var.set(from_text[:-1])
            if deleted_char.upper() in label_dict:
                label_dict[deleted_char.upper()].config(bg="white", fg="black", font=("Arial", 20))

            if len(entry_from_var.get()) <= 1:
                square_selected = ()
            drawGameState(screen, game_state, valid_moves, square_selected)
        update_white_key_labels()


    backspace_button = tk.Button(main_frame, text="⌫", font=("Helvetica", 25), command=delete_last_char, bg="white", bd="1", relief="solid")
    backspace_button.place(x=45-3, y=410-32, width=64, height=64)


    #Update White Key Labels
    def update_white_key_labels():
        from_val = entry_from_var.get()
        to_val = entry_to_var.get()
        
        labels_lowering = "\n\n\n\n\n\n"

        
        if len(from_val) == 0:
            for i, btn in enumerate(white_buttons):
                btn.config(text=labels_lowering + chr(ord("A") + i))
                
        elif len(from_val) == 1:
            for i, btn in enumerate(white_buttons):
                btn.config(text=labels_lowering + str(i + 1))
                
        elif len(from_val) == 2 and len(to_val) == 0:
            for i, btn in enumerate(white_buttons):
                btn.config(text=labels_lowering + chr(ord("A") + i))
                
        elif len(to_val) == 1:
            for i, btn in enumerate(white_buttons):
                btn.config(text=labels_lowering + str(i + 1))
                
        else:
            for i, btn in enumerate(white_buttons):
                btn.config(text=labels_lowering + white_key_funcs[i].__name__[5:])


    update_white_key_labels()
    
    
    #Update Black Key Labels
    def update_black_key_labels():
        if toplevel_data.get("ignore_updates_promotion"):
            return
            
        black_key_labels=[]
        black_key_labels.append("AI")
        black_key_labels.append("⚔")
        black_key_labels.append(backspace_button.cget("text"))
        black_key_labels.append(reset_button.cget("text"))
        black_key_labels.append(undo_button.cget("text"))
        
        for i, btn in enumerate(black_buttons):
        
            if toplevel_data.get("ignore_updates_askyesno") and i == 3:
                btn.config(bg="green")
                return
                
            if toplevel_data.get("ignore_updates_askyesno") and i == 4:
                btn.config(bg="red")
                return
        
            btn.config(text=black_key_labels[i])
            
            if i == 0:
                btn.config(font=("Helvetica", 12), bg="black")
            if i == 1:
                btn.config(font=("Helvetica", 12), bg="black")
            if i == 2:
                btn.config(font=("Helvetica", 12), bg="black")
            if i > 2:
                if black_key_labels[i] == "1/2":
                     btn.config(font=("Helvetica", 12), bg="black")
                else:
                    btn.config(font=("Helvetica", 15), bg="black")
    
    
    update_black_key_labels()
    toplevel_data["update_black_keys"]=update_black_key_labels
    toplevel_data["black_buttons"]=black_buttons
    
    
    #Disable White Keys (to prevent players from moving using MIDI while the game is locked)
    def disable_white_buttons():
        for btn in white_buttons:
            btn.config(state="disabled")
    
    
    toplevel_data["disable_white_buttons"]=disable_white_buttons
    
    
    #Enable White Keys
    def enable_white_buttons():
        for btn in white_buttons:
            btn.config(state="normal")
    

    toplevel_data["enable_white_buttons"]=enable_white_buttons


    #Post-Move Updates
    def post_move_updates():
        nonlocal valid_moves, move_made, square_selected, player_clicks
        valid_moves = game_state.getValidMoves()
        move_made = False
        square_selected = ()
        player_clicks.clear()
        entry_to.config(state="normal")
        entry_from.config(state="normal")
        entry_from.delete(0, "end")
        entry_to.delete(0, "end")
        entry_from.config(state="readonly")
        entry_to.config(state="readonly")
        reset_label_colors()
        update_white_key_labels()
        enable_white_buttons()

    
    #Handle White Key Press
    def handle_white_keys(key):
        nonlocal square_selected, move_made, valid_moves
        
        if len(entry_from.get()) == 0:
            entry_from.config(state="normal")
            entry_from.insert("end", str(key))
            entry_from.config(state="readonly")
            label_to_highlight=label_dict[str(key)]
            label_to_highlight.config(bg="blue", fg="white", font=("Arial", 20, "bold"))
            
        elif len(entry_from.get()) == 1:
            key=column_row_dict[key]
            entry_from.config(state="normal")
            entry_from.insert("end", str(key))
            entry_from.config(state="readonly")
            label_to_highlight = label_dict[str(key)]
            label_to_highlight.config(bg="blue", fg="white", font=("Arial", 20, "bold"))

            col_char = entry_from.get()[0].upper()
            row_char = entry_from.get()[1]

            col = ord(col_char) - ord("A")
            row=8 - int(row_char)

            piece = game_state.board[row][col]
            current_player = "w" if game_state.white_to_move else "b"

            if piece == "--" or piece[0] != current_player:
                entry_from.config(state="normal")
                entry_from.delete(0, "end")
                entry_from.config(state="readonly")
                reset_label_colors()
                update_white_key_labels()
                return

            square_selected = (row, col)
            player_clicks.clear()
            player_clicks.append(square_selected)
            drawGameState(screen, game_state, valid_moves, square_selected)

        elif len(entry_from.get()) == 2 and len(entry_to.get()) == 0:
            entry_to.config(state="normal")
            entry_to.insert("end", str(key))
            entry_to.config(state="readonly")
            label_to_highlight = label_dict[str(key)]
            label_to_highlight.config(bg="red", fg="white", font=("Arial", 20, "bold"))

        elif len(entry_to.get()) == 1:
            key = column_row_dict[key]
            entry_to.config(state="normal")
            entry_to.insert("end", str(key))
            entry_to.config(state="readonly")
            label_to_highlight = label_dict[str(key)]
            label_to_highlight.config(bg="red", fg="white", font=("Arial", 20, "bold"))

            col_from_char = entry_from.get()[0].upper()
            row_from_char = entry_from.get()[1]
            col_from = ord(col_from_char) - ord("A")
            row_from = 8 - int(row_from_char)

            col_to_char = entry_to.get()[0].upper()
            row_to_char = entry_to.get()[1]
            col_to = ord(col_to_char) - ord("A")
            row_to = 8 - int(row_to_char)

            square_selected = (row_from, col_from)
            player_clicks.clear()
            player_clicks.append(square_selected)

            move = ENGINE.Move((row_from, col_from), (row_to, col_to), game_state.board)
            move_executed = False

            for valid_move in valid_moves:
                if move == valid_move:
                    promotion_piece = None

                    if move.is_pawn_promotion:
                        disable_white_buttons()
                        def ask_promotion_and_continue():
                            promotion_piece = ask_promotion_choice(root, "w" if game_state.white_to_move else "b", embed, toplevel_data)
                            game_state.makeMove(valid_move, promotion_choice=promotion_piece)
                            animateMove(valid_move, screen, game_state.board, clock)
                            post_move_updates()

                        root.after(10, ask_promotion_and_continue)
                        return

                    game_state.makeMove(valid_move, promotion_choice=promotion_piece)
                    animateMove(valid_move, screen, game_state.board, clock)
                    
                    move_made = True
                    square_selected = ()
                    player_clicks.clear()
                    move_executed = True
                    break

            if move_executed:
                valid_moves = game_state.getValidMoves()
                move_made = False
                drawGameState(screen, game_state, valid_moves, square_selected)

                entry_to.config(state="normal")
                entry_from.config(state="normal")
                entry_from.delete(0, "end")
                entry_to.delete(0, "end")
                entry_from.config(state="readonly")
                entry_to.config(state="readonly")
                reset_label_colors()

            else:
                to_text = entry_to.get()
                to_col = to_text[0].upper() if len(to_text) >= 1 else None
                to_row = to_text[1] if len(to_text) >= 2 else None

                entry_to.config(state="normal")
                entry_to.delete(0, "end")
                entry_to.config(state="readonly")
                update_white_key_labels()

                if to_col in label_dict:
                    label_dict[to_col].config(bg="white", fg="black", font=("Arial", 20))
                if to_row in label_dict:
                    label_dict[to_row].config(bg="white", fg="black", font=("Arial", 20))

                from_text = entry_from.get()
                
                if len(from_text) == 2:
                    from_col = from_text[0].upper()
                    from_row = from_text[1]
                    if from_col in label_dict:
                        label_dict[from_col].config(bg="blue", fg="white", font=("Arial", 20, "bold"))
                    if from_row in label_dict:
                        label_dict[from_row].config(bg="blue", fg="white", font=("Arial", 20, "bold"))
                        
        update_white_key_labels()


    threading.Thread(target=update_midi_devices, daemon=True).start()
    
    try:
        threading.Thread(target=start_midi_listener, daemon=True).start()
    except:
        pass


    root.update()
    embed.update()


    game_state=ENGINE.GameState()
    valid_moves=game_state.getValidMoves()
    move_made=False
    animate=False
    loadImages()


    square_selected=()
    player_clicks=[]
    game_over=False
    ai_thinking=False
    move_undone=False
    move_finder_process=None
    return_queue=None
    move_log_font=p.font.SysFont("Arial", 14, False, False)
    player_one=True
    running=True


    #Main Pygame Loop
    def pygame_loop():
        nonlocal running, move_made, animate, square_selected, player_clicks, game_over
        nonlocal ai_thinking, move_undone, move_finder_process, valid_moves, game_state, return_queue

        while running:
            mode = player_mode_var.get()
            player_two = mode == "Player vs Player"
            human_turn = (game_state.white_to_move and player_one) or (not game_state.white_to_move and player_two)
            
            for e in p.event.get():
                if e.type == p.QUIT:
                    running = False
                    p.quit()
                    root.quit()
                    sys.exit()

                elif e.type == p.MOUSEBUTTONDOWN:
                    if not game_over:
                        location = p.mouse.get_pos()
                        
                        col = location[0] // SQUARE_SIZE
                        row = location[1] // SQUARE_SIZE
                        
                        if square_selected == (row, col) or col >= 8:
                            square_selected = ()
                            player_clicks = []
                            
                        else:
                            square_selected = (row, col)
                            player_clicks.append(square_selected)
                            
                        if len(player_clicks) == 2 and human_turn:
                            move = ENGINE.Move(player_clicks[0], player_clicks[1], game_state.board)
                            
                            for i in range(len(valid_moves)):
                                if move == valid_moves[i]:
                                    move = valid_moves[i]
                                    promotion_piece = None

                                    if move.is_pawn_promotion:
                                        disable_white_buttons()
                                        promotion_piece = ask_promotion_choice(root, "w" if game_state.white_to_move else "b", embed, toplevel_data)
                                        enable_white_buttons()

                                    game_state.makeMove(move, promotion_choice=promotion_piece)

                                    move_made = True
                                    animate = True
                                    square_selected = ()
                                    player_clicks = []
                                    
                            if not move_made:
                                player_clicks = [square_selected]

                elif e.type == p.KEYDOWN:
                
                    if e.key == p.K_z:
                        game_state.undoMove()
                        move_made = True
                        animate = False
                        game_over = False
                        if ai_thinking and move_finder_process:
                            move_finder_process.terminate()
                            ai_thinking = False
                        move_undone = True
                        
                    if e.key == p.K_r:
                        game_state = ENGINE.GameState()
                        valid_moves = game_state.getValidMoves()
                        square_selected = ()
                        player_clicks = []
                        move_made = False
                        animate = False
                        game_over = False
                        if ai_thinking and move_finder_process:
                            move_finder_process.terminate()
                            ai_thinking = False
                        move_undone = True

            if not game_over and not human_turn and not move_undone:
            
                if not ai_thinking:
                    ai_thinking = True
                    return_queue = Queue()
                    move_finder_process = Process(target=AI.findBestMove, args=(game_state, valid_moves, return_queue, DEPTH))
                    move_finder_process.start()
                    
                elif not move_finder_process.is_alive():
                    ai_move = return_queue.get()
                    if ai_move is None:
                        ai_move = AI.findRandomMove(valid_moves)
                    game_state.makeMove(ai_move)
                    move_made = True
                    animate = True
                    ai_thinking = False

            if state_flags["reset"]:
                enable_white_buttons()
                game_state = ENGINE.GameState()
                valid_moves = game_state.getValidMoves()
                square_selected = ()
                player_clicks = []
                move_made = False
                animate = False
                game_over = False
                if ai_thinking and move_finder_process:
                    move_finder_process.terminate()
                    ai_thinking = False
                move_undone = False
                state_flags["reset"] = False
            
            if state_flags["undo"]:
                game_state.undoMove()
                valid_moves = game_state.getValidMoves()
                square_selected = ()
                player_clicks = []
                move_made = True
                animate = False
                game_over = False
                if ai_thinking and move_finder_process:
                    move_finder_process.terminate()
                    ai_thinking = False
                move_undone = True
                state_flags["undo"] = False
            
            if move_made:
                if animate:
                    animateMove(game_state.move_log[-1], screen, game_state.board, clock)
                valid_moves = game_state.getValidMoves()
                move_made = False
                animate = False
                move_undone = False

            drawGameState(screen, game_state, valid_moves, square_selected)
            
            if not game_over:
                drawMoveLog(screen, game_state, move_log_font)

            #GAME OVER - Checkmate
            if game_state.checkmate:
                game_over = True
                disable_white_buttons()
                if player_mode_var.get() == "Player vs Player":
                    if game_over:
                        reset_button.config(text="⟳", font=("Helvetica", 27))
                    else:
                        reset_button.config(text="1/2", font=("Helvetica", 25))

                if game_state.white_to_move:
                    drawEndGameText(screen, "CHECKMATE - BLACK WINS")
                    update_reset_button_label()
                else:
                    drawEndGameText(screen, "CHECKMATE - WHITE WINS")
                    update_reset_button_label()
                    
            #GAME OVER - Stalemate
            elif game_state.stalemate:
                game_over = True
                disable_white_buttons()
                
                if player_mode_var.get() == "Player vs Player":
                    if game_over:
                        reset_button.config(text="⟳", font=("Helvetica", 27))
                    else:
                        reset_button.config(text="1/2", font=("Helvetica", 25))

                drawEndGameText(screen, "STALEMATE")
                update_reset_button_label()

            clock.tick(MAX_FPS)
            p.display.flip()
            update_reset_button_label()

    threading.Thread(target=pygame_loop, daemon=True).start()
    root.mainloop()


#Draw Game State
def drawGameState(screen, game_state, valid_moves, square_selected):
    drawBoard(screen)
    highlightSquares(screen, game_state, valid_moves, square_selected)
    drawPieces(screen, game_state.board)


#Draw Chess Board
def drawBoard(screen):
    global colors
    colors = [p.Color("#f0d9b5"), p.Color("#b58863")]
    for row in range(DIMENSION):
        for column in range(DIMENSION):
            color = colors[((row + column) % 2)]
            p.draw.rect(screen, color, p.Rect(column * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))


#Highlight Squares (last move, check, valid moves)
def highlightSquares(screen, game_state, valid_moves, square_selected):
    if (len(game_state.move_log)) > 0:
        last_move = game_state.move_log[-1]
        s = p.Surface((SQUARE_SIZE, SQUARE_SIZE))
        s.set_alpha(100)
        s.fill(p.Color("green"))
        screen.blit(s, (last_move.end_col * SQUARE_SIZE, last_move.end_row * SQUARE_SIZE))
    
    if game_state.inCheck():
        if game_state.white_to_move:
            king_pos = game_state.white_king_location
        else:
            king_pos = game_state.black_king_location
        s = p.Surface((SQUARE_SIZE, SQUARE_SIZE))
        s.set_alpha(150)
        s.fill(p.Color("red"))
        screen.blit(s, (king_pos[1] * SQUARE_SIZE, king_pos[0] * SQUARE_SIZE))
            
    if square_selected != ():
        row, col = square_selected
        if game_state.board[row][col][0] == (
                "w" if game_state.white_to_move else "b"):

            s = p.Surface((SQUARE_SIZE, SQUARE_SIZE))
            s.set_alpha(100)
            s.fill(p.Color("yellow"))
            screen.blit(s, (col * SQUARE_SIZE, row * SQUARE_SIZE))

            s.fill(p.Color("yellow"))
            for move in valid_moves:
                if move.start_row == row and move.start_col == col:
                    screen.blit(s, (move.end_col * SQUARE_SIZE, move.end_row * SQUARE_SIZE))


#Draw Pieces
def drawPieces(screen, board):
    for row in range(DIMENSION):
        for column in range(DIMENSION):
            piece = board[row][column]
            if piece != "--":
                screen.blit(IMAGES[piece], p.Rect(column * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))


#Draw Move Log
def drawMoveLog(screen, game_state, font):
    move_log_rect = p.Rect(BOARD_WIDTH+20, 0, MOVE_LOG_PANEL_WIDTH, MOVE_LOG_PANEL_HEIGHT)
    p.draw.rect(screen, p.Color("white"), move_log_rect)
    move_log = game_state.move_log
    move_texts = []
    
    for i in range(0, len(move_log), 2):
        move_string = str(i // 2 + 1) + ". " + str(move_log[i]) + " "
        if i + 1 < len(move_log):
            move_string += str(move_log[i + 1]) + "  "
        move_texts.append(move_string)

    moves_per_row = 3
    padding = 5
    line_spacing = 2
    text_y = padding
    
    for i in range(0, len(move_texts), moves_per_row):
        text = ""
        for j in range(moves_per_row):
            if i + j < len(move_texts):
                text += move_texts[i + j]

        text_object = font.render(text, True, p.Color("black"))
        text_location = move_log_rect.move(padding, text_y)
        screen.blit(text_object, text_location)
        text_y += text_object.get_height() + line_spacing


#Draw End Game Text
def drawEndGameText(screen, text):
    font = p.font.SysFont("Helvetica", 32, True, False)
    text_object = font.render(text, False, p.Color("gray"))
    text_location = p.Rect(0, 0, BOARD_WIDTH, BOARD_HEIGHT).move(BOARD_WIDTH / 2 - text_object.get_width() / 2, BOARD_HEIGHT / 2 - text_object.get_height() / 2)
    screen.blit(text_object, text_location)
    text_object = font.render(text, False, p.Color("black"))
    screen.blit(text_object, text_location.move(2, 2))


#Animate Moves
def animateMove(move, screen, board, clock):
    global colors
    d_row = move.end_row - move.start_row
    d_col = move.end_col - move.start_col
    frames_per_square = 10
    frame_count = (abs(d_row) + abs(d_col)) * frames_per_square
    
    for frame in range(frame_count + 1):
        row, col = (move.start_row + d_row * frame / frame_count, move.start_col + d_col * frame / frame_count)
        drawBoard(screen)
        drawPieces(screen, board)

        color = colors[(move.end_row + move.end_col) % 2]
        end_square = p.Rect(move.end_col * SQUARE_SIZE, move.end_row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
        p.draw.rect(screen, color, end_square)

        if move.piece_captured != "--":
            if move.is_enpassant_move:
                enpassant_row = move.end_row + 1 if move.piece_captured[0] == "b" else move.end_row - 1
                end_square = p.Rect(move.end_col * SQUARE_SIZE, enpassant_row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
            screen.blit(IMAGES[move.piece_captured], end_square)

        screen.blit(IMAGES[move.piece_moved], p.Rect(col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))
        p.display.flip()
        clock.tick(60)


#Program Entry Point
if __name__ == "__main__":
    main()
