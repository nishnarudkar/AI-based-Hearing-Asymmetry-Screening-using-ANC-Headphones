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
from PIL import Image, ImageTk

class ModernButton(tk.Button):
    """Custom modern button with hover effects and professional styling"""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.default_bg = kwargs.get('bg', '#2c3e50')
        self.hover_bg = kwargs.get('hover_bg', '#34495e')
        self.active_bg = kwargs.get('active_bg', '#1a252f')
        
        # Set default button properties for better visibility
        self.config(
            relief='flat',
            borderwidth=2,
            cursor='hand2',
            font=kwargs.get('font', ('Segoe UI', 14, 'bold')),
            padx=15,
            pady=8,
            highlightthickness=0
        )
        
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<Button-1>", self.on_click)
        
    def on_enter(self, event):
        self.config(bg=self.hover_bg)
        
    def on_leave(self, event):
        self.config(bg=self.default_bg)
        
    def on_click(self, event):
        self.config(bg=self.active_bg)
        self.after(100, lambda: self.config(bg=self.default_bg))

class HearingScreeningApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Professional Hearing Asymmetry Screening")
        self.root.geometry("1000x700")
        self.root.resizable(False, False)
        
        # Professional color palette
        self.colors = {
            'primary': '#2c3e50',      # Dark blue-gray
            'secondary': '#34495e',    # Lighter blue-gray
            'accent': '#3498db',       # Professional blue
            'success': '#27ae60',      # Professional green
            'warning': '#f39c12',      # Professional orange
            'danger': '#e74c3c',       # Professional red
            'light': '#ecf0f1',       # Light gray
            'dark': '#2c3e50',        # Dark text
            'white': '#ffffff',        # Pure white
            'gradient_start': '#2c3e50', # Gradient start
            'gradient_end': '#34495e',   # Gradient end
            'card_bg': '#ffffff',      # Card background
            'border': '#bdc3c7'        # Subtle border
        }
        
        # Create modern gradient background
        self.canvas = tk.Canvas(self.root, bg=self.colors['white'], highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)
        
        # Create subtle gradient effect
        self.create_gradient_background()
        
        # Load and display logo
        try:
            self.logo_image = Image.open("logo.png").resize((60, 60), Image.LANCZOS)
            self.logo_photo = ImageTk.PhotoImage(self.logo_image)
            self.canvas.create_image(80, 60, image=self.logo_photo, anchor='center')
        except FileNotFoundError:
            print("Logo file 'logo.png' not found. Skipping logo display.")
        except Exception as e:
            print(f"Error loading logo: {e}")
        
        # Application state
        self.current_screen = "welcome"
        self.test_frequencies = [1000, 2000]
        self.sample_rate = 44100
        self.reference_level = 0.1
        self.thresholds = {'left': {}, 'right': {}}
        self.current_test = None
        self.test_results = []
        
        # Adaptive testing parameters
        self.reversals_target = 2
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
        
    def create_gradient_background(self):
        """Create a subtle professional gradient background"""
        width = 1000
        height = 700
        
        # Create multiple gradient layers for depth
        for i in range(height):
            # Calculate gradient color
            ratio = i / height
            r1, g1, b1 = int(self.colors['gradient_start'][1:3], 16), int(self.colors['gradient_start'][3:5], 16), int(self.colors['gradient_start'][5:7], 16)
            r2, g2, b2 = int(self.colors['gradient_end'][1:3], 16), int(self.colors['gradient_end'][3:5], 16), int(self.colors['gradient_end'][5:7], 16)
            
            r = int(r1 + (r2 - r1) * ratio)
            g = int(g1 + (g2 - g1) * ratio)
            b = int(b1 + (b2 - b1) * ratio)
            
            color = f'#{r:02x}{g:02x}{b:02x}'
            self.canvas.create_line(0, i, width, i, fill=color, width=1)
        
        # Add subtle pattern overlay
        for i in range(0, width, 50):
            for j in range(0, height, 50):
                self.canvas.create_oval(i, j, i+2, j+2, fill=self.colors['white'], outline='', stipple='gray50')
        
    def setup_fonts(self):
        try:
            self.title_font = font.Font(family="Segoe UI", size=28, weight="bold")
            self.subtitle_font = font.Font(family="Segoe UI", size=20, weight="normal")
            self.button_font = font.Font(family="Segoe UI", size=14, weight="bold")
            self.text_font = font.Font(family="Segoe UI", size=12, weight="normal")
            self.small_text_font = font.Font(family="Segoe UI", size=10, weight="normal")
            self.card_title_font = font.Font(family="Segoe UI", size=16, weight="bold")
            # NEW: Even smaller font for detailed explanations
            self.tiny_text_font = font.Font(family="Segoe UI", size=9, weight="normal") 
        except:
            self.title_font = font.Font(family="Arial", size=28, weight="bold")
            self.subtitle_font = font.Font(family="Arial", size=20, weight="normal")
            self.button_font = font.Font(family="Arial", size=14, weight="bold")
            self.text_font = font.Font(family="Arial", size=12, weight="normal")
            self.small_text_font = font.Font(family="Arial", size=10, weight="normal")
            self.card_title_font = font.Font(family="Arial", size=16, weight="bold")
            self.tiny_text_font = font.Font(family="Arial", size=9, weight="normal")
        
    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        # Professional progress bar styling
        style.configure('TProgressbar', 
                        background=self.colors['accent'], 
                        troughcolor=self.colors['light'],
                        bordercolor=self.colors['border'],
                        lightcolor=self.colors['accent'],
                        darkcolor=self.colors['accent'])
        
        # Professional button styling
        style.configure('TButton',
                        font=self.button_font,
                        background=self.colors['primary'],
                        foreground=self.colors['white'],
                        padding=12,
                        relief='flat',
                        borderwidth=0)
        
        style.map('TButton',
                  background=[('active', self.colors['secondary'])],
                  foreground=[('active', self.colors['white'])])
        
    def create_widgets(self):
        # Main container with card-like appearance
        self.main_frame = tk.Frame(self.canvas, bg=self.colors['card_bg'], 
                                  relief='flat', bd=2, highlightbackground=self.colors['border'])
        self.main_frame.place(relx=0.5, rely=0.5, anchor='center', width=900, height=600)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            self.main_frame, 
            variable=self.progress_var, 
            maximum=100,
            length=600,
            style='TProgressbar'
        )
        
    def create_card(self, parent, title, content_widgets, buttons=None):
        """Create a professional card layout"""
        # Clear existing content
        for widget in parent.winfo_children():
            widget.destroy()
        
        # Card header
        header_frame = tk.Frame(parent, bg=self.colors['primary'], height=60)
        header_frame.pack(fill='x', pady=(0, 20))
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(header_frame, text=title, font=self.title_font, 
                              bg=self.colors['primary'], fg=self.colors['white'])
        title_label.pack(expand=True)
        
        # Content area
        content_frame = tk.Frame(parent, bg=self.colors['card_bg'])
        content_frame.pack(fill='both', expand=True, padx=30, pady=(0, 20))
        
        # Add content widgets to content_frame instead of parent
        for widget in content_widgets:
            widget.pack(in_=content_frame, pady=10)
        
        # Button area
        if buttons:
            button_frame = tk.Frame(parent, bg=self.colors['card_bg'])
            button_frame.pack(fill='x', padx=30, pady=(20, 30))
            button_frame.pack_propagate(False)  # Prevent frame from shrinking
            
            # Create a container frame for buttons to center them
            button_container = tk.Frame(button_frame, bg=self.colors['card_bg'])
            button_container.pack(expand=True)
            
            for i, (text, command, color) in enumerate(buttons):
                btn = ModernButton(button_container, text=text, command=command, 
                                 bg=color, fg=self.colors['white'], font=self.button_font)
                btn.pack(side='left', padx=15)
            
            # Ensure button frame has minimum height
            button_frame.configure(height=80)
        
    def clear_screen(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()
            
    def show_welcome_screen(self):
        self.clear_screen()
        self.current_screen = "welcome"
        
        # Create card layout first
        self.create_card(
            self.main_frame,
            "Professional Hearing Screening System",
            [],  # Empty content list - we'll add widgets after
            [("Begin Screening", self.show_consent_screen, self.colors['accent'])]
        )
        
        # Now add content widgets to the content area
        content_frame = self.main_frame.winfo_children()[1]  # Get the content frame
        
        title_label = tk.Label(content_frame, text="🎧 Professional Hearing Screening", 
                              font=self.title_font, bg=self.colors['card_bg'], fg=self.colors['primary'])
        title_label.pack(pady=10)
        
        desc_text = """Welcome to the Advanced Hearing Asymmetry Screening System

This professional-grade screening tool provides comprehensive hearing assessment
using advanced adaptive algorithms and clinical-grade protocols.

- Clinical-grade accuracy with adaptive threshold testing
- Professional audiogram visualization
- Comprehensive asymmetry analysis
- Professional reporting and recommendations"""
        
        desc_label = tk.Label(content_frame, text=desc_text, font=self.text_font,
                             bg=self.colors['card_bg'], fg=self.colors['dark'],
                             justify='center', wraplength=600)
        desc_label.pack(pady=10)
        
    def show_consent_screen(self):
        self.clear_screen()
        self.current_screen = "consent"
        
        # Create card layout first
        self.create_card(
            self.main_frame,
            "Professional Notice & Consent",
            [],  # Empty content list - we'll add widgets after
            [("I Understand - Continue", self.show_device_check, self.colors['success']),
             ("Return to Start", self.show_welcome_screen, self.colors['secondary'])]
        )
        
        # Now add content widgets to the content area
        content_frame = self.main_frame.winfo_children()[1]  # Get the content frame
        
        title_label = tk.Label(content_frame, text="⚠️ Professional Notice", 
                              font=self.title_font, bg=self.colors['card_bg'], fg=self.colors['warning'])
        title_label.pack(pady=10)
        
        consent_text = """IMPORTANT PROFESSIONAL DISCLAIMER

This screening tool is designed for professional use and demonstration purposes.
It is NOT intended for clinical diagnosis or medical decision-making.

PROFESSIONAL USE ONLY:
- Results are for screening purposes only
- Consult qualified audiologists for clinical decisions
- Ensure proper calibration and equipment setup
- Follow professional testing protocols

By proceeding, you acknowledge this is a professional demonstration tool."""
        
        consent_label = tk.Label(content_frame, text=consent_text, font=self.text_font,
                                bg=self.colors['card_bg'], fg=self.colors['dark'],
                                justify='left', wraplength=600)
        consent_label.pack(pady=10)
        
    def show_device_check(self):
        self.clear_screen()
        self.current_screen = "device_check"
        
        # Create card layout first
        self.create_card(
            self.main_frame,
            "Equipment Calibration",
            [],  # Empty content list - we'll add widgets after
            [("Proceed to Calibration", self.show_calibration_screen, self.colors['success']),
             ("Return", self.show_consent_screen, self.colors['secondary'])]
        )
        
        # Now add content widgets to the content area
        content_frame = self.main_frame.winfo_children()[1]  # Get the content frame
        
        title_label = tk.Label(content_frame, text="🎧 Equipment Calibration", 
                              font=self.title_font, bg=self.colors['card_bg'], fg=self.colors['primary'])
        title_label.pack(pady=10)
        
        check_text = """PROFESSIONAL EQUIPMENT SETUP

1. Ensure high-quality headphones are properly positioned
2. Verify left and right channel functionality
3. Test audio levels for optimal performance
4. Confirm quiet testing environment

Click below to test individual channels:"""
        
        check_label = tk.Label(content_frame, text=check_text, font=self.text_font,
                              bg=self.colors['card_bg'], fg=self.colors['dark'],
                              justify='left', wraplength=600)
        check_label.pack(pady=10)
        
        # Channel test buttons
        test_frame = tk.Frame(content_frame, bg=self.colors['card_bg'])
        test_frame.pack(pady=20)
        
        left_btn = ModernButton(test_frame, text="🔊 Test Left Channel", 
                               command=lambda: self.play_channel_test('left'),
                               bg=self.colors['accent'], fg=self.colors['white'],
                               font=self.button_font, padx=20, pady=10)
        left_btn.pack(side='left', padx=10)
        
        right_btn = ModernButton(test_frame, text="🔊 Test Right Channel", 
                                command=lambda: self.play_channel_test('right'),
                                bg=self.colors['accent'], fg=self.colors['white'],
                                font=self.button_font, padx=20, pady=10)
        right_btn.pack(side='left', padx=10)
        
        self.channel_status = tk.Label(test_frame, text="", font=self.text_font,
                                      bg=self.colors['card_bg'], fg=self.colors['accent'])
        self.channel_status.pack(pady=10)
        
    def show_calibration_screen(self):
        self.clear_screen()
        self.current_screen = "calibration"
        
        # Create a unique, compact layout with better organization
        # Header with gradient effect
        header_frame = tk.Frame(self.main_frame, bg=self.colors['primary'], height=50)
        header_frame.pack(fill='x', pady=(0, 15))
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(header_frame, text="🎧 Volume Calibration", font=self.subtitle_font, 
                              bg=self.colors['primary'], fg=self.colors['white'])
        title_label.pack(expand=True)
        
        # Main content area with compact design
        content_frame = tk.Frame(self.main_frame, bg=self.colors['card_bg'])
        content_frame.pack(fill='both', expand=True, padx=25, pady=(0, 15))
        
        # Compact title
        title_label = tk.Label(content_frame, text="🔧 Professional Calibration", 
                              font=self.subtitle_font, bg=self.colors['card_bg'], fg=self.colors['primary'])
        title_label.pack(pady=(5, 8))
        
        # Compact instructions
        instr_text = """PROFESSIONAL VOLUME CALIBRATION

We will present a 1000 Hz reference tone for calibration.
Adjust your system volume to a comfortable, professional level.

CALIBRATION PROTOCOL:
- Reference frequency: 1000 Hz
- Target level: Comfortable but clear
- Duration: 1 second
- This establishes your baseline threshold"""
        
        instr_label = tk.Label(content_frame, text=instr_text, font=self.small_text_font,
                              bg=self.colors['card_bg'], fg=self.colors['dark'],
                              justify='left', wraplength=500)
        instr_label.pack(pady=(0, 15))
        
        # Compact volume control section with modern styling
        volume_frame = tk.Frame(content_frame, bg=self.colors['light'], relief='flat', bd=1)
        volume_frame.pack(pady=(0, 15), padx=20, fill='x')
        
        # Volume label with icon
        volume_header = tk.Frame(volume_frame, bg=self.colors['light'])
        volume_header.pack(fill='x', padx=15, pady=(10, 5))
        
        tk.Label(volume_header, text="🔊 Volume Level:", font=self.text_font,
                bg=self.colors['light'], fg=self.colors['primary']).pack(side='left')
        
        # Current volume display
        self.volume_display = tk.Label(volume_header, text="50%", font=self.text_font,
                                      bg=self.colors['light'], fg=self.colors['accent'])
        self.volume_display.pack(side='right')
        
        # Compact volume scale with better styling
        self.volume_var = tk.DoubleVar(value=50)
        volume_scale = tk.Scale(volume_frame, from_=10, to=100, orient='horizontal',
                               variable=self.volume_var, length=300, font=self.small_text_font,
                               bg=self.colors['light'], troughcolor=self.colors['white'],
                               sliderrelief='flat', command=self.update_volume_display,
                               highlightthickness=0, fg=self.colors['dark'])
        volume_scale.pack(pady=(0, 10))
        
        # Add volume level indicators
        level_frame = tk.Frame(volume_frame, bg=self.colors['light'])
        level_frame.pack(fill='x', padx=15, pady=(0, 5))
        
        tk.Label(level_frame, text="Low", font=self.small_text_font,
                bg=self.colors['light'], fg=self.colors['dark']).pack(side='left')
        tk.Label(level_frame, text="High", font=self.small_text_font,
                bg=self.colors['light'], fg=self.colors['dark']).pack(side='right')
        
        # Compact play button with modern styling
        play_btn = ModernButton(volume_frame, text="▶ Play Reference Tone", 
                               command=self.play_reference_tone,
                               bg=self.colors['accent'], fg=self.colors['white'],
                               font=self.small_text_font, padx=15, pady=8)
        play_btn.pack(pady=(0, 10))
        
        # Compact navigation buttons with modern styling
        button_frame = tk.Frame(self.main_frame, bg=self.colors['card_bg'])
        button_frame.pack(fill='x', padx=25, pady=(10, 20))
        
        # Create compact buttons with better spacing and modern icons
        complete_btn = ModernButton(button_frame, text="✓ Calibration Complete", 
                                   command=self.show_test_instructions,
                                   bg=self.colors['success'], fg=self.colors['white'],
                                   font=self.text_font)
        complete_btn.pack(side='left', padx=(0, 10), pady=5)
        
        return_btn = ModernButton(button_frame, text="← Return", 
                                 command=self.show_device_check,
                                 bg=self.colors['secondary'], fg=self.colors['white'],
                                 font=self.text_font)
        return_btn.pack(side='left', padx=(10, 0), pady=5)
        
        # Add a subtle progress indicator
        progress_indicator = tk.Frame(button_frame, bg=self.colors['accent'], height=3)
        progress_indicator.pack(fill='x', pady=(10, 0))
        
    def show_test_instructions(self):
        self.clear_screen()
        self.current_screen = "instructions"
        
        # COMPLETELY REDESIGNED - FORCE BUTTON VISIBILITY
        # Header
        header_frame = tk.Frame(self.main_frame, bg=self.colors['primary'], height=60)
        header_frame.pack(fill='x', pady=(0, 20))
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(header_frame, text="📋 Testing Protocol", font=self.title_font, 
                              bg=self.colors['primary'], fg=self.colors['white'])
        title_label.pack(expand=True)
        
        # Main content area - LIMITED HEIGHT TO FORCE BUTTON VISIBILITY
        content_frame = tk.Frame(self.main_frame, bg=self.colors['card_bg'], height=400)
        content_frame.pack(fill='x', padx=30, pady=(0, 20))
        content_frame.pack_propagate(False)  # FORCE HEIGHT
        
        # Title
        title_label = tk.Label(content_frame, text="📋 Professional Testing Protocol", 
                              font=self.title_font, bg=self.colors['card_bg'], fg=self.colors['primary'])
        title_label.pack(pady=10)
        
        # Instructions - SHORTER TEXT
        instr_text = """PROFESSIONAL TESTING INSTRUCTIONS

TEST PROTOCOL:
- Adaptive threshold testing using 2-down, 1-up algorithm
- Professional-grade frequency testing (1000 Hz, 2000 Hz)
- Binaural testing for asymmetry detection

RESPONSE PROTOCOL:
- Press SPACEBAR when you hear a tone
- No response for silent trials
- Maintain focus throughout testing

TEST DURATION: Approximately 2-3 minutes"""
        
        instr_label = tk.Label(content_frame, text=instr_text, font=self.text_font,
                              bg=self.colors['card_bg'], fg=self.colors['dark'],
                              justify='left', wraplength=600)
        instr_label.pack(pady=10)
        
        # SPACEBAR instruction - COMPACT
        key_frame = tk.Frame(content_frame, bg=self.colors['light'], relief='ridge', bd=2)
        key_frame.pack(pady=5, padx=50, fill='x')
        
        key_label = tk.Label(key_frame, text="⌨️ PRESS SPACEBAR TO RESPOND TO TONES", 
                            font=self.small_text_font, bg=self.colors['light'], fg=self.colors['primary'],
                            pady=5, padx=15)
        key_label.pack()
        
        # START TEST BUTTON - FIXED LAYOUT
        start_button_frame = tk.Frame(self.main_frame, bg=self.colors['card_bg'])
        start_button_frame.pack(fill='x', padx=30, pady=20)
        
        # Make button HUGE and impossible to miss
        start_test_btn = ModernButton(start_button_frame, text="🚀 START HEARING TEST NOW!", 
                                     command=self.start_hearing_test,
                                     bg=self.colors['success'], fg=self.colors['white'],
                                     font=self.button_font, padx=60, pady=25)
        start_test_btn.pack(pady=20)
        
        # Clear instruction
        instruction_label = tk.Label(start_button_frame, text="CLICK THIS BUTTON TO BEGIN THE TEST", 
                                   font=self.text_font, bg=self.colors['card_bg'], fg=self.colors['dark'])
        instruction_label.pack(pady=(10, 0))
        
        # Navigation button
        return_frame = tk.Frame(self.main_frame, bg=self.colors['card_bg'])
        return_frame.pack(fill='x', padx=30, pady=20)
        
        return_btn = ModernButton(return_frame, text="← Return to Calibration", 
                                 command=self.show_calibration_screen,
                                 bg=self.colors['secondary'], fg=self.colors['white'],
                                 font=self.text_font)
        return_btn.pack()
        
    def show_test_screen(self):
        self.clear_screen()
        self.current_screen = "testing"
        
        # Professional test interface
        self.progress_bar = ttk.Progressbar(self.main_frame, variable=self.progress_var,
                                           maximum=100, length=600, style='TProgressbar')
        self.progress_bar.pack(pady=(40, 10))
        
        self.progress_label = tk.Label(self.main_frame, text="0%", font=self.subtitle_font,
                                      bg=self.colors['card_bg'], fg=self.colors['primary'])
        self.progress_label.pack(pady=5)
        
        self.status_label = tk.Label(self.main_frame, text="Initializing test protocol...", 
                                    font=self.subtitle_font, bg=self.colors['card_bg'], fg=self.colors['primary'])
        self.status_label.pack(pady=10)
        
        # Ear indicator
        self.ear_frame = tk.Frame(self.main_frame, bg=self.colors['card_bg'])
        self.ear_frame.pack(pady=15)
        
        self.ear_label = tk.Label(self.ear_frame, text="", font=self.title_font,
                                 bg=self.colors['card_bg'], fg=self.colors['accent'])
        self.ear_label.pack()
        
        # Response area with professional styling
        response_frame = tk.Frame(self.main_frame, bg=self.colors['light'], relief='ridge', bd=3)
        response_frame.pack(pady=30, padx=50, fill='x')
        
        tk.Label(response_frame, text="🎵 RESPONSE PROTOCOL", font=self.card_title_font,
                bg=self.colors['light'], fg=self.colors['primary'], pady=20).pack()
        
        self.response_status = tk.Label(response_frame, text="Maintaining professional focus...", 
                                       font=self.text_font, bg=self.colors['light'], fg=self.colors['dark'],
                                       pady=15)
        self.response_status.pack()
        
        self.pulse_response_area(response_frame)
        
        self.test_info = tk.Label(self.main_frame, text="", font=self.text_font,
                                 bg=self.colors['card_bg'], fg=self.colors['dark'])
        self.test_info.pack(pady=15)
        
    def pulse_response_area(self, frame):
        colors = [self.colors['light'], self.colors['white']]
        def pulse():
            if self.current_screen == "testing":
                current_color = frame.cget("bg")
                next_color = colors[0] if current_color == colors[1] else colors[1]
                frame.config(bg=next_color)
                self.root.after(800, pulse)
        self.root.after(0, pulse)
        
    def show_results_screen(self):
        self.clear_screen()
        self.current_screen = "results"
        
        # Header
        header_frame = tk.Frame(self.main_frame, bg=self.colors['primary'], height=60)
        header_frame.pack(fill='x', pady=(0, 20))
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(header_frame, text="📊 Test Results", font=self.title_font, 
                              bg=self.colors['primary'], fg=self.colors['white'])
        title_label.pack(expand=True)
        
        # Main content area
        content_frame = tk.Frame(self.main_frame, bg=self.colors['card_bg'])
        content_frame.pack(fill='both', expand=True, padx=30, pady=(0, 20))
        
        # Professional analysis
        analysis = self.analyze_asymmetry()
        
        # RESULT STATUS - PROMINENT AND CLEAR
        result_status_frame = tk.Frame(content_frame, bg=self.colors['card_bg'])
        result_status_frame.pack(pady=(10, 5), fill='x')
        
        status_color = self.colors['warning'] if analysis['asymmetry_detected'] else self.colors['success']
        status_text = "⚠️ ASYMMETRY DETECTED" if analysis['asymmetry_detected'] else "✅ NO ASYMMETRY DETECTED"
        
        status_label = tk.Label(result_status_frame, text=status_text, font=self.title_font,
                               bg=self.colors['card_bg'], fg=status_color)
        status_label.pack(pady=5)
        
        # CLEAR RESULT EXPLANATION
        if analysis['asymmetry_detected']:
            result_explanation = f"""HEARING ASYMMETRY DETECTED

Your test results show a significant difference between your left and right ears.
Maximum difference detected: {analysis['max_difference']:.1f} dB
Affected frequencies: {', '.join(map(str, analysis['problematic_frequencies']))} Hz

⚠️ IMPORTANT: This requires professional medical attention!

RECOMMENDATIONS:
- Schedule an appointment with an audiologist or ENT specialist
- Get a comprehensive hearing evaluation
- Consider additional diagnostic testing
- Monitor for any changes in hearing function

This screening result indicates you should seek professional medical evaluation."""
        else:
            result_explanation = f"""NO SIGNIFICANT ASYMMETRY DETECTED

Your hearing appears balanced between both ears.
Maximum difference detected: {analysis['max_difference']:.1f} dB

✅ This is a normal result!

RECOMMENDATIONS:
- Continue regular hearing health monitoring
- Maintain current hearing protection practices
- Schedule routine screening as recommended
- This result indicates normal hearing symmetry"""
        
        # --- MODIFICATION START ---
        # Use the new tiny_text_font for the explanation to save vertical space
        explanation_label = tk.Label(result_status_frame, text=result_explanation, font=self.tiny_text_font,
                                   bg=self.colors['card_bg'], fg=self.colors['dark'],
                                   justify='left', wraplength=600)
        explanation_label.pack(pady=(5, 10))
        
        # Action buttons
        # Create a container for buttons to ensure they are grouped and centered
        button_container_frame = tk.Frame(content_frame, bg=self.colors['card_bg'])
        button_container_frame.pack(pady=(10, 20), fill='x')
        button_container_frame.pack_propagate(False) # Prevent shrinking
        button_container_frame.configure(height=80) # Give it a fixed height to ensure buttons fit

        # Inner frame to center the buttons horizontally
        button_inner_frame = tk.Frame(button_container_frame, bg=self.colors['card_bg'])
        button_inner_frame.pack(expand=True) # This will center the inner frame

        new_screening_btn = ModernButton(button_inner_frame, text="🔄 New Screening", 
                                        command=self.restart_test,
                                        bg=self.colors['accent'], fg=self.colors['white'],
                                        font=self.button_font)
        new_screening_btn.pack(side='left', padx=5) # Reduced padx for more horizontal space

        # New button to view audiogram separately
        view_audiogram_btn = ModernButton(button_inner_frame, text="📈 View Detailed Audiogram",
                                          command=self.show_audiogram_screen,
                                          bg=self.colors['primary'], fg=self.colors['white'],
                                          font=self.button_font)
        view_audiogram_btn.pack(side='left', padx=5) # Reduced padx

        exit_btn = ModernButton(button_inner_frame, text="Exit System", 
                               command=self.root.quit,
                               bg=self.colors['secondary'], fg=self.colors['white'],
                               font=self.button_font)
        exit_btn.pack(side='left', padx=5) # Reduced padx
        # --- MODIFICATION END ---
        
        # Professional success animation
        if not analysis['asymmetry_detected']:
            self.root.after(500, self.show_professional_success)
            
    def show_professional_success(self):
        """Show professional success indicators instead of confetti"""
        success_canvas = tk.Canvas(self.root, width=1000, height=700, bg='', highlightthickness=0)
        success_canvas.place(x=0, y=0, relwidth=1, relheight=1)
        success_canvas.lower(self.main_frame)
        
        # Create professional success indicators
        indicators = []
        for i in range(8):
            x = random.randint(100, 900)
            y = random.randint(50, 650)
            size = random.randint(20, 40)
            
            # Professional checkmark
            indicator = success_canvas.create_text(x, y, text="✓", font=("Arial", size, "bold"),
                                                fill=self.colors['success'])
            indicators.append({'id': indicator, 'speed': random.uniform(0.5, 1.5)})
        
        def animate_success():
            for indicator in indicators:
                success_canvas.move(indicator['id'], 0, indicator['speed'])
                
                if success_canvas.coords(indicator['id'])[1] > 700:
                    success_canvas.delete(indicator['id'])
            
            if success_canvas.find_all():
                self.root.after(50, animate_success)
            else:
                success_canvas.destroy()
        
        animate_success()
        
    def show_audiogram_screen(self):
        """Displays the audiogram in a new, dedicated window."""
        audiogram_window = tk.Toplevel(self.root)
        audiogram_window.title("Detailed Audiogram Results")
        audiogram_window.geometry("900x600") # Adjust size as needed
        audiogram_window.transient(self.root) # Make it appear on top of the main window
        audiogram_window.grab_set() # Make it modal (user must interact with it)

        # Create a frame for the audiogram within the new window
        audiogram_frame = tk.Frame(audiogram_window, bg=self.colors['card_bg'])
        audiogram_frame.pack(fill='both', expand=True, padx=20, pady=20)

        # Header for the audiogram window
        header_label = tk.Label(audiogram_frame, text="📈 Detailed Audiogram", 
                                font=self.title_font, bg=self.colors['card_bg'], fg=self.colors['primary'])
        header_label.pack(pady=(0, 15))

        # Create the audiogram within this new frame
        self.create_audiogram(audiogram_frame, figsize=(10, 5)) # Use a larger figsize for detail

        # Add a close button
        close_btn = ModernButton(audiogram_frame, text="Close", 
                                 command=audiogram_window.destroy,
                                 bg=self.colors['secondary'], fg=self.colors['white'],
                                 font=self.button_font)
        close_btn.pack(pady=15)

        # Center the new window
        audiogram_window.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (audiogram_window.winfo_width() // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (audiogram_window.winfo_height() // 2)
        audiogram_window.geometry(f"+{x}+{y}")
        
    def create_audiogram(self, parent_frame, figsize=(8, 4)):
        """Create professional audiogram visualization on a given parent frame"""
        fig, ax = plt.subplots(figsize=figsize)
        fig.patch.set_facecolor(self.colors['card_bg'])
        
        frequencies = list(self.test_frequencies)
        left_thresholds = [self.thresholds['left'].get(f, 0) for f in frequencies]
        right_thresholds = [self.thresholds['right'].get(f, 0) for f in frequencies]
        
        # Professional plotting
        ax.plot(frequencies, left_thresholds, 'o-', color=self.colors['accent'], linewidth=3, 
                markersize=14, label='Left Ear', zorder=2)
        ax.plot(frequencies, right_thresholds, 's-', color=self.colors['warning'], linewidth=3, 
                markersize=14, label='Right Ear', zorder=2)
        
        # Professional annotations
        for i, (freq, left, right) in enumerate(zip(frequencies, left_thresholds, right_thresholds)):
            ax.annotate(f'{left:.0f} dB', (freq, left), xytext=(0, 15), textcoords='offset points', 
                        ha='center', fontsize=11, color=self.colors['accent'], weight='bold')
            ax.annotate(f'{right:.0f} dB', (freq, right), xytext=(0, -20), textcoords='offset points', 
                        ha='center', fontsize=11, color=self.colors['warning'], weight='bold')
        
        # Professional styling
        ax.set_xlabel('Frequency (Hz)', fontsize=14, fontweight='bold', color=self.colors['dark'])
        ax.set_ylabel('Threshold (dB)', fontsize=14, fontweight='bold', color=self.colors['dark'])
        ax.set_title('Professional Audiogram Results', fontsize=16, fontweight='bold', color=self.colors['primary'])
        ax.grid(True, alpha=0.3, linestyle='--', color=self.colors['border'])
        ax.legend(fontsize=12, frameon=True, framealpha=0.9, loc='upper right')
        ax.set_xscale('log')
        ax.set_xticks(frequencies)
        ax.set_xticklabels([f'{f} Hz' for f in frequencies])
        ax.invert_yaxis()
        
        # Professional color scheme
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color(self.colors['border'])
        ax.spines['bottom'].set_color(self.colors['border'])
        
        canvas = FigureCanvasTkAgg(fig, parent_frame)
        canvas.get_tk_widget().pack(pady=15, fill='both', expand=True)
        canvas.draw()
        
    def play_channel_test(self, channel):
        try:
            duration = 0.7
            frequency = 1000
            t = np.linspace(0, duration, int(self.sample_rate * duration))
            tone = 0.3 * np.sin(2 * np.pi * frequency * t)
            
            if channel == 'left':
                stereo_tone = np.column_stack([tone, np.zeros_like(tone)])
                self.channel_status.config(text="LEFT CHANNEL ACTIVE", fg=self.colors['accent'])
            else:
                stereo_tone = np.column_stack([np.zeros_like(tone), tone])
                self.channel_status.config(text="RIGHT CHANNEL ACTIVE", fg=self.colors['warning'])
                
            sd.play(stereo_tone, self.sample_rate)
            self.root.after(1000, lambda: self.channel_status.config(text=""))
            
        except Exception as e:
            messagebox.showerror("Audio Error", f"Could not play audio: {str(e)}")
            
    def update_reference_level(self, value):
        self.reference_level = float(value) / 100.0 * 0.3
        
    def update_volume_display(self, value):
        """Update the volume display label"""
        if hasattr(self, 'volume_display'):
            self.volume_display.config(text=f"{int(float(value))}%")
        self.update_reference_level(value)
        
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
        # Show countdown screen first
        self.show_countdown_screen()
        
    def show_countdown_screen(self):
        """Show interactive countdown before starting the test"""
        self.clear_screen()
        self.current_screen = "countdown"
        
        # Header
        header_frame = tk.Frame(self.main_frame, bg=self.colors['primary'], height=60)
        header_frame.pack(fill='x', pady=(0, 20))
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(header_frame, text="Test Starting", font=self.title_font, 
                              bg=self.colors['primary'], fg=self.colors['white'])
        title_label.pack(expand=True)
        
        # Content area
        content_frame = tk.Frame(self.main_frame, bg=self.colors['card_bg'])
        content_frame.pack(fill='both', expand=True, padx=30, pady=(0, 20))
        
        # Countdown label
        self.countdown_label = tk.Label(content_frame, text="", font=self.title_font,
                                       bg=self.colors['card_bg'], fg=self.colors['accent'])
        self.countdown_label.pack(expand=True)
        
        # Instructions
        instr_label = tk.Label(content_frame, text="Get ready! The test will begin in:", 
                              font=self.subtitle_font, bg=self.colors['card_bg'], fg=self.colors['dark'])
        instr_label.pack(pady=(0, 20))
        
        # Start countdown
        self.countdown_value = 3
        self.update_countdown()
        
    def update_countdown(self):
        """Update the countdown display"""
        if self.countdown_value > 0:
            self.countdown_label.config(text=str(self.countdown_value), fg=self.colors['accent'])
            self.countdown_value -= 1
            self.root.after(1000, self.update_countdown)
        else:
            self.countdown_label.config(text="GO!", fg=self.colors['success'])
            self.root.after(1000, self.begin_test)
            
    def begin_test(self):
        """Actually start the hearing test"""
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
        
        self.response_status.config(text="Maintaining professional focus...", fg=self.colors['dark'])
        
        progress = (self.current_test_index / self.total_tests) * 100
        self.progress_var.set(progress)
        self.progress_label.config(text=f"{int(progress)}%")
        
        ear_color = self.colors['accent'] if ear == 'left' else self.colors['warning']
        ear_symbol = '👂 LEFT EAR' if ear == 'left' else '👂 RIGHT EAR'
        
        self.ear_label.config(text=ear_symbol, fg=ear_color)
        
        self.status_label.config(text=f"Testing Frequency: {freq} Hz")
        self.test_info.config(text=f"Test {self.current_test_index + 1} of {self.total_tests}")
        
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
            recommendation = f"""PROFESSIONAL ASSESSMENT REQUIRED

Asymmetry detected with maximum difference: {max_difference:.1f} dB
Affected frequencies: {', '.join(map(str, problematic_frequencies))} Hz

RECOMMENDATION:
- Consult qualified audiologist for comprehensive evaluation
- Consider additional diagnostic testing
- Monitor for changes in hearing function
- This screening result requires professional follow-up"""
        else:
            recommendation = f"""PROFESSIONAL SCREENING COMPLETE

No significant asymmetry detected (maximum difference: {max_difference:.1f} dB)
Hearing function appears balanced across tested frequencies

RECOMMENDATION:
- Continue regular hearing health monitoring
- Maintain current hearing protection practices
- Schedule routine screening as recommended
- This result indicates normal hearing symmetry"""
            
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
            if messagebox.askyesno("Exit Test", "Are you sure you want to exit the screening?"):
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
        self.app.response_status.config(text="Maintaining professional focus...", fg=self.app.colors['dark'])
        
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
        
        # Professional feedback
        if self.is_catch_trial:
            if not heard:
                self.app.response_status.config(text="✓ Correct Response (No tone)", fg=self.app.colors['success'])
            else:
                self.app.response_status.config(text="⚠️ False Positive Response", fg=self.app.colors['warning'])
        else:
            if heard:
                self.app.response_status.config(text="✓ Tone Detected", fg=self.app.colors['success'])
            else:
                self.app.response_status.config(text="○ No Response Recorded", fg=self.app.colors['dark'])
                
        if not self.is_catch_trial:
            self.update_level(heard)
        
        self.app.root.after(300, self.run_trial)
        
    def on_no_response(self):
        if not self.waiting_for_response:
            return
        self.on_response(False)
        
    def update_level(self, heard):
        new_level = self.current_level
        
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
            new_level = self.current_level + self.step_size
            self.consecutive_heard = 0
            
            if self.last_direction == 'down':
                self.reversals.append(self.current_level)
                if len(self.reversals) >= 1:
                    self.step_size = self.app.step_size_small
            self.last_direction = 'up'
        
        self.current_level = max(-60, min(0, new_level))
        
    def complete_test(self):
        if len(self.reversals) >= 2:
            threshold = np.mean(self.reversals[-2:])
        elif self.reversals:
            threshold = self.reversals[-1]
        else:
            valid_responses = [r for r in self.responses if not r['catch_trial']]
            if valid_responses:
                threshold_levels = []
                for i in range(1, len(valid_responses)):
                    if valid_responses[i]['heard'] != valid_responses[i-1]['heard']:
                        threshold_levels.append(valid_responses[i]['level'])
                threshold = np.mean(threshold_levels) if threshold_levels else self.current_level
            else:
                threshold = 0

        self.app.on_threshold_complete(self.frequency, self.ear, threshold)


if __name__ == "__main__":
    try:
        Image.new('RGBA', (60, 60), (255, 255, 255, 0)).save("logo.png")
        print("Created a dummy 'logo.png' for demonstration. Replace it with your actual logo.")
    except Exception as e:
        print(f"Could not create dummy logo: {e}. Ensure Pillow is installed.")

    root = tk.Tk()
    app = HearingScreeningApp(root)
    root.mainloop()
