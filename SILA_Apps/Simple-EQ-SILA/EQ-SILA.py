import sys
import sounddevice as sd
import numpy as np
import scipy.signal as signal
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QSlider, QFileDialog, QWidget, QProgressBar, QMenuBar, QAction
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QColor, QFont, QIcon
from pydub import AudioSegment
import wave
import traceback


class RealTimeEqualizer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simple EQSILA")
        self.setGeometry(100, 100, 700, 400)
        self.audio_data = None
        self.sampling_rate = 44100
        self.stream = None
        self.band_gains = np.zeros(10)
        self.volume = 1.0
        self.filters = []
        self.play_position = 0
        self.init_filters()
        self.init_ui()

    def init_ui(self):
        # Configuración de tema oscuro
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(26, 26, 26))
        palette.setColor(QPalette.WindowText, QColor(230, 230, 230))
        self.setPalette(palette)

        font = QFont('Arial', 10)
        self.setFont(font)

        central_widget = QWidget()
        main_layout = QVBoxLayout()

        # Menú de presets
        menu_bar = QMenuBar(self)
        preset_menu = menu_bar.addMenu("Presets")
        presets = {
            "Cut Bass": lambda: self.apply_preset([-10, -10, -5, 0, 0, 0, 0, 0, 0, 0]),
            "Cut Treble": lambda: self.apply_preset([0, 0, 0, 0, 0, 0, 0, -5, -10, -10]),
            "Boost Bass": lambda: self.apply_preset([5, 5, 5, 0, 0, 0, 0, 0, 0, 0]),
            "Boost Treble": lambda: self.apply_preset([0, 0, 0, 0, 0, 0, 5, 5, 5, 5]),
            "RIAA": lambda: self.apply_preset([-5, -5, -3, 0, 3, 5, 5, 5, 3, 0]),
            "Flat": lambda: self.apply_preset([0] * 10),
        }
        for preset_name, preset_action in presets.items():
            action = QAction(preset_name, self)
            action.triggered.connect(preset_action)
            preset_menu.addAction(action)
        self.setMenuBar(menu_bar)

        # Botones
        btn_layout = QHBoxLayout()
        self.load_btn = self.create_button("Load Audio", "icons/load.png", self.load_audio)
        self.play_btn = self.create_button("Play", "icons/play.png", self.play_audio, "#4CAF50")
        self.stop_btn = self.create_button("Stop", "icons/stop.png", self.stop_audio, "#F44336")
        self.export_btn = self.create_button("Export Audio", "icons/export.png", self.export_audio, "#2196F3")
        for btn in (self.load_btn, self.play_btn, self.stop_btn, self.export_btn):
            btn_layout.addWidget(btn)
        main_layout.addLayout(btn_layout)

        # Deslizadores para bandas de frecuencia
        sliders_layout = QHBoxLayout()
        self.sliders = []
        band_labels = [
            "31 Hz", "62 Hz", "125 Hz", "250 Hz", "500 Hz",
            "1 kHz", "2 kHz", "4 kHz", "8 kHz", "16 kHz"
        ]
        for label_text in band_labels:
            slider_layout = QVBoxLayout()
            label = QLabel(label_text)
            label.setStyleSheet("color: #B0B0B0; font-weight: bold;")
            label.setAlignment(Qt.AlignCenter)
            slider = QSlider(Qt.Vertical)
            slider.setRange(-10, 10)
            slider.setValue(0)
            slider.valueChanged.connect(self.update_band_gains)
            self.sliders.append(slider)
            slider_layout.addWidget(label)
            slider_layout.addWidget(slider)
            sliders_layout.addLayout(slider_layout)
        main_layout.addLayout(sliders_layout)

        # Volumen maestro
        self.master_vol_slider = QSlider(Qt.Horizontal)
        self.master_vol_slider.setRange(0, 100)
        self.master_vol_slider.setValue(100)
        self.master_vol_slider.valueChanged.connect(self.update_volume)
        main_layout.addWidget(QLabel("Master Volume"))
        main_layout.addWidget(self.master_vol_slider)

        # Indicador de distorsión
        self.distortion_indicator = QLabel("Distortion: None")
        self.distortion_indicator.setStyleSheet("color: #4CAF50; font-weight: bold;")
        main_layout.addWidget(self.distortion_indicator)

        # Barra de progreso
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        main_layout.addWidget(self.progress_bar)

        # Etiqueta de información
        self.info_label = QLabel("Ready to load audio.")
        self.info_label.setStyleSheet("color: #FFFFFF; font-size: 14px; font-weight: bold;")
        main_layout.addWidget(self.info_label)

        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def create_button(self, text, icon, action, color=None):
        btn = QPushButton(text)
        btn.setIcon(QIcon(icon))
        btn.setStyleSheet(f"background-color: {color if color else '#2A2A2A'}; color: white; border-radius: 5px; padding: 10px;")
        btn.clicked.connect(action)
        return btn

    def init_filters(self):
        bands = [
            (20, 60), (60, 120), (120, 250), (250, 500),
            (500, 1000), (1000, 2000), (2000, 4000), (4000, 8000),
            (8000, 16000), (16000, 20000)
        ]
        self.filters = []
        for low, high in bands:
            sos = signal.butter(2, [low / (self.sampling_rate / 2), high / (self.sampling_rate / 2)],
                                btype='band', output='sos')
            self.filters.append(sos)

    def load_audio(self):
        try:
            file_dialog = QFileDialog.getOpenFileName(
                self, "Select Audio File", "", "Audio Files (*.mp3 *.wav *.flac)"
            )
            if file_dialog[0]:
                audio_file = AudioSegment.from_file(file_dialog[0])
                audio_file = audio_file.set_channels(1).set_frame_rate(self.sampling_rate)
                self.audio_data = np.array(audio_file.get_array_of_samples(), dtype=np.float32) / (2 ** 15)
                self.sampling_rate = audio_file.frame_rate

                if self.audio_data is not None:
                    self.info_label.setText(f"Loaded audio: {file_dialog[0].split('/')[-1]}")
                    self.statusBar().showMessage("Audio loaded successfully!")
                else:
                    self.statusBar().showMessage("Failed to load audio.")
        except Exception as e:
            self.statusBar().showMessage(f"Error loading audio: {str(e)}")

    def update_band_gains(self):
        self.band_gains = np.array([slider.value() for slider in self.sliders])
        self.statusBar().showMessage(f"Band gains updated: {self.band_gains}")

    def update_volume(self):
        self.volume = self.master_vol_slider.value() / 100.0
        self.statusBar().showMessage(f"Master Volume: {self.volume * 100:.0f}%")
        self.info_label.setText(f"Master Volume: {self.volume * 100:.0f}%")

    def apply_preset(self, gains):
        for i, gain in enumerate(gains):
            self.sliders[i].setValue(gain)

    def check_distortion(self):
        if self.audio_data is not None and (np.any(self.audio_data > 1.0) or np.any(self.audio_data < -1.0)):
            self.distortion_indicator.setText("Distortion: Yes")
            self.distortion_indicator.setStyleSheet("color: #F44336; font-weight: bold;")
        else:
            self.distortion_indicator.setText("Distortion: No")
            self.distortion_indicator.setStyleSheet("color: #4CAF50; font-weight: bold;")

    def play_audio(self):
        try:
            if self.audio_data is None:
                self.statusBar().showMessage("No audio loaded.")
                return
            
            def callback(outdata, frames, time, status):
                if status:
                    print(f"Status: {status}", file=sys.stderr)
                start = int(self.play_position * self.sampling_rate)
                end = start + frames
                chunk = self.audio_data[start:end]
                if len(chunk) < frames:
                    outdata[:len(chunk)] = chunk.reshape(-1, 1)
                    outdata[len(chunk):] = 0
                    self.stop_audio()
                else:
                    outdata[:] = chunk.reshape(-1, 1)

                # Apply equalizer
                for i, sos in enumerate(self.filters):
                    chunk = signal.sosfilt(sos, chunk) * (10 ** (self.band_gains[i] / 20))
                chunk *= self.volume
                self.check_distortion()
                self.play_position += frames / self.sampling_rate

            self.play_position = 0
            self.stream = sd.OutputStream(
                samplerate=self.sampling_rate,
                channels=1,
                callback=callback
            )
            self.stream.start()
            self.statusBar().showMessage("Playing audio...")
            self.info_label.setText("Playing audio...")
        except Exception as e:
            self.statusBar().showMessage(f"Error playing audio: {str(e)}")
            traceback.print_exc()


    def stop_audio(self):
        if self.stream and self.stream.active:
            self.stream.stop()
        self.statusBar().showMessage("Audio stopped.")
        self.info_label.setText("Audio stopped.")

    def export_audio(self):
        if self.audio_data is None:
            self.info_label.setText("No audio loaded to export.")
            return

        try:
            file_dialog = QFileDialog.getSaveFileName(
                self, "Save Processed Audio", "", "WAV Files (*.wav)"
            )
            if not file_dialog[0]:
                return  # Usuario canceló la operación

            # Aplicar los filtros a la señal
            processed_audio = self.audio_data.copy()
            for i, sos in enumerate(self.filters):
                gain = 10 ** (self.band_gains[i] / 20)  # Convertir de dB a escala lineal
                processed_audio = signal.sosfilt(sos, processed_audio) * gain

            # Ajustar el volumen maestro
            processed_audio *= self.volume

            # Escalar los datos para que estén en el rango adecuado para WAV
            max_amplitude = np.max(np.abs(processed_audio))
            if max_amplitude > 0:
                processed_audio = processed_audio / max_amplitude  # Normalizar
            processed_audio = (processed_audio * 32767).astype(np.int16)  # Convertir a 16 bits

            # Guardar el archivo WAV
            with wave.open(file_dialog[0], 'w') as wav_file:
                wav_file.setnchannels(1)  # Canal mono
                wav_file.setsampwidth(2)  # 16 bits
                wav_file.setframerate(self.sampling_rate)
                wav_file.writeframes(processed_audio.tobytes())

            self.info_label.setText(f"Audio exported successfully: {file_dialog[0].split('/')[-1]}")
            self.statusBar().showMessage("Audio exported successfully!")
        except Exception as e:
            self.info_label.setText(f"Error exporting audio: {str(e)}")
            self.statusBar().showMessage(f"Error exporting audio: {traceback.format_exc()}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    eq = RealTimeEqualizer()
    eq.show()
    sys.exit(app.exec_())