"""App Launcher Module - Lists and launches apps from /app directory"""

import os
import gc  # Importar o Garbage Collector
import time
import tft_config as tft
import st7789py as st7789
from romfonts import vga1_8x8 as font
from lib.app_runner import run_app  # Importa o novo runner
from lib.touch import Touch
from lib.trackball import Trackball
from lib.sound import SoundManager

class AppLauncher:
    def __init__(self, display, touch, trackball, i2c, sound):
        self.display = display
        self.touch = touch
        self.trackball = trackball
        self.i2c = i2c
        self.sound = sound
        self.apps = []
        self.selected_app = None

    def scan_apps(self):
        """Scan /app directory for valid apps (directories with __init__.py)"""
        self.apps = []
        app_base_path = '/app'
        try:
            app_dirs = os.listdir(app_base_path)
            for dir_name in app_dirs:
                app_full_path = f"{app_base_path}/{dir_name}"
                # Verifica se é um diretório e tem __init__.py
                if '__init__.py' in os.listdir(app_full_path):
                    self.apps.append({
                        'name': dir_name,
                        'path': app_full_path,
                        'init_file': f'{app_full_path}/__init__.py'
                    })
        except Exception as e:
            print(f"Erro ao escanear diretório de apps: {e}")

    def draw_app_list(self):
        """Draw the list of available apps"""
        self.display.fill(st7789.color565(20, 20, 20))  # Dark background

        # Title
        self.display.text(font, "APPS DISPONIVEIS", 30, 10, st7789.WHITE, st7789.color565(20, 20, 20))

        if not self.apps:
            self.display.text(font, "Nenhuma app encontrada", 10, 50, st7789.GRAY, st7789.color565(20, 20, 20))
            self.display.text(font, "Crie diretorios em /app", 10, 70, st7789.GRAY, st7789.color565(20, 20, 20))
            self.display.text(font, "com __init__.py", 10, 90, st7789.GRAY, st7789.color565(20, 20, 20))
            return

        # Draw app list
        y_pos = 40
        for i, app in enumerate(self.apps):
            color = st7789.BLUE if app == self.selected_app else st7789.WHITE
            bg_color = st7789.color565(40, 40, 40) if app == self.selected_app else st7789.color565(20, 20, 20)

            # Draw selection rectangle
            if app == self.selected_app:
                self.display.fill_rect(5, y_pos-2, 310, 20, st7789.color565(40, 40, 40))
                self.display.rect(5, y_pos-2, 310, 20, st7789.BLUE)

            self.display.text(font, f"{i+1}. {app['name']}", 10, y_pos, color, bg_color)
            y_pos += 25

        # Instructions
        self.display.text(font, "Toque ou trackball + click", 10, 200, st7789.GRAY, st7789.color565(20, 20, 20))
        self.display.text(font, "para selecionar", 10, 220, st7789.GRAY, st7789.color565(20, 20, 20))

    def select_app(self, index):
        """Select an app by index"""
        if 0 <= index < len(self.apps):
            self.selected_app = self.apps[index]
            # Don't play sound here, play it in the caller when actually needed
            return True
        return False

    def launch_selected_app(self):
        """Launch the selected app"""
        if not self.selected_app:
            return False

        # Cria o dicionário de hardware para passar para o app
        hardware_globals = {
            'display': self.display,
            'touch': self.touch,
            'trackball': self.trackball,
            'i2c': self.i2c,
            'sound': self.sound
        }

        # Chama o runner para executar o app
        return run_app(self.selected_app['init_file'], hardware_globals)

    def run_launcher(self):
        """Main launcher loop"""
        self.scan_apps()
        selected_index = 0
        self.select_app(selected_index)
        self.draw_app_list()  # Draw initial list

        while True:
            redraw_needed = False

            # Handle touch input
            event_type, x, y = self.touch.read()
            if event_type == Touch.TAP:
                # Calculate which app was tapped
                if y >= 40:
                    tapped_index = (y - 40) // 25
                    if tapped_index < len(self.apps):
                        if tapped_index != selected_index:
                            selected_index = tapped_index
                            self.select_app(selected_index)
                            self.sound.play_navigation()
                            redraw_needed = True
                        else: # Tapped on the already selected app
                            time.sleep_ms(200)  # Debounce
                            if self.launch_selected_app():
                                # App finished, reset state and redraw
                                selected_index = 0
                                self.select_app(selected_index)
                                redraw_needed = True

            # Handle trackball input
            direction, click = self.trackball.get_direction()
            if direction:
                old_index = selected_index
                if direction in ['up', 'left']:
                    selected_index = max(0, selected_index - 1)
                elif direction in ['down', 'right']:
                    selected_index = min(len(self.apps) - 1, selected_index + 1)
                if selected_index != old_index:
                    self.select_app(selected_index)
                    self.sound.play_navigation()
                    redraw_needed = True

            if click and self.selected_app:
                # Launch the app, and if it runs successfully...
                if self.launch_selected_app():
                    # ...reset the selection and redraw the launcher screen.
                    selected_index = 0
                    self.select_app(selected_index)
                    redraw_needed = True

            # Only redraw if something changed
            if redraw_needed:
                self.draw_app_list()

            time.sleep_ms(50)
