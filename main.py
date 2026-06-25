import sys
import os
import random
import time
from enum import Enum
from pathlib import Path
from datetime import datetime

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QSlider, QListWidget, QFileDialog, QTabWidget,
    QFrame, QGridLayout, QStyle, QComboBox, QMessageBox
)
from PyQt6.QtCore import (
    Qt, QTimer, QSize, QPoint, pyqtSignal, QThread
)
from PyQt6.QtGui import (
    QPainter, QColor, QFont, QPen, QBrush, QPainterPath,
    QRadialGradient, QLinearGradient, QPixmap, QIcon
)

import pygame
from pygame import mixer
from mutagen.mp3 import MP3
from mutagen.wave import WAVE
from effects import SoundEffects


class Theme(Enum):
    CLASSIC = "Retrô Clássico"
    NEON = "Futurista Neon"
    DARK = "Dark Mode"


class VUMeter(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(200, 60)
        self.left_level = 0
        self.right_level = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_levels)
        self.timer.start(50)

    def update_levels(self):
        if hasattr(self, 'window') and hasattr(self.window(), 'audio_engine'):
            if self.window().audio_engine.is_playing:
                self.left_level = min(1.0, self.left_level + random.uniform(0.1, 0.3))
                self.right_level = min(1.0, self.right_level + random.uniform(0.1, 0.3))
            else:
                self.left_level = max(0, self.left_level - 0.15)
                self.right_level = max(0, self.right_level - 0.15)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        
        if hasattr(self.window(), 'current_theme'):
            theme = self.window().current_theme
            if theme == Theme.CLASSIC:
                colors = [QColor(0, 255, 0), QColor(255, 255, 0), QColor(255, 0, 0)]
            elif theme == Theme.NEON:
                colors = [QColor(0, 255, 255), QColor(255, 0, 255), QColor(255, 255, 0)]
            else:
                colors = [QColor(100, 100, 255), QColor(255, 100, 100), QColor(100, 255, 100)]
        else:
            colors = [QColor(0, 255, 0), QColor(255, 255, 0), QColor(255, 0, 0)]

        bar_width = w // 2 - 20
        bar_height = h - 20
        
        for channel, level in enumerate([self.left_level, self.right_level]):
            x = 10 + channel * (w // 2)
            y = 10
            segments = 12
            
            for i in range(segments):
                segment_height = bar_height // segments
                fill_ratio = level
                if i < int(segments * fill_ratio):
                    if i < segments * 0.7:
                        color = colors[0]
                    elif i < segments * 0.9:
                        color = colors[1]
                    else:
                        color = colors[2]
                    rect_x = int(x)
                    rect_y = int(y + bar_height - (i + 1) * segment_height)
                    rect_w = int(bar_width - 10)
                    rect_h = int(segment_height - 2)
                    painter.fillRect(rect_x, rect_y, rect_w, rect_h, color)
        
        painter.setPen(QColor(255, 255, 255, 100))
        painter.drawText(10, h - 5, "L")
        painter.drawText(w // 2 + 10, h - 5, "R")


class TapeWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(300, 200)
        self.reel1_angle = 0
        self.reel2_angle = 0
        self.is_playing = False
        self.is_rewinding = False
        self.is_forwarding = False
        self.tape_inserted = False
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.rotate_reels)
        self.timer.start(30)

    def rotate_reels(self):
        if self.is_playing:
            self.reel1_angle += 3
            self.reel2_angle -= 2.5
        elif self.is_rewinding:
            self.reel1_angle -= 8
            self.reel2_angle += 7
        elif self.is_forwarding:
            self.reel1_angle += 8
            self.reel2_angle -= 7
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w // 2, h // 2

        if hasattr(self.window(), 'current_theme'):
            theme = self.window().current_theme
            if theme == Theme.CLASSIC:
                body_color = QColor(25, 25, 25)
                tape_color = QColor(40, 40, 40)
                reel_color = QColor(180, 180, 180)
                label_color = QColor(200, 200, 200)
            elif theme == Theme.NEON:
                body_color = QColor(10, 10, 30)
                tape_color = QColor(20, 20, 50)
                reel_color = QColor(0, 255, 255)
                label_color = QColor(255, 0, 255)
            else:
                body_color = QColor(20, 20, 20)
                tape_color = QColor(35, 35, 35)
                reel_color = QColor(80, 80, 80)
                label_color = QColor(150, 150, 150)
        else:
            body_color = QColor(25, 25, 25)
            tape_color = QColor(40, 40, 40)
            reel_color = QColor(180, 180, 180)
            label_color = QColor(200, 200, 200)

        if not self.tape_inserted:
            painter.setPen(QColor(100, 100, 100))
            painter.setFont(QFont("Arial", 12))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Insira uma fita!")
            return

        body_rect = QFrame.rect(self)
        body_path = QPainterPath()
        body_path.addRoundedRect(20, 20, w - 40, h - 40, 15, 15)
        painter.fillPath(body_path, body_color)
        
        painter.setPen(QPen(QColor(50, 50, 50), 3))
        painter.drawPath(body_path)

        window_rect = QFrame.rect(self).adjusted(50, 50, -50, -50)
        painter.fillRect(window_rect, tape_color)
        
        painter.fillRect(cx - 30, 40, 60, h - 80, label_color)

        self.draw_reel(painter, cx - 60, cy, 40, 12, self.reel1_angle, reel_color)
        self.draw_reel(painter, cx + 60, cy, 40, 12, self.reel2_angle, reel_color)

        painter.setPen(QColor(100, 100, 100))
        for i in range(5):
            x = 30 + i * 60
            painter.drawEllipse(QPoint(x, 30), 5, 5)
            painter.drawEllipse(QPoint(x, h - 30), 5, 5)

    def draw_reel(self, painter, x, y, radius, inner_radius, angle, color):
        painter.save()
        painter.translate(x, y)
        painter.rotate(angle)
        
        gradient = QRadialGradient(0, 0, radius)
        gradient.setColorAt(0, color.lighter(150))
        gradient.setColorAt(1, color.darker(150))
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(QColor(50, 50, 50), 2))
        painter.drawEllipse(QPoint(0, 0), radius, radius)
        
        painter.setBrush(QBrush(QColor(30, 30, 30)))
        painter.drawEllipse(QPoint(0, 0), inner_radius, inner_radius)
        
        painter.setPen(QPen(QColor(100, 100, 100), 2))
        for i in range(6):
            painter.save()
            painter.rotate(i * 60)
            painter.drawLine(inner_radius + 5, 0, radius - 5, 0)
            painter.restore()
        
        painter.restore()


