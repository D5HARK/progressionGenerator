import tkinter as tk
from tkinter import messagebox
import random
from music21 import scale, note, chord, pitch
from PIL import Image, ImageTk
import sys
import os


# --- Music Generation Logic ---
def generate_scale(root_note_str, mode_name):
    if not any(char.isdigit() for char in root_note_str):
        root_note_str += "4"

    root_note = note.Note(root_note_str)

    mode_map = {
        'major': scale.MajorScale,
        'minor': scale.MinorScale,
        'aeolian': scale.MinorScale,
        'dorian': scale.DorianScale,
        'phrygian': scale.PhrygianScale,
        'lydian': scale.LydianScale,
        'mixolydian': scale.MixolydianScale,
        'locrian': scale.LocrianScale,
    }

    if mode_name.lower() not in mode_map:
        raise ValueError("Unsupported mode. Choose from: " + ", ".join(mode_map.keys()))

    scale_obj = mode_map[mode_name.lower()](root_note)
    pitches = scale_obj.getPitches(root_note.nameWithOctave, root_note.transpose('P8').nameWithOctave)

    fixed_notes = []
    for p in pitches:
        try:
            note_obj = note.Note(p.nameWithOctave)
            pitch_obj = note_obj.pitch
            if pitch_obj.accidental and (pitch_obj.accidental.alter > 1 or pitch_obj.accidental.alter < -1):
                pitch_obj = pitch_obj.getEnharmonic()
            fixed_notes.append(pitch_obj.name.replace('-', 'b').replace('+', '#'))
        except Exception as e:
            print("DEBUG: Failed to clean pitch", p, "→", e)
            fixed_notes.append(p.name)

    return fixed_notes


def get_diatonic_7_chords(scale_notes):
    print("DEBUG: Generating chords for scale:", scale_notes)
    chords = []

    for i in range(7):
        root = note.Note(scale_notes[i] + '4')
        third = note.Note(scale_notes[(i + 2) % 7] + '4')
        fifth = note.Note(scale_notes[(i + 4) % 7] + '4')
        seventh = note.Note(scale_notes[(i + 6) % 7] + '5')  # Better voicing

        chord_obj = chord.Chord([root, third, fifth, seventh])

        if chord_obj.commonName == 'major seventh chord':
            suffix = 'maj7'
        elif chord_obj.commonName == 'dominant seventh chord':
            suffix = '7'
        elif chord_obj.commonName == 'minor seventh chord':
            suffix = 'm7'
        elif chord_obj.commonName == 'diminished seventh chord':
            suffix = 'dim7'
        elif chord_obj.commonName == 'half-diminished seventh chord':
            suffix = 'm7b5'
        else:
            suffix = '7'

        label = chord_obj.root().name + suffix
        chords.append(label)

    return chords


def random_progression():
    notes = ['C', 'C#', 'Db', 'D', 'D#', 'Eb', 'E', 'F', 'F#', 'Gb', 'G', 'G#', 'Ab', 'A', 'A#', 'Bb', 'B']
    modes = ['major', 'minor', 'dorian', 'phrygian', 'lydian', 'mixolydian', 'aeolian', 'locrian']
    return random.choice(notes), random.choice(modes)


