# hearing_test_kivy.py
# A Kivy replica of the Hearing Asymmetry Screening web app

import sqlite3
import numpy as np
from scipy.io.wavfile import write
from io import BytesIO
import tempfile
import os
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.checkbox import CheckBox
from kivy.uix.progressbar import ProgressBar
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.core.audio import SoundLoader
from kivy.clock import Clock
from kivy.graphics import Color, Line
from kivy.metrics import dp
import math
import random

# Initialize DB
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        surname TEXT,
        age_group TEXT,
        gender TEXT,
        headphones_correct BOOLEAN,
        anc_mode TEXT,
        left_avg REAL,
        right_avg REAL,
        dissimilarity REAL
    )''')
    conn.commit()
    conn.close()

init_db()

# Global variables
current_screen = 'login'
test_frequencies = [4000, 2000, 1000, 500, 250]
thresholds = {'left': {}, 'right': {}}
current_test = None
test_sequence = []
current_test_index = 0
total_tests = 0
step_size_large = 20
step_size_small = 10
user_id = None

# Audio functions
def generate_tone(freq=1000, duration=0.3, volume=1.0, channel='both'):
    sample_rate = 44100
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    note = np.sin(2 * np.pi * freq * t) * volume

    if channel == 'both':
        audio = np.column_stack((note, note))
    elif channel == 'left':
        silence = np.zeros_like(note)
        audio = np.column_stack((note, silence))
    else:  # right
        silence = np.zeros_like(note)
        audio = np.column_stack((silence, note))

    # Normalize to 16-bit range
    if np.max(np.abs(audio)) > 0:
        audio = audio / np.max(np.abs(audio)) * 32767 * 0.8
    audio = audio.astype(np.int16)

    bio = BytesIO()
    write(bio, sample_rate, audio)
    bio.seek(0)
    return bio.getvalue()

def play_sound(data):
    # Save to a temporary file since SoundLoader doesn't support BytesIO directly
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
        temp_file.write(data)
        temp_file_path = temp_file.name

    sound = SoundLoader.load(temp_file_path)
    if sound:
        sound.play()
        # Schedule cleanup of temporary file after playback
        Clock.schedule_once(lambda dt: os.unlink(temp_file_path), sound.length + 0.1)

def play_channel_test(channel):
    status_label = App.get_running_app().root.get_screen('device_check').ids.get('status', Label(text=''))
    status_label.text = f'Playing in {channel.upper()} ear 🔊'
    data = generate_tone(freq=1000, duration=0.7, volume=0.5, channel=channel)
    play_sound(data)
    Clock.schedule_once(lambda dt: setattr(status_label, 'text', ''), 1)

def play_reference_tone():
    data = generate_tone(freq=1000, duration=1.0, volume=1.0, channel='both')
    play_sound(data)

def play_test_tone(freq, channel, level_db):
    amplitude = math.pow(10, level_db / 20)
    data = generate_tone(freq=freq, duration=0.3, volume=amplitude, channel=channel)
    play_sound(data)

# Screen classes
class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        
        title = Label(text='User Information', size_hint_y=None, height=dp(50), font_size='20sp')
        layout.add_widget(title)
        
        self.name_input = TextInput(hint_text='Name', multiline=False)
        layout.add_widget(self.name_input)
        
        self.surname_input = TextInput(hint_text='Surname', multiline=False)
        layout.add_widget(self.surname_input)
        
        age_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40))
        age_layout.add_widget(Label(text='Age Group:'))
        self.age_child = ToggleButton(text='Child (<18)', group='age')
        self.age_adult = ToggleButton(text='Adult (18–60)', group='age', state='down')
        self.age_senior = ToggleButton(text='Senior (60+)', group='age')
        age_layout.add_widget(self.age_child)
        age_layout.add_widget(self.age_adult)
        age_layout.add_widget(self.age_senior)
        layout.add_widget(age_layout)
        
        gender_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40))
        gender_layout.add_widget(Label(text='Gender (optional):'))
        self.gender_male = ToggleButton(text='Male', group='gender')
        self.gender_female = ToggleButton(text='Female', group='gender')
        self.gender_other = ToggleButton(text='Other', group='gender')
        self.gender_none = ToggleButton(text='Prefer not to say', group='gender', state='down')
        gender_layout.add_widget(self.gender_male)
        gender_layout.add_widget(self.gender_female)
        gender_layout.add_widget(self.gender_other)
        gender_layout.add_widget(self.gender_none)
        layout.add_widget(gender_layout)
        
        headphone_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40))
        self.headphones_check = CheckBox()
        headphone_layout.add_widget(Label(text='I am wearing the headphones correctly (Left = L, Right = R).'))
        headphone_layout.add_widget(self.headphones_check)
        layout.add_widget(headphone_layout)
        
        anc_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40))
        anc_layout.add_widget(Label(text='ANC Mode:'))
        self.anc_on = ToggleButton(text='ON', group='anc', state='down')
        self.anc_off = ToggleButton(text='OFF', group='anc')
        anc_layout.add_widget(self.anc_on)
        anc_layout.add_widget(self.anc_off)
        layout.add_widget(anc_layout)
        
        submit_btn = Button(text='Submit and Proceed', on_press=self.submit)
        layout.add_widget(submit_btn)
        
        self.add_widget(layout)
    
    def submit(self, instance):
        global user_id
        data = {
            'name': self.name_input.text,
            'surname': self.surname_input.text,
            'age_group': 'Child (<18)' if self.age_child.state == 'down' else 
                         'Adult (18–60)' if self.age_adult.state == 'down' else 'Senior (60+)',
            'gender': 'Male' if self.gender_male.state == 'down' else 
                      'Female' if self.gender_female.state == 'down' else 
                      'Other' if self.gender_other.state == 'down' else 'Prefer not to say',
            'headphones_correct': self.headphones_check.active,
            'anc_mode': 'ON' if self.anc_on.state == 'down' else 'OFF'
        }
        # Save to DB
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute('''INSERT INTO users (name, surname, age_group, gender, headphones_correct, anc_mode)
                     VALUES (?, ?, ?, ?, ?, ?)''', (data['name'], data['surname'], data['age_group'], 
                                                    data['gender'], data['headphones_correct'], data['anc_mode']))
        user_id = c.lastrowid
        conn.commit()
        conn.close()
        App.get_running_app().root.current = 'welcome'

class WelcomeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        
        title = Label(text='🎧 Hearing Asymmetry Screening', size_hint_y=None, height=dp(50), font_size='20sp')
        layout.add_widget(title)
        
        subtitle = Label(text='Welcome to the Hearing Test! 🔊\nThis quick demo (1-2 minutes) checks your hearing using headphones. 🎧\nEnsure a quiet environment for best results. 🤫')
        layout.add_widget(subtitle)
        
        start_btn = Button(text='Start Screening 🚀', size_hint_y=None, height=dp(50), on_press=self.start)
        layout.add_widget(start_btn)
        
        self.add_widget(layout)
    
    def start(self, instance):
        App.get_running_app().root.current = 'consent'

class ConsentScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        
        title = Label(text='⚠️ Important Notice', size_hint_y=None, height=dp(50), font_size='20sp')
        layout.add_widget(title)
        
        warning_text = Label(text='This demo is for showcase purposes only. 🩺\nIt is NOT a medical tool.\n- Results are not for diagnosis\n- Consult an audiologist for hearing concerns\n- Ensure headphones work properly')
        layout.add_widget(warning_text)
        
        agree_btn = Button(text='I Understand - Continue ✅', size_hint_y=None, height=dp(50), on_press=self.agree)
        layout.add_widget(agree_btn)
        
        back_btn = Button(text='Back ⬅️', size_hint_y=None, height=dp(50), on_press=self.back)
        layout.add_widget(back_btn)
        
        self.add_widget(layout)
    
    def agree(self, instance):
        App.get_running_app().root.current = 'device_check'
    
    def back(self, instance):
        App.get_running_app().root.current = 'welcome'

class DeviceCheckScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        
        title = Label(text='🎧 Headphone Check', size_hint_y=None, height=dp(50), font_size='20sp')
        layout.add_widget(title)
        
        instr = Label(text='Put on your headphones and position them correctly. 🎧\nWe\'ll play sounds to check left and right channels. 🔊')
        layout.add_widget(instr)
        
        btn_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50))
        left_btn = Button(text='🔊 Left Ear 👈', on_press=lambda x: self.play_channel('left'))
        right_btn = Button(text='🔊 Right Ear 👉', on_press=lambda x: self.play_channel('right'))
        btn_layout.add_widget(left_btn)
        btn_layout.add_widget(right_btn)
        layout.add_widget(btn_layout)
        
        self.status = Label(text='', size_hint_y=None, height=dp(30))
        self.ids['status'] = self.status
        layout.add_widget(self.status)
        
        ready_btn = Button(text='Headphones Ready ✓', size_hint_y=None, height=dp(50), on_press=self.ready)
        layout.add_widget(ready_btn)
        
        back_btn = Button(text='← Back', size_hint_y=None, height=dp(50), on_press=self.back)
        layout.add_widget(back_btn)
        
        self.add_widget(layout)
    
    def play_channel(self, channel):
        play_channel_test(channel)
    
    def ready(self, instance):
        App.get_running_app().root.current = 'calibration'
    
    def back(self, instance):
        App.get_running_app().root.current = 'consent'

class CalibrationScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        
        title = Label(text='🔧 Volume Calibration', size_hint_y=None, height=dp(50), font_size='20sp')
        layout.add_widget(title)
        
        instr = Label(text='We\'ll play a 1000 Hz tone. 🎵\nAdjust your computer\'s volume to a comfortable level before playing. This is the loudest sound you\'ll hear.')
        layout.add_widget(instr)
        
        play_btn = Button(text='🔊 Play Tone', size_hint_y=None, height=dp(50), on_press=self.play_tone)
        layout.add_widget(play_btn)
        
        set_btn = Button(text='Volume Set ✓', size_hint_y=None, height=dp(50), on_press=self.set_volume)
        layout.add_widget(set_btn)
        
        back_btn = Button(text='← Back', size_hint_y=None, height=dp(50), on_press=self.back)
        layout.add_widget(back_btn)
        
        self.add_widget(layout)
    
    def play_tone(self, instance):
        play_reference_tone()
    
    def set_volume(self, instance):
        App.get_running_app().root.current = 'instructions'
    
    def back(self, instance):
        App.get_running_app().root.current = 'device_check'

class InstructionsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        
        title = Label(text='📝 Test Instructions', size_hint_y=None, height=dp(50), font_size='20sp')
        layout.add_widget(title)
        
        scroll = ScrollView()
        instr_text = Label(text='Here\'s how it works: 🔍\n- Hear beeps in left/right ears 👂\n- Click YES if you hear a beep, NO if not\n- Some trials are silent (normal) ❓\n- If you click NO, you\'ll get up to 2 retries at the same level\n- Test adjusts to find your threshold 📉\n\nStay focused and respond quickly! ⚡\n\nClick YES or NO after the tone', text_size=(None, None), halign='left')
        scroll.add_widget(instr_text)
        layout.add_widget(scroll)
        
        start_btn = Button(text='🎵 Start Test', size_hint_y=None, height=dp(50), on_press=self.start_test)
        layout.add_widget(start_btn)
        
        back_btn = Button(text='← Back', size_hint_y=None, height=dp(50), on_press=self.back)
        layout.add_widget(back_btn)
        
        self.add_widget(layout)
    
    def start_test(self, instance):
        global test_sequence, current_test_index, total_tests
        thresholds['left'] = {}
        thresholds['right'] = {}
        test_sequence = []
        for freq in test_frequencies:
            for ear in ['left', 'right']:
                test_sequence.append({'freq': freq, 'ear': ear})
        current_test_index = 0
        total_tests = len(test_sequence)
        App.get_running_app().root.current = 'testing'
        Clock.schedule_once(lambda dt: run_next_threshold_test(), 0)
    
    def back(self, instance):
        App.get_running_app().root.current = 'calibration'

class TestingScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        
        self.progress = ProgressBar(max=100, value=0)
        self.ids['progress'] = self.progress
        layout.add_widget(self.progress)
        
        self.progress_label = Label(text='0%', size_hint_y=None, height=dp(30))
        self.ids['progress_label'] = self.progress_label
        layout.add_widget(self.progress_label)
        
        self.test_info = Label(text='Preparing test... ⚙️', size_hint_y=None, height=dp(30))
        self.ids['test_info'] = self.test_info
        layout.add_widget(self.test_info)
        
        self.ear_label = Label(text='', size_hint_y=None, height=dp(30))
        self.ids['ear_label'] = self.ear_label
        layout.add_widget(self.ear_label)
        
        self.status_label = Label(text='Frequency: ', size_hint_y=None, height=dp(30))
        self.ids['status_label'] = self.status_label
        layout.add_widget(self.status_label)
        
        self.response_status = Label(text='Listen carefully... 👂', size_hint_y=None, height=dp(30))
        self.ids['response_status'] = self.response_status
        layout.add_widget(self.response_status)
        
        btn_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50), spacing=dp(10))
        self.yes_btn = Button(text='YES, I heard it ✓', disabled=True)
        self.no_btn = Button(text='NO, I didn\'t hear it ❌', disabled=True)
        self.yes_btn.bind(on_press=self.yes_response)
        self.no_btn.bind(on_press=self.no_response)
        self.ids['yes_btn'] = self.yes_btn
        self.ids['no_btn'] = self.no_btn
        btn_layout.add_widget(self.yes_btn)
        btn_layout.add_widget(self.no_btn)
        layout.add_widget(btn_layout)
        
        self.add_widget(layout)
    
    def yes_response(self, instance):
        if current_test:
            current_test.on_response(True)
    
    def no_response(self, instance):
        if current_test:
            current_test.on_response(False)

def run_next_threshold_test(dt=None):
    if current_test_index >= total_tests:
        show_results_screen()
        return
    test = test_sequence[current_test_index]
    freq = test['freq']
    ear = test['ear']
    app = App.get_running_app()
    app.root.get_screen('testing').ids['response_status'].text = 'Listen carefully... 👂'
    progress = (current_test_index / total_tests) * 100
    app.root.get_screen('testing').ids['progress'].value = progress
    app.root.get_screen('testing').ids['progress_label'].text = f'{int(progress)}%'
    ear_symbol = '👂 Left' if ear == 'left' else '👂 Right'
    app.root.get_screen('testing').ids['ear_label'].text = f'{ear_symbol} Ear'
    app.root.get_screen('testing').ids['status_label'].text = f'Frequency: {freq} Hz 🎵'
    app.root.get_screen('testing').ids['test_info'].text = f'Test {current_test_index + 1}/{total_tests} ⚡'
    global current_test
    current_test = AdaptiveThresholdTest(freq, ear)
    current_test.start()

def on_threshold_complete(freq, ear, threshold):
    thresholds[ear][freq] = threshold
    global current_test_index
    current_test_index += 1
    Clock.schedule_once(run_next_threshold_test, 0.5)

class AdaptiveThresholdTest:
    def __init__(self, frequency, ear):
        self.frequency = frequency
        self.ear = ear
        self.current_level = -10
        self.step_size = step_size_large
        self.reversals = []
        self.responses = []
        self.trial_count = 0
        self.max_trials = 10
        self.last_direction = None
        self.catch_trial_probability = 0.03
        self.is_catch_trial = False
        self.waiting_for_response = False
        self.retry_attempts = 0

    def start(self):
        self.run_trial()

    def run_trial(self):
        if self.trial_count >= self.max_trials:
            self.complete_test()
            return
        self.trial_count += 1
        self.is_catch_trial = random.random() < self.catch_trial_probability
        app = App.get_running_app()
        app.root.get_screen('testing').ids['response_status'].text = 'Listen carefully... 👂'
        app.root.get_screen('testing').ids['yes_btn'].disabled = True
        app.root.get_screen('testing').ids['no_btn'].disabled = True
        Clock.schedule_once(lambda dt: self.present_stimulus(), 0)

    def present_stimulus(self):
        self.waiting_for_response = True
        app = App.get_running_app()
        if not self.is_catch_trial:
            play_test_tone(self.frequency, self.ear, self.current_level)
            Clock.schedule_once(lambda dt: self.response_ready(), 0.4)
        else:
            Clock.schedule_once(lambda dt: self.response_ready(), 0.3)

    def response_ready(self):
        app = App.get_running_app()
        app.root.get_screen('testing').ids['response_status'].text = 'Click YES or NO'
        app.root.get_screen('testing').ids['yes_btn'].disabled = False
        app.root.get_screen('testing').ids['no_btn'].disabled = False

    def on_response(self, heard):
        if not self.waiting_for_response:
            return
        self.waiting_for_response = False
        app = App.get_running_app()
        app.root.get_screen('testing').ids['yes_btn'].disabled = True
        app.root.get_screen('testing').ids['no_btn'].disabled = True

        status = app.root.get_screen('testing').ids['response_status']
        correct_response = not self.is_catch_trial
        self.responses.append({
            'level': self.current_level,
            'heard': heard,
            'catch_trial': self.is_catch_trial,
            'correct': heard == correct_response
        })

        if self.is_catch_trial:
            status.text = 'False alarm ❌' if heard else 'Good! (No tone) 👍'
            Clock.schedule_once(lambda dt: self.run_trial(), 1)
            return
        else:
            if heard:
                status.text = 'Heard ✓'
                on_threshold_complete(self.frequency, self.ear, self.current_level)
                return
            else:
                status.text = 'Not heard 🚫'

        self.retry_attempts += 1
        if self.retry_attempts < 3:
            status.text = f'Retry {self.retry_attempts}/2 - Listen carefully...'
            Clock.schedule_once(lambda dt: self.present_stimulus(), 1)
        else:
            status.text = 'Not heard after retries 🚫'
            self.update_level(False)
            Clock.schedule_once(lambda dt: self.run_trial(), 1)

    def update_level(self, heard):
        if heard:
            new_level = self.current_level - self.step_size
            if self.last_direction == 'up':
                self.reversals.append(self.current_level)
                if len(self.reversals) >= 1:
                    self.step_size = step_size_small
            self.last_direction = 'down'
        else:
            new_level = self.current_level + self.step_size
            if self.last_direction == 'down':
                self.reversals.append(self.current_level)
                if len(self.reversals) >= 1:
                    self.step_size = step_size_small
            self.last_direction = 'up'
        self.current_level = max(-60, min(0, new_level))

    def complete_test(self):
        valid_responses = [r for r in self.responses if not r['catch_trial']]
        if len(self.reversals) >= 2:
            threshold = sum(self.reversals[-2:]) / 2
        else:
            threshold_levels = []
            for i in range(1, len(valid_responses)):
                if valid_responses[i]['heard'] != valid_responses[i-1]['heard']:
                    threshold_levels.append(valid_responses[i]['level'])
            threshold = sum(threshold_levels) / len(threshold_levels) if threshold_levels else 0
        on_threshold_complete(self.frequency, self.ear, threshold)

def analyze_asymmetry():
    asymmetry_detected = False
    max_difference = 0
    differences = {}
    for freq in test_frequencies:
        if freq in thresholds['left'] and freq in thresholds['right']:
            diff = abs(thresholds['left'][freq] - thresholds['right'][freq])
            differences[freq] = diff
            max_difference = max(max_difference, diff)
            if diff >= 20:
                asymmetry_detected = True
    recommendation = f"Asymmetry detected (max difference: {max_difference:.1f} dB). ⚠️\nConsult an audiologist." if asymmetry_detected else f"No asymmetry detected (max: {max_difference:.1f} dB). ✅\nThis is a demo result."
    return {'asymmetry_detected': asymmetry_detected, 'max_difference': max_difference, 'recommendation': recommendation}

def show_results_screen():
    app = App.get_running_app()
    app.root.current = 'results'
    analysis = analyze_asymmetry()
    app.root.get_screen('results').ids['status_text'].text = '⚠️ Asymmetry Detected' if analysis['asymmetry_detected'] else '✅ No Asymmetry'
    app.root.get_screen('results').ids['recommendation'].text = analysis['recommendation']
    
    left_values = list(thresholds['left'].values())
    right_values = list(thresholds['right'].values())
    left_avg = sum(left_values) / len(left_values) if left_values else 0
    right_avg = sum(right_values) / len(right_values) if right_values else 0
    dissimilarity = analysis['max_difference']
    
    # Save to DB
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('UPDATE users SET left_avg=?, right_avg=?, dissimilarity=? WHERE id=?',
              (left_avg, right_avg, dissimilarity, user_id))
    conn.commit()
    conn.close()
    
    # Draw audiogram
    chart_widget = app.root.get_screen('results').ids['chart_widget']
    chart_widget.canvas.after.clear()
    with chart_widget.canvas.after:
        # Draw axes
        Color(0, 0, 0, 1)
        Line(points=[50, 50, 50, 350, 350, 350], width=2)  # x,y axes
        # Plot points (simplified)
        x_positions = [300, 250, 200, 150, 100]  # Approximate log scale
        y_base = 300
        # Left ear
        left_points = []
        for i, freq in enumerate(test_frequencies):
            left_y = y_base - (thresholds['left'].get(freq, 0) + 60) * 2
            left_points.extend([x_positions[i], left_y])
        Color(0.2, 0.6, 1, 1)  # Blue for left
        Line(points=left_points, width=2)
        # Right ear
        right_points = []
        for i, freq in enumerate(test_frequencies):
            right_y = y_base - (thresholds['right'].get(freq, 0) + 60) * 2
            right_points.extend([x_positions[i], right_y])
        Color(1, 0.3, 0.3, 1)  # Red for right
        Line(points=right_points, width=2)

class ResultsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        
        self.status_text = Label(text='', size_hint_y=None, height=dp(50), font_size='20sp')
        self.ids['status_text'] = self.status_text
        layout.add_widget(self.status_text)
        
        self.recommendation = Label(text='', halign='center', valign='middle', text_size=(None, None))
        self.ids['recommendation'] = self.recommendation
        layout.add_widget(self.recommendation)
        
        self.chart_widget = Widget()  # Use Widget for canvas drawing
        self.ids['chart_widget'] = self.chart_widget
        layout.add_widget(self.chart_widget)
        
        btn_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50), spacing=dp(10))
        try_again_btn = Button(text='🔄 Try Again', on_press=self.try_again)
        exit_btn = Button(text='Exit ❌', on_press=self.exit_app)
        btn_layout.add_widget(try_again_btn)
        btn_layout.add_widget(exit_btn)
        layout.add_widget(btn_layout)
        
        self.add_widget(layout)
    
    def try_again(self, instance):
        global thresholds, current_test
        thresholds = {'left': {}, 'right': {}}
        current_test = None
        App.get_running_app().root.current = 'welcome'
    
    def exit_app(self, instance):
        App.get_running_app().stop()

# Main App
class HearingTestApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(WelcomeScreen(name='welcome'))
        sm.add_widget(ConsentScreen(name='consent'))
        sm.add_widget(DeviceCheckScreen(name='device_check'))
        sm.add_widget(CalibrationScreen(name='calibration'))
        sm.add_widget(InstructionsScreen(name='instructions'))
        sm.add_widget(TestingScreen(name='testing'))
        sm.add_widget(ResultsScreen(name='results'))
        return sm

if __name__ == '__main__':
    HearingTestApp().run()