class ButtonStyle(QPushButton):
    def __init__(self, text, parent=None, sound_type='click'):
        super().__init__(text, parent)
        self.setFixedSize(60, 60)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.sound_type = sound_type
        self.pressed.connect(self.play_sound)

    def play_sound(self):
        if hasattr(self.window(), 'sound_effects'):
            try:
                self.window().sound_effects.play(self.sound_type)
            except Exception as e:
                print(f"Sound error: {e}")


class AudioEngine:
    def __init__(self):
        pygame.init()
        mixer.init()
        self.current_file = None
        self.is_playing = False
        self.is_paused = False
        self.volume = 0.7
        self.position = 0.0  # Posição atual em segundos
        self.duration = 0.0  # Duração total em segundos
        self.start_time = 0.0  # Timestamp de início da reprodução
        self.paused_time = 0.0  # Timestamp de quando foi pausado

    def load(self, file_path):
        try:
            self.current_file = file_path
            mixer.music.load(file_path)
            
            if file_path.endswith('.mp3'):
                audio = MP3(file_path)
                self.duration = audio.info.length
            elif file_path.endswith('.wav'):
                audio = WAVE(file_path)
                self.duration = audio.info.length
                
            self.position = 0.0
            self.is_playing = False
            self.is_paused = False
            return True
        except Exception as e:
            print(f"Error loading file: {e}")
            return False

    def play(self):
        if self.current_file:
            if self.is_paused:
                self.resume()
            else:
                mixer.music.play()
                self.start_time = time.time()
                self.position = 0.0
                self.is_playing = True
                self.is_paused = False

    def pause(self):
        if self.is_playing:
            mixer.music.pause()
            self.paused_time = time.time()
            # Atualiza a posição com o tempo decorrido até o pause
            self.position = self.position + (self.paused_time - self.start_time)
            self.is_paused = True
            self.is_playing = False

    def resume(self):
        if self.is_paused:
            mixer.music.unpause()
            self.start_time = time.time()  # Reinicia o contador
            self.is_paused = False
            self.is_playing = True

    def stop(self):
        mixer.music.stop()
        self.is_playing = False
        self.is_paused = False
        self.position = 0.0

    def set_volume(self, volume):
        self.volume = volume / 100
        mixer.music.set_volume(self.volume)

    def get_position(self):
        """
        Retorna a posição atual em segundos usando tracking manual com time.time()
        Esta é a solução profissional e confiável
        """
        if self.is_playing:
            # Calcula o tempo decorrido desde o início (ou último resume)
            current_time = time.time()
            elapsed = current_time - self.start_time
            total_position = self.position + elapsed
            
            # Garante que não ultrapasse a duração
            if total_position >= self.duration:
                return self.duration
            return total_position
        elif self.is_paused:
            return self.position
        else:
            return 0.0

    def seek(self, position_seconds):
        """
        Avança ou retrocede para uma posição específica (em segundos)
        """
        if self.current_file:
            position_seconds = max(0, min(position_seconds, self.duration))
            mixer.music.play(start=position_seconds)
            self.position = position_seconds
            self.start_time = time.time()
            self.is_playing = True
            self.is_paused = False


