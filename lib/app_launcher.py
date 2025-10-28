"""App Launcher Module - Lists and launches apps from /sd/app directory"""

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
        """Scan /sd/app directory for valid apps (directories with __init__.py)"""
        self.apps = []
        app_base_path = '/sd/app'
        try:
            app_dirs = os.listdir(app_base_path)
            for dir_name in app_dirs:
                app_full_path = f"{app_base_path}/{dir_name}"
                # Verifica se é um diretório e tem __init__.py
                dir_contents = os.listdir(app_full_path)
                if '__init__.py' in dir_contents:
                    icon_path = None
                    if '__icon__.p4' in dir_contents:
                        icon_path = f'{app_full_path}/__icon__.p4'
                    elif '__icon__.bmp' in dir_contents:
                        icon_path = f'{app_full_path}/__icon__.bmp'

                    self.apps.append({
                        'name': dir_name,
                        'path': app_full_path,
                        'init_file': f'{app_full_path}/__init__.py',
                        'icon_path': icon_path
                    })
        except OSError as e:
            # Se o diretório /sd/app não existir (ENOENT), não é um erro fatal.
            # Apenas significa que não há apps para listar.
            if e.args[0] == 2: # errno 2 is ENOENT
                print("Diretório de apps '/sd/app' não encontrado. Verifique o SD card.")
            else:
                print(f"Erro de I/O ao escanear diretório de apps: {e}")

    def draw_app_item(self, index):
        """Draw a single app item at a given index."""
        if not (0 <= index < len(self.apps)):
            return

        app = self.apps[index]
        is_selected = (app == self.selected_app)

        # List settings
        item_height = 40
        start_y = 40
        icon_size = 30
        
        y = index * item_height + start_y
        x = 10

        color = st7789.BLUE if is_selected else st7789.WHITE
        bg_color = st7789.color565(40, 40, 40) if is_selected else st7789.color565(20, 20, 20)

        # Draw item background
        self.display.fill_rect(x - 5, y - 2, 220, item_height - 4, bg_color)

        # Draw selection border
        if is_selected:
            self.display.rect(x - 5, y - 2, 220, item_height - 4, st7789.BLUE)

        # Draw icon
        if app['icon_path']:
            icon_y = y + (item_height - icon_size - 4) // 2
            if app['icon_path'].endswith('.p4'):
                self.display.draw_p4(app['icon_path'], x, icon_y)
            elif app['icon_path'].endswith('.bmp'):
                try:
                    self.display.draw_bmp(app['icon_path'], x, icon_y)
                except Exception as e:
                    print(f"Erro ao desenhar icone {app['icon_path']}: {e}")
                    self.display.fill_rect(x, icon_y, icon_size, icon_size, st7789.RED)
        
        # Draw app name (sem fundo para não cortar o ícone)
        self.display.text(font, app['name'][:15], x + icon_size + 10, y + 10, color, bg_color)

    def draw_app_list(self):
        """Draw the vertical list of available apps"""
        self.display.fill(st7789.color565(20, 20, 20))  # Dark background

        # Title
        self.display.text(font, "APPS DISPONIVEIS", 30, 10, st7789.WHITE, st7789.color565(20, 20, 20))

        if not self.apps:
            self.display.text(font, "Nenhuma app encontrada", 10, 50, st7789.GRAY, st7789.color565(20, 20, 20))
            self.display.text(font, "Crie diretorios em /sd/app", 10, 70, st7789.GRAY, st7789.color565(20, 20, 20))
            self.display.text(font, "com __init__.py", 10, 90, st7789.GRAY, st7789.color565(20, 20, 20))
            return

        # Draw app list
        for i, app in enumerate(self.apps):
            self.draw_app_item(i)

    def select_app(self, index):
        """Select an app by index"""
        if 0 <= index < len(self.apps):
            self.selected_app = self.apps[index]
            # Don't play sound here, play it in the caller when actually needed
            return True
        return False

    def reset_icon_cache(self):
        """Reset icon loaded cache for all apps"""
        for app in self.apps:
            if 'icon_loaded' in app:
                del app['icon_loaded']

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
        self.reset_icon_cache()  # Reset cache on start
        selected_index = 0
        last_selected_index = -1
        self.select_app(selected_index)
        self.draw_app_list()  # Draw initial list

        while True:
            redraw_needed = False

            # Handle touch input
            event_type, x, y = self.touch.read()
            if event_type == Touch.TAP:
                # Calculate which app was tapped in list
                if y >= 40:
                    item_height = 40
                    tapped_index = (y - 40) // item_height
                    if 0 <= tapped_index < len(self.apps):
                        if tapped_index != selected_index:
                            last_selected_index = selected_index
                            selected_index = tapped_index
                            self.select_app(selected_index)
                            self.sound.play_navigation()
                            redraw_needed = True
                        else: # Tapped on the already selected app
                            time.sleep_ms(200)  # Debounce
                            last_selected_index = selected_index
                            if self.launch_selected_app():
                                # App finished, reset state and redraw
                                self.scan_apps() # Re-scan apps in case something changed
                                self.select_app(selected_index) # Re-select to refresh state
                                self.draw_app_list() # Full redraw after app closes

            # Handle trackball input
            direction, click = self.trackball.get_direction()
            if direction:
                old_index = selected_index
                if direction == 'up':
                    selected_index = max(0, selected_index - 1)
                elif direction == 'down':
                    selected_index = min(len(self.apps) - 1, selected_index + 1)
                elif direction == 'left':
                    # No left/right in list, maybe wrap or ignore
                    pass
                elif direction == 'right':
                    # No left/right in list, maybe wrap or ignore
                    pass
                if selected_index != old_index:
                    last_selected_index = old_index # Guarda o índice antigo para redesenhar
                    self.select_app(selected_index)
                    self.sound.play_navigation()
                    redraw_needed = True

            if click and self.selected_app:
                last_selected_index = selected_index
                # Launch the app, and if it runs successfully...
                if self.launch_selected_app():
                    # ...reset the selection and redraw the launcher screen.
                    self.select_app(selected_index)
                    self.draw_app_list() # Redesenho completo após sair do app

            # Only redraw if something changed
            if redraw_needed:
                # Redesenha o item antigo para remover a seleção
                if last_selected_index != -1:
                    self.draw_app_item(last_selected_index)
                # Redesenha o novo item selecionado
                self.draw_app_item(selected_index)

            time.sleep_ms(50)