# --- GUI Setup ---
class ChordGeneratorApp:
    def __init__(self, root):
        try:
            # Use the path that works for bundled executables
            base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
            self.bg_image = Image.open(os.path.join(base_path, "background.jpg"))
            self.bg_image = self.bg_image.resize((1000, 800))
            self.bg_photo = ImageTk.PhotoImage(self.bg_image)
            self.bg_label = tk.Label(root, image=self.bg_photo)
            self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        except Exception as e:
            print("Background image failed to load:", e)
            root.configure(bg="#2c2f33")

        self.root = root
        self.root.title("it come with egg roll")

        try:
            self.root.iconbitmap(os.path.join(base_path, "eggwuh.ico"))  # Set the custom taskbar icon
        except Exception as e:
            print("Icon failed to load:", e)

        self.selected_note = None
        self.selected_mode = None

        self.display_label = tk.Label(root, text="Choose a root note and a mode", font=("Helvetica", 16, "bold"),
                                      fg="#ffffff", bg="#2c2f33")
        self.display_label.pack(pady=10)

        self.note_frame = tk.LabelFrame(root, text="Select Note", fg="#ffffff", bg="#23272a",
                                        font=("Helvetica", 12, "bold"), bd=2, relief="ridge")
        self.note_frame.pack(pady=5)
        self.notes = ['C', 'C#', 'Db', 'D', 'D#', 'Eb', 'E', 'F', 'F#', 'Gb', 'G', 'G#', 'Ab', 'A', 'A#', 'Bb', 'B']
        for n in self.notes:
            tk.Button(self.note_frame, text=n, width=3, command=lambda n=n: self.set_note(n), bg="#7289da", fg="white",
                      font=("Helvetica", 10, "bold")).pack(side="left", padx=1, pady=1)
        tk.Button(self.note_frame, text="Random", command=self.set_random_note, bg="#99aab5", fg="black").pack(
            side="left", padx=2)

        self.mode_frame = tk.LabelFrame(root, text="Select Mode", fg="#ffffff", bg="#23272a",
                                        font=("Helvetica", 12, "bold"), bd=2, relief="ridge")
        self.mode_frame.pack(pady=5)
        self.modes = ['major', 'minor', 'dorian', 'phrygian', 'lydian', 'mixolydian', 'aeolian', 'locrian']
        for m in self.modes:
            tk.Button(self.mode_frame, text=m, command=lambda m=m: self.set_mode(m), bg="#7289da", fg="white",
                      font=("Helvetica", 10)).pack(side="left", padx=1, pady=1)
        tk.Button(self.mode_frame, text="Random", command=self.set_random_mode, bg="#99aab5", fg="black").pack(
            side="left", padx=2)

        self.control_frame = tk.Frame(root, bg="#2c2f33")
        self.control_frame.pack(pady=10)
        self.randomize_frame = tk.Frame(self.root, bg="#2c2f33")
        self.randomize_frame.pack(pady=5)
        self.randomize_btn = None
        self.update_randomize_button()
        tk.Button(self.control_frame, text="Clear", command=self.clear_selection, bg="#f04747", fg="white",
                  font=("Helvetica", 10, "bold")).pack(side="left", padx=5)
        tk.Button(self.control_frame, text="Generate Progression", command=self.generate, bg="#43b581", fg="white",
                  font=("Helvetica", 10, "bold")).pack(side="left", padx=5)

        self.output = tk.Text(root, height=10, width=60, font=("Comic Sans MS", 12), bg="#23272a", fg="#ffffff",
                              wrap="word", bd=2, relief="groove")
        self.output.pack(pady=10)

    def set_note(self, note):
        self.selected_note = note
        self.update_display()

    def set_mode(self, mode):
        self.selected_mode = mode
        self.update_display()

    def set_random_note(self):
        self.selected_note = random.choice(self.notes)
        self.update_display()

    def set_random_mode(self):
        self.selected_mode = random.choice(self.modes)
        self.update_display()

    def clear_selection(self):
        self.selected_note = None
        self.selected_mode = None
        self.update_display()
        self.output.delete('1.0', tk.END)

    def update_display(self):
        note = self.selected_note or "?"
        mode = self.selected_mode or "?"
        self.display_label.config(text=f"Selected: {note} {mode}")

    def generate(self):
        if not self.selected_note or not self.selected_mode:
            messagebox.showerror("Error", "Please select both a note and a mode")
            return

        try:
            scale_notes = generate_scale(self.selected_note, self.selected_mode)
            chords = get_diatonic_7_chords(scale_notes)
            progression_length = random.randint(3, 7)
            if progression_length > len(chords):
                progression_length = len(chords)
            progression = random.sample(chords, progression_length)

            self.output.delete('1.0', tk.END)
            self.output.insert(tk.END,
                               f"🎼 Scale:\n  {'  |  '.join(n.replace('+', '#').replace('-', '♭') for n in scale_notes)}\n\n")
            self.output.insert(tk.END,
                               f"🎹 Diatonic 7th Chords:\n  →  {'  |  '.join(c.replace('+', '#').replace('-', '♭') for c in chords)}\n\n")
            self.output.insert(tk.END,
                               f"🎲 Random Progression:\n  →  {'  →  '.join(p.replace('+', '#').replace('-', '♭') for p in progression)}\n")

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def randomize_and_generate(self):
        self.clear_selection()
        self.set_random_note()
        self.set_random_mode()
        self.generate()
        self.update_randomize_button()

    def update_randomize_button(self):
        for widget in self.randomize_frame.winfo_children():
            widget.destroy()

        self.randomize_btn = tk.Button(
            self.randomize_frame,
            text="RANDOMIZE",
            command=self.randomize_and_generate,
            bg="#5865F2",
            fg="white",
            font=("Helvetica", 10, "bold"),
            relief="raised"
        )
        self.randomize_btn.pack(pady=4)


if __name__ == "__main__":
    root = tk.Tk()
    app = ChordGeneratorApp(root)
    root.mainloop()