class CassettePlayer(QWidget):
    def __init__(self):
        super().__init__()
        self.current_theme = Theme.CLASSIC
        self.audio_engine = AudioEngine()
        self.playlist = []
        self.history = []
        self.current_index = -1
        self.shuffle_mode = False
        self.repeat_mode = False
        self.wear_effect = False
        self.sound_effects = SoundEffects()
        
        self.init_ui()
        self.apply_theme()
        
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_progress)
        self.update_timer.start(100)
        
        self.wear_timer = QTimer()
        self.wear_timer.timeout.connect(self.play_wear_effect)
        self.wear_timer.start(500)

    def init_ui(self):
        self.setWindowTitle("Toca-Fitas Retrô")
        self.resize(800, 700)
        
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)

        title_label = QLabel("TOCA-FITAS")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setFont(QFont("Courier New", 24, QFont.Weight.Bold))
        main_layout.addWidget(title_label)

        theme_layout = QHBoxLayout()
        theme_label = QLabel("Tema:")
        theme_label.setFont(QFont("Arial", 10))
        self.theme_combo = QComboBox()
        for theme in Theme:
            self.theme_combo.addItem(theme.value, theme)
        self.theme_combo.currentIndexChanged.connect(self.change_theme)
        theme_layout.addWidget(theme_label)
        theme_layout.addWidget(self.theme_combo)
        theme_layout.addStretch()
        main_layout.addLayout(theme_layout)

        self.tape_widget = TapeWidget(self)
        main_layout.addWidget(self.tape_widget, 1)

        self.track_info = QLabel("Nenhuma fita inserida")
        self.track_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.track_info.setFont(QFont("Courier New", 14))
        main_layout.addWidget(self.track_info)

        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_label.setFont(QFont("Courier New", 12))
        main_layout.addWidget(self.time_label)

        self.progress_slider = QSlider(Qt.Orientation.Horizontal)
        self.progress_slider.setRange(0, 1000)
        self.progress_slider.sliderPressed.connect(self.slider_pressed)
        self.progress_slider.sliderReleased.connect(self.slider_released)
        main_layout.addWidget(self.progress_slider)

        self.vu_meter = VUMeter(self)
        main_layout.addWidget(self.vu_meter)

        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(15)
        controls_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.btn_rewind = ButtonStyle("⏪")
        self.btn_rewind.clicked.connect(self.rewind)
        self.btn_play = ButtonStyle("▶️")
        self.btn_play.clicked.connect(self.toggle_play)
        self.btn_pause = ButtonStyle("⏸")
        self.btn_pause.clicked.connect(self.toggle_pause)
        self.btn_stop = ButtonStyle("⏹")
        self.btn_stop.clicked.connect(self.stop)
        self.btn_forward = ButtonStyle("⏩")
        self.btn_forward.clicked.connect(self.forward)
        self.btn_eject = ButtonStyle("⏏")
        self.btn_eject.clicked.connect(self.eject)

        controls_layout.addWidget(self.btn_rewind)
        controls_layout.addWidget(self.btn_play)
        controls_layout.addWidget(self.btn_pause)
        controls_layout.addWidget(self.btn_stop)
        controls_layout.addWidget(self.btn_forward)
        controls_layout.addWidget(self.btn_eject)

        main_layout.addLayout(controls_layout)

        volume_layout = QHBoxLayout()
        volume_label = QLabel("Volume:")
        volume_label.setFont(QFont("Arial", 10))
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(70)
        self.volume_slider.valueChanged.connect(self.change_volume)
        volume_layout.addWidget(volume_label)
        volume_layout.addWidget(self.volume_slider)
        main_layout.addLayout(volume_layout)

        extra_layout = QHBoxLayout()
        self.btn_shuffle = ButtonStyle("🔀")
        self.btn_shuffle.setCheckable(True)
        self.btn_shuffle.clicked.connect(self.toggle_shuffle)
        self.btn_repeat = ButtonStyle("🔁")
        self.btn_repeat.setCheckable(True)
        self.btn_repeat.clicked.connect(self.toggle_repeat)
        self.btn_wear = ButtonStyle("📼")
        self.btn_wear.setCheckable(True)
        self.btn_wear.clicked.connect(self.toggle_wear)
        extra_layout.addWidget(self.btn_shuffle)
        extra_layout.addWidget(self.btn_repeat)
        extra_layout.addWidget(self.btn_wear)
        extra_layout.addStretch()
        main_layout.addLayout(extra_layout)

        tabs = QTabWidget()
        
        playlist_tab = QWidget()
        playlist_layout = QVBoxLayout()
        self.playlist_widget = QListWidget()
        playlist_layout.addWidget(QLabel("Playlist:"))
        playlist_layout.addWidget(self.playlist_widget)
        add_btn = QPushButton("Adicionar Música")
        add_btn.clicked.connect(self.add_to_playlist)
        playlist_layout.addWidget(add_btn)
        playlist_tab.setLayout(playlist_layout)
        
        history_tab = QWidget()
        history_layout = QVBoxLayout()
        self.history_widget = QListWidget()
        history_layout.addWidget(QLabel("Histórico:"))
        history_layout.addWidget(self.history_widget)
        history_tab.setLayout(history_layout)
        
        tabs.addTab(playlist_tab, "Playlist")
        tabs.addTab(history_tab, "Histórico")
        main_layout.addWidget(tabs)

        self.setLayout(main_layout)

    def apply_theme(self):
        if self.current_theme == Theme.CLASSIC:
            bg_color = "#2d2d2d"
            text_color = "#f0f0f0"
            button_color = "#555555"
            button_hover = "#777777"
        elif self.current_theme == Theme.NEON:
            bg_color = "#0a0a1a"
            text_color = "#00ffff"
            button_color = "#1a1a3a"
            button_hover = "#2a2a5a"
        else:
            bg_color = "#1a1a1a"
            text_color = "#e0e0e0"
            button_color = "#333333"
            button_hover = "#444444"

        self.setStyleSheet(f"""
            QWidget {{
                background-color: {bg_color};
                color: {text_color};
                font-family: 'Courier New', monospace;
            }}
            QPushButton {{
                background-color: {button_color};
                border: 3px solid #666;
                border-radius: 30px;
                font-size: 20px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {button_hover};
            }}
            QPushButton:pressed {{
                background-color: #333;
                border: 3px solid #444;
            }}
            QPushButton:checked {{
                background-color: #4a4;
                border: 3px solid #2a2;
            }}
            QSlider::groove:horizontal {{
                height: 8px;
                background: #444;
                border-radius: 4px;
            }}
            QSlider::handle:horizontal {{
                width: 20px;
                background: #888;
                border-radius: 10px;
                margin: -6px 0;
            }}
            QListWidget {{
                border: 2px solid #444;
                border-radius: 8px;
                padding: 5px;
            }}
            QComboBox {{
                background-color: {button_color};
                border: 2px solid #666;
                border-radius: 5px;
                padding: 5px;
            }}
        """)

    def change_theme(self, index):
        self.current_theme = self.theme_combo.itemData(index)
        self.apply_theme()

    def eject(self):
        if self.tape_widget.tape_inserted:
            self.sound_effects.play('eject')
            self.tape_widget.tape_inserted = False
            self.stop()
            self.track_info.setText("Fita ejetada")
        else:
            file, _ = QFileDialog.getOpenFileName(
                self,
                "Escolha uma música",
                "",
                "Arquivos de Áudio (*.mp3 *.wav)"
            )
            if file:
                self.sound_effects.play('eject')
                self.load_track(file)

    def play_wear_effect(self):
        if self.wear_effect and self.audio_engine.is_playing:
            if random.random() < 0.3:
                self.sound_effects.play('wear')

    def load_track(self, file_path):
        if self.audio_engine.load(file_path):
            self.tape_widget.tape_inserted = True
            self.track_info.setText(Path(file_path).stem)
            if file_path not in self.playlist:
                self.playlist.append(file_path)
                self.playlist_widget.addItem(Path(file_path).name)
            self.history.append(file_path)
            self.history_widget.addItem(Path(file_path).name)
            self.current_index = len(self.playlist) - 1

    def toggle_play(self):
        if not self.tape_widget.tape_inserted:
            return
        if self.audio_engine.is_paused:
            self.audio_engine.resume()
        else:
            self.audio_engine.play()
        self.tape_widget.is_playing = True
        self.tape_widget.is_rewinding = False
        self.tape_widget.is_forwarding = False

    def toggle_pause(self):
        if self.audio_engine.is_playing:
            self.audio_engine.pause()
            self.tape_widget.is_playing = False
        elif self.audio_engine.is_paused:
            self.audio_engine.resume()
            self.tape_widget.is_playing = True

    def stop(self):
        self.audio_engine.stop()
        self.tape_widget.is_playing = False
        self.tape_widget.is_rewinding = False
        self.tape_widget.is_forwarding = False
        self.progress_slider.setValue(0)

    def rewind(self):
        self.tape_widget.is_rewinding = True
        self.tape_widget.is_playing = False
        self.tape_widget.is_forwarding = False
        QTimer.singleShot(2000, lambda: setattr(self.tape_widget, 'is_rewinding', False))

    def forward(self):
        self.tape_widget.is_forwarding = True
        self.tape_widget.is_playing = False
        self.tape_widget.is_rewinding = False
        QTimer.singleShot(2000, lambda: setattr(self.tape_widget, 'is_forwarding', False))

    def change_volume(self, value):
        self.audio_engine.set_volume(value)

    def toggle_shuffle(self):
        self.shuffle_mode = self.btn_shuffle.isChecked()

    def toggle_repeat(self):
        self.repeat_mode = self.btn_repeat.isChecked()

    def toggle_wear(self):
        self.wear_effect = self.btn_wear.isChecked()

    def slider_pressed(self):
        self.slider_held = True

    def slider_released(self):
        self.slider_held = False
        # Quando o usuário soltar o slider, move a música para a posição
        if self.audio_engine.current_file and self.audio_engine.duration > 0:
            slider_value = self.progress_slider.value()
            target_position = (slider_value / 1000) * self.audio_engine.duration
            self.audio_engine.seek(target_position)

    def update_progress(self):
        if hasattr(self, 'audio_engine'):
            # Verifica se a música terminou de tocar
            if self.audio_engine.is_playing and self.audio_engine.duration > 0:
                current_pos = self.audio_engine.get_position()
                
                # Se a posição atual for maior ou igual à duração, a música terminou
                if current_pos >= self.audio_engine.duration - 0.1:
                    self.stop()
                    return
            
            # Atualiza o slider e o tempo apenas se não estivermos arrastando o slider
            if not hasattr(self, 'slider_held') or not self.slider_held:
                pos = self.audio_engine.get_position()
                
                if self.audio_engine.duration > 0:
                    progress = (pos / self.audio_engine.duration) * 1000
                    self.progress_slider.setValue(int(progress))
                
                current = self.format_time(pos)
                total = self.format_time(self.audio_engine.duration)
                self.time_label.setText(f"{current} / {total}")

    def format_time(self, seconds):
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins:02d}:{secs:02d}"

    def add_to_playlist(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Adicionar músicas à playlist",
            "",
            "Arquivos de Áudio (*.mp3 *.wav)"
        )
        for file in files:
            if file not in self.playlist:
                self.playlist.append(file)
                self.playlist_widget.addItem(Path(file).name)


def main():
    app = QApplication(sys.argv)
    player = CassettePlayer()
    player.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
