import tkinter as tk
from tkinter import messagebox
import random
import serial
import threading
import time
import csv
from datetime import datetime

# --- SERIAL CONFIGURATION ---
ser = serial.Serial('COM17', baudrate=9600, parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=1)

# --- KEY MAPPING ---
key_mapping = {
    'A': 'T', 'B': 'R', 'C': 'A', 'D': 'BACKSPACE',
    'E': 'S', 'F': 'L', 'G': 'I', 'H': 'N',
    'I': 'ENTER', 'J': 'D', 'K': 'C', 'L': 'E'
}

valid_letters = ['T', 'R', 'A', 'S', 'L', 'I', 'N', 'D', 'C', 'E']

valid_words = [
    "ART", "TIN", "SIN", "RAN", "ANT", "LID", "RID", "SAD",
    "TAR", "ARC", "CAR", "RAT", "CAT", "LAD", "DIN", "RAD",
    "SAT", "AID", "SIR", "AND"
]

# --- GLOBAL VARIABLES ---
start_time = None
game_start_timestamp = None
current_word = ""
user_input = []
sensor_data = []
sensor_csv_file = ""
timer_running = False

# --- GUI SETUP ---
root = tk.Tk()
root.title("🕹️ Serial Typing Challenge")
root.geometry("600x550")
root.configure(bg="#f0f9ff")

title = tk.Label(root, text="⌨️ SMART TYPING GLOVES", font=("Helvetica", 26, "bold"), bg="#f0f9ff", fg="#003366")
title.pack(pady=20)

word_frame = tk.Frame(root, bg="#f0f9ff")
word_frame.pack()
word_label = tk.Label(word_frame, text="📝 Word: Click Start to Begin", font=("Helvetica", 20), bg="#f0f9ff")
word_label.pack()

typed_frame = tk.Frame(root, bg="#f0f9ff")
typed_frame.pack()
typed_label = tk.Label(typed_frame, text="✍️ Typed: ", font=("Helvetica", 18), bg="#f0f9ff", fg="#333")
typed_label.pack(pady=10)

timer_frame = tk.Frame(root, bg="#f0f9ff")
timer_frame.pack()
timer_label = tk.Label(timer_frame, text="⏱️ Timer: 0.0 sec", font=("Helvetica", 16), bg="#f0f9ff", fg="#005580")
timer_label.pack(pady=10)

status_frame = tk.Frame(root, bg="#f0f9ff")
status_frame.pack()
status_msg = tk.Label(status_frame, text="🕹️ Press Start to Play!", font=("Helvetica", 16), bg="#e0f7fa", fg="#00695c", width=40, height=2, relief="groove")
status_msg.pack(pady=10)

# --- FUNCTIONS ---
def update_timer():
    if start_time and timer_running:
        elapsed = time.time() - start_time
        timer_label.config(text=f"⏱️ Timer: {elapsed:.1f} sec")
        root.after(100, update_timer)

def generate_word():
    return random.choice(valid_words)

def get_user_level(duration):
    if duration <= 40:
        return "🔥 Level 3 (Expert)"
    elif duration <= 70:
        return "⚡ Level 2 (Intermediate)"
    elif duration <= 100:
        return "🌱 Level 1 (Beginner)"
    else:
        return "❌ Unranked"

def write_to_csv(start_time_str, duration, word, typed, level):
    with open("typing_game_results.csv", mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([start_time_str, word, typed, f"{duration:.2f}", level])

def write_sensor_csv():
    global sensor_data, sensor_csv_file
    with open(sensor_csv_file, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Timestamp", "Sensor Value"])
        writer.writerows(sensor_data)


def update_typed_display():
    typed_label.config(text=f"✍️ Typed: {''.join(user_input)}")

def read_serial():
    global user_input, current_word, start_time, sensor_data, timer_running

    while True:
        try:
            line = ser.readline().decode('utf-8', 'ignore').strip()
            if not line:
                continue

            chars = line.split(',')
            for ch in chars:
                ch = ch.strip()

                # Sensor data
                if any(s in ch for s in ["F1", "F2", "F3", "F4", "X", "Y", "Z"]):
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
                    sensor_data.append([timestamp, ch])
                    continue

                key = key_mapping.get(ch)

                if key == 'BACKSPACE':
                    if user_input:
                        user_input.pop()
                elif key == 'ENTER':
                    final_input = ''.join(user_input)
                    if final_input == current_word:
                        duration = time.time() - start_time
                        timer_running = False  # stop timer
                        level = get_user_level(duration)

                        status_msg.config(
                            text=f"🎉 Correct! Time: {duration:.2f} sec\n🏆 {level}",
                            bg="#c8e6c9", fg="#1b5e20"
                        )
                        word_label.config(text="📝 Word: Click Start to Begin Again")
                        timer_label.config(text=f"⏱️ Timer: {duration:.2f} sec")

                        write_to_csv(game_start_timestamp, duration, current_word, final_input, level)
                        write_sensor_csv()
                        return
                    else:
                        messagebox.showwarning("❌ Try Again", "Incorrect word. Try again!")
                        user_input.clear()
                elif key in valid_letters:
                    if len(user_input) < len(current_word):
                        user_input.append(key)

                update_typed_display()
        except Exception as e:
            print("Error:", e)
            continue

def start_game():
    global current_word, user_input, start_time, game_start_timestamp, sensor_data, sensor_csv_file, timer_running

    current_word = generate_word()
    word_label.config(text=f"📝 Word: {current_word}")
    status_msg.config(text="⌨️ Type the word using your Morse keys!", bg="#e0f7fa", fg="#00695c")

    user_input = []
    sensor_data.clear()

    game_start_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sensor_csv_file = f"sensor_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    start_time = time.time()
    timer_running = True
    update_timer()

    threading.Thread(target=read_serial, daemon=True).start()

# --- START BUTTON ---
start_button = tk.Button(root, text="▶️ Start Game", font=("Helvetica", 16, "bold"), bg="#007acc", fg="white",
                         width=15, height=2, command=start_game, relief="raised", bd=3)
start_button.pack(pady=30)

# --- MAIN LOOP ---
root.mainloop()
