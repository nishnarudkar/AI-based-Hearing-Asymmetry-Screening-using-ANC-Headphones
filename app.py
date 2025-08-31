import tkinter as tk
from tkinter import ttk, messagebox, font
import numpy as np
import threading
import time
import random
import math
from collections import defaultdict
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import sounddevice as sd

class HearingScreeningApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AI-based Hearing Asymmetry Screening")
        self.root.geometry("800x600")
        
        # Create gradient background
        self.canvas = tk.Canvas(self.root, bg='#f0f0f0')
        self.canvas.pack(fill='both', expand=True)
        self.canvas.create_rectangle(0, 0, 800, 600, fill='#1abc9c', outline='')
        self.canvas.create_rectangle(0, 300, 800, 600, fill='#3498db', outline='')
        
        # Application state
        self.current_screen = "welcome"
        self.test_frequencies = [1000, 2000]  # Reduced for demo
        self.sample_rate = 44100
        self.reference_level = 0.1
        self.thresholds = {'left': {}, 'right': {}}
        self.current_test = None
        self.test_results = []
        
        # Adaptive testing parameters
        self.reversals_target = 2  # Reduced for speed
        self.step_size_large = 20
        self.step_size_small = 10
        
        # UI Components
        self.setup_fonts()
        self.setup_styles()
        self.create_widgets()
        self.show_welcome_screen()
        
        # Bind keyboard events
        self.root.bind('<Key>', self.handle_keypress)
        self.root.focus_set()
        
    def setup_fonts(self):
        try:
            self.title_font = font.Font(family="Helvetica Neue", size=26, weight="bold")
            self.subtitle_font = font.Font(family="Helvetica Neue", size=18)
            self.button_font = font.Font(family="Helvetica Neue", size=14, weight="bold")
            self.text_font = font.Font(family="Helvetica Neue", size=12)
        except:
            self.title_font = font.Font(family="Arial", size=26, weight="bold")
            self.subtitle_font = font.Font(family="Arial", size=18)
            self.button_font = font.Font(family="Arial", size=14, weight="bold")
            self.text_font = font.Font(family="Arial", size=12)
        
    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure('TProgressbar', 
                        background='#1abc9c', 
                        troughcolor='#e0e0e0',
                        bordercolor='#1abc9c',
                        lightcolor='#1abc9c',
                        darkcolor='#1abc9c')
        
        style.configure('TButton',
                        font=self.button_font,
                        background='#3498db',
                        foreground='white',
                        padding=10)
        
        style.map('TButton',
                  background=[('active', '#2980b9')],
                  foreground=[('active', 'white')])
        
    def create_widgets(self):
        # Main container
        self.main_frame = tk.Frame(self.canvas, bg='#f0f0f0')  # Changed from transparent
        self.main_frame.place(relx=0.5, rely=0.5, anchor='center')
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            self.main_frame, 
            variable=self.progress_var, 
            maximum=100,
            length=400,
            style='TProgressbar'
        )
        
    def clear_screen(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()
            
    def show_welcome_screen(self):
        self.clear_screen()
        self.current_screen = "welcome"
        
        title_label = tk.Label(
            self.main_frame,
            text="🎧 Hearing Asymmetry Screening",
            font=self.title_font,
            bg='#f0f0f0',
            fg='white',
            highlightthickness=0,
            pady=10
        )
        title_label.pack(pady=(30, 15))
        
        desc_text = """Welcome to the Hearing Test! 🔊
This quick demo (1-2 minutes) checks your hearing using headphones. 🎧
Ensure a quiet environment for best results. 🤫"""
        
        desc_label = tk.Label(
            self.main_frame,
            text=desc_text,
            font=self.text_font,
            bg='#f0f0f0',
            fg='white',
            justify='center',
            wraplength=600
        )
        desc_label.pack(pady=15)
        
        start_btn = tk.Button(
            self.main_frame,
            text="Start Screening 🚀",
            font=self.button_font,
            bg='#e74c3c',
            fg='white',
            pady=15,
            padx=30,
            command=self.show_consent_screen,
            cursor='hand2',
            relief='flat',
            borderwidth=0
        )
        start_btn.pack(pady=20)
        start_btn.bind("<Enter>", lambda e: start_btn.config(bg='#c0392b'))
        start_btn.bind("<Leave>", lambda e: start_btn.config(bg='#e74c3c'))
        
        instr_label = tk.Label(
            self.main_frame,
            text="Press SPACE or click to proceed ⌨️",
            font=self.text_font,
            bg='#f0f0f0',
            fg='#ecf0f1'
        )
        instr_label.pack()
        
    def show_consent_screen(self):
        self.clear_screen()
        self.current_screen = "consent"
        
        title_label = tk.Label(
            self.main_frame,
            text="⚠️ Important Notice",
            font=self.title_font,
            bg='#f0f0f0',
            fg='#e74c3c'
        )
        title_label.pack(pady=(30, 15))
        
        consent_text = """This demo is for showcase purposes only. 🩺
It is NOT a medical tool.

• Results are not for diagnosis
• Consult an audiologist for hearing concerns
• Ensure headphones work properly

By proceeding, you understand this is a demo."""
        
        consent_label = tk.Label(
            self.main_frame,
            text=consent_text,
            font=self.text_font,
            bg='#f0f0f0',
            fg='white',
            justify='left',
            wraplength=600
        )
        consent_label.pack(pady=15)
        
        button_frame = tk.Frame(self.main_frame, bg='#f0f0f0')
        button_frame.pack(pady=20)
        
        agree_btn = tk.Button(
            button_frame,
            text="I Understand - Continue ✅",
            font=self.button_font,
            bg='#27ae60',
            fg='white',
            pady=10,
            padx=20,
            command=self.show_device_check,
            cursor='hand2',
            relief='flat',
            borderwidth=0
        )
        agree_btn.pack(side='left', padx=10)
        agree_btn.bind("<Enter>", lambda e: agree_btn.config(bg='#219a52'))
        agree_btn.bind("<Leave>", lambda e: agree_btn.config(bg='#27ae60'))
        
        back_btn = tk.Button(
            button_frame,
            text="Back ⬅️",
            font=self.button_font,
            bg='#7f8c8d',
            fg='white',
            pady=10,
            padx=20,
            command=self.show_welcome_screen,
            cursor='hand2',
            relief='flat',
            borderwidth=0
        )
        back_btn.pack(side='left', padx=10)
        back_btn.bind("<Enter>", lambda e: back_btn.config(bg='#6c7a89'))
        back_btn.bind("<Leave>", lambda e: back_btn.config(bg='#7f8c8d'))
        
    def show_device_check(self):
        self.clear_screen()
        self.current_screen = "device_check"
        
        title_label = tk.Label(
            self.main_frame,
            text="🎧 Headphone Check",
            font=self.title_font,
            bg='#f0f0f0',
            fg='white'
        )
        title_label.pack(pady=(30, 15))
        
        check_text = """Put on your headphones and position them correctly. 🎧
We'll play sounds to check left and right channels. 🔊"""
        
        check_label = tk.Label(
            self.main_frame,
            text=check_text,
            font=self.text_font,
            bg='#f0f0f0',
            fg='white',
            justify='center',
            wraplength=600
        )
        check_label.pack(pady=15)

        self.channel_status = tk.Label(
            self.main_frame,
            text="",
            font=self.text_font,
            bg='#f0f0f0',
            fg='#ecf0f1'
        )
        self.channel_status.pack(pady=10)
        
        button_frame = tk.Frame(self.main_frame, bg='#f0f0f0')
        button_frame.pack(pady=20)
        
        left_btn = tk.Button(
            button_frame,
            text="🔊 Left Ear 👈",
            font=self.button_font,
            bg='#9b59b6',
            fg='white',
            pady=15,
            padx=20,
            command=lambda: self.play_channel_test('left'),
            cursor='hand2',
            relief='flat',
            borderwidth=0
        )
        left_btn.pack(side='left', padx=10)
        left_btn.bind("<Enter>", lambda e: left_btn.config(bg='#8e44ad'))
        left_btn.bind("<Leave>", lambda e: left_btn.config(bg='#9b59b6'))
        
        right_btn = tk.Button(
            button_frame,
            text="🔊 Right Ear 👉",
            font=self.button_font,
            bg='#e67e22',
            fg='white',
            pady=15,
            padx=20,
            command=lambda: self.play_channel_test('right'),
            cursor='hand2',
            relief='flat',
            borderwidth=0
        )
        right_btn.pack(side='left', padx=10)
        right_btn.bind("<Enter>", lambda e: right_btn.config(bg='#d35400'))
        right_btn.bind("<Leave>", lambda e: right_btn.config(bg='#e67e22'))
        
        continue_btn = tk.Button(
            self.main_frame,
            text="Headphones Ready ✓",
            font=self.button_font,
            bg='#27ae60',
            fg='white',
            pady=15,
            padx=30,
            command=self.show_calibration_screen,
            cursor='hand2',
            relief='flat',
            borderwidth=0
        )
        continue_btn.pack(pady=(30, 15))
        continue_btn.bind("<Enter>", lambda e: continue_btn.config(bg='#219a52'))
        continue_btn.bind("<Leave>", lambda e: continue_btn.config(bg='#27ae60'))
        
        back_btn = tk.Button(
            self.main_frame,
            text="← Back",
            font=self.text_font,
            bg='#7f8c8d',
            fg='white',
            pady=8,
            padx=15,
            command=self.show_consent_screen,
            cursor='hand2',
            relief='flat',
            borderwidth=0
        )
        back_btn.pack()
        back_btn.bind("<Enter>", lambda e: back_btn.config(bg='#6c7a89'))
        back_btn.bind("<Leave>", lambda e: back_btn.config(bg='#7f8c8d'))
        
    def show_calibration_screen(self):
        self.clear_screen()
        self.current_screen = "calibration"
        
        title_label = tk.Label(
            self.main_frame,
            text="🔧 Volume Calibration",
            font=self.title_font,
            bg='#f0f0f0',
            fg='white'
        )
        title_label.pack(pady=(30, 15))
        
        instr_text = """We'll play a 1000 Hz tone. 🎵
Adjust volume to a comfortable level. 🔊
This is the loudest sound you'll hear."""
        
        instr_label = tk.Label(
            self.main_frame,
            text=instr_text,
            font=self.text_font,
            bg='#f0f0f0',
            fg='white',
            justify='center',
            wraplength=600
        )
        instr_label.pack(pady=15)
        
        volume_frame = tk.Frame(self.main_frame, bg='#f0f0f0')
        volume_frame.pack(pady=20)
        
        tk.Label(
            volume_frame,
            text="Volume Level: 📶",
            font=self.subtitle_font,
            bg='#f0f0f0',
            fg='white'
        ).pack()
        
        self.volume_var = tk.DoubleVar(value=50)
        volume_scale = tk.Scale(
            volume_frame,
            from_=10,
            to=100,
            orient='horizontal',
            variable=self.volume_var,
            length=400,
            font=self.text_font,
            bg='#f0f0f0',
            troughcolor='#ecf0f1',
            sliderrelief='flat',
            command=self.update_reference_level,
            highlightthickness=0
        )
        volume_scale.pack(pady=10)
        
        play_btn = tk.Button(
            self.main_frame,
            text="🔊 Play Tone",
            font=self.button_font,
            bg='#3498db',
            fg='white',
            pady=15,
            padx=30,
            command=self.play_reference_tone,
            cursor='hand2',
            relief='flat',
            borderwidth=0
        )
        play_btn.pack(pady=15)
        play_btn.bind("<Enter>", lambda e: play_btn.config(bg='#2980b9'))
        play_btn.bind("<Leave>", lambda e: play_btn.config(bg='#3498db'))
        
        continue_btn = tk.Button(
            self.main_frame,
            text="Volume Set ✓",
            font=self.button_font,
            bg='#27ae60',
            fg='white',
            pady=15,
            padx=30,
            command=self.show_test_instructions,
            cursor='hand2',
            relief='flat',
            borderwidth=0
        )
        continue_btn.pack(pady=15)
        continue_btn.bind("<Enter>", lambda e: continue_btn.config(bg='#219a52'))
        continue_btn.bind("<Leave>", lambda e: continue_btn.config(bg='#27ae60'))
        
        back_btn = tk.Button(
            self.main_frame,
            text="← Back",
            font=self.text_font,
            bg='#7f8c8d',
            fg='white',
            pady=8,
            padx=15,
            command=self.show_device_check,
            cursor='hand2',
            relief='flat',
            borderwidth=0
        )
        back_btn.pack(pady=10)
        back_btn.bind("<Enter>", lambda e: back_btn.config(bg='#6c7a89'))
        back_btn.bind("<Leave>", lambda e: back_btn.config(bg='#7f8c8d'))
        
    def show_test_instructions(self):
        self.clear_screen()
        self.current_screen = "instructions"
        
        title_label = tk.Label(
            self.main_frame,
            text="📝 Test Instructions",
            font=self.title_font,
            bg='#f0f0f0',
            fg='white'
        )
        title_label.pack(pady=(30, 15))
        
        instr_text = """Here's how it works: 🔍

• Hear beeps in left/right ears 👂
• Press SPACEBAR when you hear a beep 🎵
• Skip if no sound is heard 🤐
• Some trials are silent (normal) ❓
• Test adjusts to find your threshold 📉

Stay focused and respond quickly! ⚡"""
        
        instr_label = tk.Label(
            self.main_frame,
            text=instr_text,
            font=self.text_font,
            bg='#f0f0f0',
            fg='white',
            justify='left',
            wraplength=600
        )
        instr_label.pack(pady=15)
        
        key_frame = tk.Frame(self.main_frame, bg='#ecf0f1', relief='ridge', bd=2)
        key_frame.pack(pady=15)
        
        key_label = tk.Label(
            key_frame,
            text="⌨️ Press SPACEBAR for beeps",
            font=self.subtitle_font,
            bg='#ecf0f1',
            fg='#e74c3c',
            pady=10,
            padx=20
        )
        key_label.pack()
        
        start_btn = tk.Button(
            self.main_frame,
            text="🎵 Start Test",
            font=self.button_font,
            bg='#e74c3c',
            fg='white',
            pady=15,
            padx=30,
            command=self.start_hearing_test,
            cursor='hand2',
            relief='flat',
            borderwidth=0
        )
        start_btn.pack(pady=20)
        start_btn.bind("<Enter>", lambda e: start_btn.config(bg='#c0392b'))
        start_btn.bind("<Leave>", lambda e: start_btn.config(bg='#e74c3c'))
        
        back_btn = tk.Button(
            self.main_frame,
            text="← Back",
            font=self.text_font,
            bg='#7f8c8d',
            fg='white',
            pady=8,
            padx=15,
            command=self.show_calibration_screen,
            cursor='hand2',
            relief='flat',
            borderwidth=0
        )
        back_btn.pack(pady=10)
        back_btn.bind("<Enter>", lambda e: back_btn.config(bg='#6c7a89'))
        back_btn.bind("<Leave>", lambda e: back_btn.config(bg='#7f8c8d'))
        
    def show_test_screen(self):
        self.clear_screen()
        self.current_screen = "testing"
        
        self.progress_bar = ttk.Progressbar(
            self.main_frame,
            variable=self.progress_var,
            maximum=100,
            length=500,
            style='TProgressbar'
        )
        self.progress_bar.pack(pady=(40, 10))
        
        self.progress_label = tk.Label(
            self.main_frame,
            text="0%",
            font=self.text_font,
            bg='#f0f0f0',
            fg='white'
        )
        self.progress_label.pack(pady=5)
        
        self.status_label = tk.Label(
            self.main_frame,
            text="Preparing test... ⚙️",
            font=self.subtitle_font,
            bg='#f0f0f0',
            fg='white'
        )
        self.status_label.pack(pady=10)
        
        self.ear_frame = tk.Frame(self.main_frame, bg='#f0f0f0')
        self.ear_frame.pack(pady=15)
        
        self.ear_label = tk.Label(
            self.ear_frame,
            text="",
            font=self.title_font,
            bg='#f0f0f0',
            fg='white'
        )
        self.ear_label.pack()
        
        response_frame = tk.Frame(self.main_frame, bg='#ecf0f1', relief='ridge', bd=3)
        response_frame.pack(pady=30, padx=50, fill='x')
        
        tk.Label(
            response_frame,
            text="🎵 Press SPACEBAR for beeps",
            font=self.subtitle_font,
            bg='#ecf0f1',
            fg='#e74c3c',
            pady=20
        ).pack()
        
        self.response_status = tk.Label(
            response_frame,
            text="Listen carefully... 👂",
            font=self.text_font,
            bg='#ecf0f1',
            fg='#7f8c8d',
            pady=10
        )
        self.response_status.pack()
        
        self.pulse_response_area(response_frame)
        
        self.test_info = tk.Label(
            self.main_frame,
            text="",
            font=self.text_font,
            bg='#f0f0f0',
            fg='#ecf0f1'
        )
        self.test_info.pack(pady=15)
        
    def pulse_response_area(self, frame):
        colors = ['#ecf0f1', '#dfe6e9']
        def pulse():
            for color in colors:
                frame.config(bg=color)
                self.root.update()
                time.sleep(0.5)
            if self.current_screen == "testing":
                self.root.after(1000, pulse)
        pulse()
        
    def show_results_screen(self):
        self.clear_screen()
        self.current_screen = "results"
        
        title_label = tk.Label(
            self.main_frame,
            text="📊 Test Results",
            font=self.title_font,
            bg='#f0f0f0',
            fg='white'
        )
        title_label.pack(pady=(20, 10))
        
        self.create_audiogram()
        
        analysis = self.analyze_asymmetry()
        
        result_frame = tk.Frame(self.main_frame, bg='#f0f0f0')
        result_frame.pack(pady=15, fill='x')
        
        status_color = '#e74c3c' if analysis['asymmetry_detected'] else '#27ae60'
        status_text = "⚠️ Asymmetry Detected" if analysis['asymmetry_detected'] else "✅ No Asymmetry"
        
        status_label = tk.Label(
            result_frame,
            text=status_text,
            font=self.subtitle_font,
            bg='#f0f0f0',
            fg=status_color
        )
        status_label.pack(pady=10)
        
        rec_label = tk.Label(
            result_frame,
            text=analysis['recommendation'],
            font=self.text_font,
            bg='#f0f0f0',
            fg='white',
            justify='center',
            wraplength=600
        )
        rec_label.pack(pady=10)
        
        button_frame = tk.Frame(self.main_frame, bg='#f0f0f0')
        button_frame.pack(pady=20)
        
        restart_btn = tk.Button(
            button_frame,
            text="🔄 Try Again",
            font=self.button_font,
            bg='#3498db',
            fg='white',
            pady=10,
            padx=20,
            command=self.restart_test,
            cursor='hand2',
            relief='flat',
            borderwidth=0
        )
        restart_btn.pack(side='left', padx=10)
        restart_btn.bind("<Enter>", lambda e: restart_btn.config(bg='#2980b9'))
        restart_btn.bind("<Leave>", lambda e: restart_btn.config(bg='#3498db'))
        
        exit_btn = tk.Button(
            button_frame,
            text="Exit ❌",
            font=self.button_font,
            bg='#7f8c8d',
            fg='white',
            pady=10,
            padx=20,
            command=self.root.quit,
            cursor='hand2',
            relief='flat',
            borderwidth=0
        )
        exit_btn.pack(side='left', padx=10)
        exit_btn.bind("<Enter>", lambda e: exit_btn.config(bg='#6c7a89'))
        exit_btn.bind("<Leave>", lambda e: exit_btn.config(bg='#7f8c8d'))
        
    def create_audiogram(self):
        fig, ax = plt.subplots(figsize=(8, 4))
        fig.patch.set_facecolor('#f0f0f0')
        
        frequencies = list(self.test_frequencies)
        left_thresholds = [self.thresholds['left'].get(f, 0) for f in frequencies]
        right_thresholds = [self.thresholds['right'].get(f, 0) for f in frequencies]
        
        ax.plot(frequencies, left_thresholds, 'o-', color='#3498db', linewidth=3, 
                markersize=12, label='Left Ear 👂', zorder=2)
        ax.plot(frequencies, right_thresholds, 's-', color='#e74c3c', linewidth=3, 
                markersize=12, label='Right Ear 👂', zorder=2)
        
        for i, (freq, left, right) in enumerate(zip(frequencies, left_thresholds, right_thresholds)):
            ax.annotate(f'{left:.0f}', (freq, left), xytext=(0, 10), textcoords='offset points', 
                        ha='center', fontsize=10, color='#3498db')
            ax.annotate(f'{right:.0f}', (freq, right), xytext=(0, -15), textcoords='offset points', 
                        ha='center', fontsize=10, color='#e74c3c')
        
        ax.set_xlabel('Frequency (Hz)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Threshold (dB)', fontsize=12, fontweight='bold')
        ax.set_title('Hearing Results 📈', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.legend(fontsize=11, frameon=True, framealpha=0.8)
        ax.set_xscale('log')
        ax.set_xticks(frequencies)
        ax.set_xticklabels([f'{f}' for f in frequencies])
        ax.invert_yaxis()
        
        canvas = FigureCanvasTkAgg(fig, self.main_frame)
        canvas.get_tk_widget().pack(pady=15)
        
    def play_channel_test(self, channel):
        try:
            duration = 0.7
            frequency = 1000
            t = np.linspace(0, duration, int(self.sample_rate * duration))
            tone = 0.3 * np.sin(2 * np.pi * frequency * t)
            
            if channel == 'left':
                stereo_tone = np.column_stack([tone, np.zeros_like(tone)])
                self.channel_status.config(text="Playing in LEFT ear 🔊", fg='#3498db')
            else:
                stereo_tone = np.column_stack([np.zeros_like(tone), tone])
                self.channel_status.config(text="Playing in RIGHT ear 🔊", fg='#e74c3c')
                
            sd.play(stereo_tone, self.sample_rate)
            self.root.after(1000, lambda: self.channel_status.config(text=""))
            
        except Exception as e:
            messagebox.showerror("Audio Error", f"Could not play audio: {str(e)}")
            
    def update_reference_level(self, value):
        self.reference_level = float(value) / 100.0 * 0.3
        
    def play_reference_tone(self):
        try:
            duration = 1.0
            frequency = 1000
            t = np.linspace(0, duration, int(self.sample_rate * duration))
            tone = self.reference_level * np.sin(2 * np.pi * frequency * t)
            stereo_tone = np.column_stack([tone, tone])
            sd.play(stereo_tone, self.sample_rate)
        except Exception as e:
            messagebox.showerror("Audio Error", f"Could not play audio: {str(e)}")
            
    def start_hearing_test(self):
        self.show_test_screen()
        self.test_results = []
        self.thresholds = {'left': {}, 'right': {}}
        
        self.test_sequence = []
        for freq in self.test_frequencies:
            for ear in ['left', 'right']:
                self.test_sequence.append((freq, ear))
        
        random.shuffle(self.test_sequence)
        self.current_test_index = 0
        self.total_tests = len(self.test_sequence)
        
        self.root.after(500, self.run_next_threshold_test)
        
    def run_next_threshold_test(self):
        if self.current_test_index >= len(self.test_sequence):
            self.show_results_screen()
            return
            
        freq, ear = self.test_sequence[self.current_test_index]
        
        self.response_status.config(text="Listen carefully... 👂", fg='#7f8c8d')
        
        progress = (self.current_test_index / self.total_tests) * 100
        self.progress_var.set(progress)
        self.progress_label.config(text=f"{int(progress)}%")
        
        ear_color = '#3498db' if ear == 'left' else '#e74c3c'
        ear_symbol = '👂 Left' if ear == 'left' else '👂 Right'
        
        self.ear_label.config(
            text=f"{ear_symbol} Ear",
            fg=ear_color
        )
        
        self.status_label.config(text=f"Frequency: {freq} Hz 🎵")
        self.test_info.config(text=f"Test {self.current_test_index + 1}/{self.total_tests} ⚡")
        
        self.current_test = AdaptiveThresholdTest(freq, ear, self)
        self.current_test.start()
        
    def on_threshold_complete(self, freq, ear, threshold):
        self.thresholds[ear][freq] = threshold
        self.current_test_index += 1
        self.root.after(500, self.run_next_threshold_test)
        
    def play_test_tone(self, frequency, ear, level_db):
        try:
            duration = 0.3
            t = np.linspace(0, duration, int(self.sample_rate * duration))
            amplitude = self.reference_level * (10 ** (level_db / 20))
            tone = amplitude * np.sin(2 * np.pi * frequency * t)
            
            envelope = np.ones_like(tone)
            fade_samples = int(0.05 * self.sample_rate)
            envelope[:fade_samples] = np.linspace(0, 1, fade_samples)
            envelope[-fade_samples:] = np.linspace(1, 0, fade_samples)
            tone *= envelope
            
            if ear == 'left':
                stereo_tone = np.column_stack([tone, np.zeros_like(tone)])
            else:
                stereo_tone = np.column_stack([np.zeros_like(tone), tone])
                
            sd.play(stereo_tone, self.sample_rate)
            return True
            
        except Exception as e:
            print(f"Audio playback error: {e}")
            return False
            
    def analyze_asymmetry(self):
        asymmetry_detected = False
        max_difference = 0
        problematic_frequencies = []
        
        differences = {}
        for freq in self.test_frequencies:
            if freq in self.thresholds['left'] and freq in self.thresholds['right']:
                diff = abs(self.thresholds['left'][freq] - self.thresholds['right'][freq])
                differences[freq] = diff
                max_difference = max(max_difference, diff)
                
                if diff >= 20:
                    asymmetry_detected = True
                    problematic_frequencies.append(freq)
                    
        freq_list = sorted(self.test_frequencies)
        for i in range(len(freq_list) - 1):
            freq1, freq2 = freq_list[i], freq_list[i + 1]
            if (freq1 in differences and freq2 in differences and 
                differences[freq1] >= 15 and differences[freq2] >= 15):
                asymmetry_detected = True
                if freq1 not in problematic_frequencies:
                    problematic_frequencies.append(freq1)
                if freq2 not in problematic_frequencies:
                    problematic_frequencies.append(freq2)
                    
        if asymmetry_detected:
            recommendation = f"""Asymmetry detected (max difference: {max_difference:.1f} dB). ⚠️
Consult an audiologist for evaluation.
This is a demo, not a diagnosis."""
        else:
            recommendation = f"""No asymmetry detected (max: {max_difference:.1f} dB). ✅
Hearing seems balanced.
This is a demo result."""
            
        return {
            'asymmetry_detected': asymmetry_detected,
            'max_difference': max_difference,
            'problematic_frequencies': problematic_frequencies,
            'recommendation': recommendation,
            'differences': differences
        }
        
    def handle_keypress(self, event):
        if event.keysym == 'space' and self.current_test:
            self.current_test.on_response(True)
        elif event.keysym == 'Escape':
            if messagebox.askyesno("Exit Test", "Sure you want to exit?"):
                self.show_welcome_screen()
                
    def restart_test(self):
        self.thresholds = {'left': {}, 'right': {}}
        self.test_results = []
        self.current_test = None
        self.show_welcome_screen()


class AdaptiveThresholdTest:
    def __init__(self, frequency, ear, app):
        self.frequency = frequency
        self.ear = ear
        self.app = app
        
        self.current_level = -10
        self.step_size = self.app.step_size_large
        self.reversals = []
        self.responses = []
        self.trial_count = 0
        self.max_trials = 10
        self.consecutive_heard = 0
        self.last_direction = None
        self.catch_trial_probability = 0.03
        self.is_catch_trial = False
        self.waiting_for_response = False
        self.response_timer = None
        
    def start(self):
        self.run_trial()
        
    def run_trial(self):
        if self.trial_count >= self.max_trials or len(self.reversals) >= self.app.reversals_target:
            self.complete_test()
            return
            
        self.trial_count += 1
        self.is_catch_trial = random.random() < self.catch_trial_probability
        self.app.response_status.config(text="Listen carefully... 👂", fg='#7f8c8d')
        delay = random.uniform(0.3, 1.0)
        self.app.root.after(int(delay * 1000), self.present_stimulus)
        
    def present_stimulus(self):
        self.waiting_for_response = True
        if not self.is_catch_trial:
            success = self.app.play_test_tone(self.frequency, self.ear, self.current_level)
            if not success:
                self.complete_test()
                return
        self.response_timer = self.app.root.after(1000, self.on_no_response)
        
    def on_response(self, heard):
        if not self.waiting_for_response:
            return
        self.waiting_for_response = False
        if self.response_timer:
            self.app.root.after_cancel(self.response_timer)
            self.response_timer = None
            
        correct_response = not self.is_catch_trial
        self.responses.append({
            'level': self.current_level,
            'heard': heard,
            'catch_trial': self.is_catch_trial,
            'correct': heard == correct_response
        })
        
        if self.is_catch_trial:
            if not heard:
                self.app.response_status.config(text="Good! (No tone) 👍", fg='#27ae60')
            else:
                self.app.response_status.config(text="False alarm ❌", fg='#e67e22')
        else:
            if heard:
                self.app.response_status.config(text="Heard ✓", fg='#27ae60')
            else:
                self.app.response_status.config(text="Not heard 🚫", fg='#7f8c8d')
                
        if not self.is_catch_trial:
            self.update_level(heard)
        self.app.root.after(300, self.run_trial)
        
    def on_no_response(self):
        if not self.waiting_for_response:
            return
        self.on_response(False)
        
    def update_level(self, heard):
        if heard:
            self.consecutive_heard += 1
            if self.consecutive_heard >= 2:
                new_level = self.current_level - self.step_size
                self.consecutive_heard = 0
                if self.last_direction == 'up':
                    self.reversals.append(self.current_level)
                    if len(self.reversals) >= 1:
                        self.step_size = self.app.step_size_small
                self.last_direction = 'down'
            else:
                return
        else:
            new_level = self.current_level + self.step_size
            self.consecutive_heard = 0
            if self.last_direction == 'down':
                self.reversals.append(self.current_level)
                if len(self.reversals) >= 1:
                    self.step_size = self.app.step_size_small
            self.last_direction = 'up'
        
        if 'new_level' in locals():
            self.current_level = max(-60, min(0, new_level))
        
    def complete_test(self):
        valid_responses = [r for r in self.responses if not r['catch_trial']]
        if len(self.reversals) >= 2:
            threshold = np.mean(self.reversals[-2:])
        else:
            threshold_levels = []
            for i in range(1, len(valid_responses)):
                if valid_responses[i]['heard'] != valid_responses[i-1]['heard']:
                    threshold_levels.append(valid_responses[i]['level'])
            threshold = np.mean(threshold_levels) if threshold_levels else 0
        self.app.on_threshold_complete(self.frequency, self.ear, threshold)


if __name__ == "__main__":
    root = tk.Tk()
    app = HearingScreeningApp(root)
    root.mainloop()