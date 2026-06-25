import pygame
from pygame import mixer
import struct
from io import BytesIO
import random


class SoundEffects:
    def __init__(self):
        pygame.init()
        mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        self.sounds = {}
        self.generate_all_sounds()

    def generate_click_sound(self, frequency=800, duration=0.05, volume=0.3):
        sample_rate = 44100
        num_samples = int(sample_rate * duration)
        samples = []
        
        for i in range(num_samples):
            t = i / sample_rate
            fade = 1.0 - (t / duration)
            value = int(32767 * volume * fade * (0.5 + 0.5 * random.uniform(-1, 1)))
            samples.append(struct.pack('<h', value))
        
        wav_header = self.create_wav_header(len(samples) * 2, sample_rate)
        temp_file = BytesIO(wav_header + b''.join(samples))
        
        with open('click.wav', 'wb') as f:
            f.write(temp_file.getvalue())
        
        return mixer.Sound('click.wav')

    def generate_eject_sound(self):
        sample_rate = 44100
        duration = 0.3
        num_samples = int(sample_rate * duration)
        samples = []
        
        for i in range(num_samples):
            t = i / sample_rate
            frequency = 400 + 200 * (1 - t/duration)
            fade = 1.0 - (t / duration)
            value = int(32767 * 0.4 * fade * (0.5 + 0.5 * random.uniform(-1, 1)))
            samples.append(struct.pack('<h', value))
        
        wav_header = self.create_wav_header(len(samples) * 2, sample_rate)
        
        with open('eject.wav', 'wb') as f:
            f.write(wav_header + b''.join(samples))
        
        return mixer.Sound('eject.wav')

    def generate_tape_wear_sound(self):
        sample_rate = 44100
        duration = 0.01
        num_samples = int(sample_rate * duration)
        samples = []
        
        for _ in range(num_samples):
            value = int(32767 * 0.02 * random.uniform(-1, 1))
            samples.append(struct.pack('<h', value))
        
        wav_header = self.create_wav_header(len(samples) * 2, sample_rate)
        
        with open('wear.wav', 'wb') as f:
            f.write(wav_header + b''.join(samples))
        
        return mixer.Sound('wear.wav')

    def generate_reel_motor_sound(self):
        sample_rate = 44100
        duration = 0.5
        num_samples = int(sample_rate * duration)
        samples = []
        
        for i in range(num_samples):
            t = i / sample_rate
            value = int(32767 * 0.1 * (0.5 + 0.5 * (t / duration)) * random.uniform(-0.5, 0.5))
            samples.append(struct.pack('<h', value))
        
        wav_header = self.create_wav_header(len(samples) * 2, sample_rate)
        
        with open('motor.wav', 'wb') as f:
            f.write(wav_header + b''.join(samples))
        
        return mixer.Sound('motor.wav')

    def create_wav_header(self, data_size, sample_rate):
        return struct.pack(
            '<4sI4s4sIHHIIHH4sI',
            b'RIFF', 36 + data_size, b'WAVE',
            b'fmt ', 16, 1, 2, sample_rate, sample_rate * 2, 2, 16,
            b'data', data_size
        )

    def generate_all_sounds(self):
        self.sounds['click'] = self.generate_click_sound()
        self.sounds['click2'] = self.generate_click_sound(frequency=600, duration=0.04)
        self.sounds['eject'] = self.generate_eject_sound()
        self.sounds['wear'] = self.generate_tape_wear_sound()
        self.sounds['motor'] = self.generate_reel_motor_sound()

    def play(self, sound_name):
        if sound_name in self.sounds:
            self.sounds[sound_name].play()
