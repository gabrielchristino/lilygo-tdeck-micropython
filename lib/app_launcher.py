"""App Launcher Module - Lists and launches apps from /sd/app directory"""

import os as _os # Importa 'os' com um alias para evitar conflitos
import gc  # Importar o Garbage Collector
import time
import tft_config as tft
import st7789py as st7789
from romfonts import vga1_8x8 as font
from lib.app_runner import run_app  # Importa o novo runner
from lib.touch import Touch
from lib.trackball import Trackball
from lib.sound import SoundManager

# --- Constantes para a Barra de Status ---
STATUS_BAR_HEIGHT = 20
STATUS_BAR_BG_COLOR = st7789.color565(10, 10, 15) # Cor de fundo da barra de status


class AppLauncher:
    def __init__(self, display, touch, trackball, i2c, sound):
        self.display = display
        self.touch = touch
        self.trackball = trackball
        self.i2c = i2c
        self.sound = sound
        self.apps = []
        self.selected_index = 0
        self.scroll_offset = 0 # Índice do primeiro app visível na tela
        self.visible_items = 4 # Ajustado para acomodar a barra de status e título

    def scan_apps(self):
        """Scan /sd/app directory for valid apps (directories with __init__.py)"""
        self.apps = []
        app_base_path = '/sd/app'
        try:
            app_dirs = _os.listdir(app_base_path)
            for dir_name in app_dirs:
                app_full_path = f"{app_base_path}/{dir_name}"
                # Verifica se é um diretório e tem __init__.py
                dir_contents = _os.listdir(app_full_path)
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

    def draw_app_list(self):
        """Draw the vertical list of available apps"""
        self.display.fill(st7789.color565(20, 20, 20))  # Dark background

        # --- Desenha a Barra de Status ---
        self.display.fill_rect(0, 0, self.display.width, STATUS_BAR_HEIGHT, STATUS_BAR_BG_COLOR)

        # Data e Hora
        now = time.localtime()
        date_time_str = f"{now[2]:02d}/{now[1]:02d} {now[3]:02d}:{now[4]:02d}"
        self.display.text(font, date_time_str, 5, 5, st7789.WHITE, STATUS_BAR_BG_COLOR)

        # Status da Bateria (Placeholder)
        # Para uma implementação real, você precisaria de hardware para ler o nível da bateria
        battery_str = "Bat: 85%" # Placeholder
        battery_x = self.display.width - (len(battery_str) * font.WIDTH) - 5
        self.display.text(font, battery_str, battery_x, 5, st7789.WHITE, STATUS_BAR_BG_COLOR)

        # Título removido, a barra de status já serve como cabeçalho

        if not self.apps:
            self.display.text(font, "Nenhum app encontrado", 10, STATUS_BAR_HEIGHT + 30, st7789.GRAY, st7789.color565(20, 20, 20))
            return

        # --- Desenha a lista de apps com rolagem ---
        item_height = 40
        # Posição Y inicial da lista de apps (abaixo da barra de status e título)
        app_list_start_y = STATUS_BAR_HEIGHT + 5 # Começa logo abaixo da barra de status
        icon_size = 30
        
        for i in range(self.visible_items):
            index = self.scroll_offset + i
            if index >= len(self.apps):
                break

            app = self.apps[index]
            is_selected = (index == self.selected_index)

            # 'i' é o índice visível na tela, 'index' é o índice real na lista de apps
            y = i * item_height + app_list_start_y
            x = 10

            color = st7789.WHITE
            bg_color = st7789.color565(40, 40, 40) if is_selected else st7789.color565(20, 20, 20)

            # Draw item background
            item_width = self.display.width - (x * 2)
            self.display.fill_rect(x, y, item_width, item_height - 2, bg_color)

            # Draw selection border
            if is_selected:
                self.display.rect(x - 2, y - 2, item_width + 4, item_height + 2, st7789.CYAN) # Use HIGHLIGHT_COLOR

            # Draw icon
            if app['icon_path']:
                icon_y = y + (item_height - icon_size) // 2
                if app['icon_path'].endswith('.p4'):
                    self.display.draw_p4(app['icon_path'], x + 2, icon_y)
                elif app['icon_path'].endswith('.bmp'):
                    try:
                        self.display.draw_bmp(app['icon_path'], x + 2, icon_y)
                    except Exception:
                        self.display.fill_rect(x + 2, icon_y, icon_size, icon_size, st7789.RED)
            
            # Draw app name
            self.display.text(font, app['name'][:25], x + icon_size + 10, y + 10, color, bg_color)

        # Draw scrollbar
        if len(self.apps) > self.visible_items:
            scrollbar_total_height = self.display.height - app_list_start_y - 5
            scrollbar_width = 5
            scrollbar_x = self.display.width - scrollbar_width - 5
            
            visible_portion_ratio = self.visible_items / len(self.apps)
            thumb_height = max(10, int(scrollbar_total_height * visible_portion_ratio))
            
            scroll_ratio = self.scroll_offset / (len(self.apps) - self.visible_items) if len(self.apps) > self.visible_items else 0
            thumb_y = app_list_start_y + int((scrollbar_total_height - thumb_height) * scroll_ratio)
            
            self.display.fill_rect(scrollbar_x, app_list_start_y, scrollbar_width, scrollbar_total_height, st7789.GRAY) # Track
            self.display.fill_rect(scrollbar_x, thumb_y, scrollbar_width, thumb_height, st7789.BLUE) # Thumb

    def select_app(self, index):
        """Select an app by index and adjust scroll_offset if necessary."""
        if 0 <= index < len(self.apps):
            self.selected_index = index
            # Adjust scroll_offset to keep selected_index visible
            if self.selected_index < self.scroll_offset:
                self.scroll_offset = self.selected_index
            elif self.selected_index >= self.scroll_offset + self.visible_items:
                self.scroll_offset = self.selected_index - self.visible_items + 1
            return True
        return False

    def reset_icon_cache(self):
        """Reset icon loaded cache for all apps"""
        # This method is no longer needed as icons are drawn directly
        pass

    def launch_selected_app(self):
        """Launch the selected app"""
        if not (0 <= self.selected_index < len(self.apps)):
            return False

        selected_app_data = self.apps[self.selected_index]

        # Cria o dicionário de hardware para passar para o app
        hardware_globals = {
            'display': self.display,
            'touch': self.touch,
            'trackball': self.trackball,
            'i2c': self.i2c,
            'sound': self.sound
        }

        # Chama o runner para executar o app
        return run_app(selected_app_data['init_file'], hardware_globals)

    def run_launcher(self):
        """Main launcher loop"""
        self.scan_apps()
        
        if not self.apps:
            self.draw_app_list() # Draw "No apps found" message
            while True: time.sleep_ms(100) # Wait indefinitely

        self.selected_index = 0
        self.select_app(self.selected_index) # Ensure scroll_offset is correct
        
        while True:
            self.draw_app_list() # Redraw the entire list after an action
            
            # Loop de entrada
            while True:
                key = None # No keyboard input for launcher
                direction, click = self.trackball.get_direction()

                # Handle trackball input
                if direction:
                    old_selected_index = self.selected_index
                    if direction == 'up':
                        self.selected_index = max(0, self.selected_index - 1)
                    elif direction == 'down':
                        self.selected_index = min(len(self.apps) - 1, self.selected_index + 1)
                    
                    if self.selected_index != old_selected_index:
                        self.select_app(self.selected_index) # This will also adjust scroll_offset
                        self.sound.play_navigation()
                        break # Break to redraw

                if click:
                    self.sound.play_confirm()
                    # Launch the app, and if it runs successfully...
                    if self.launch_selected_app():
                        # ...reset the selection and redraw the launcher screen.
                        gc.collect() # Força a coleta de lixo para liberar memória
                        self.scan_apps() # Re-scan apps in case something changed
                        # Ensure selected_index is still valid after scan (apps might have changed)
                        if self.selected_index >= len(self.apps):
                            self.selected_index = max(0, len(self.apps) - 1)
                        self.select_app(self.selected_index) # Re-select to refresh state and scroll
                        break # Break to redraw

                # Atualiza a barra de status periodicamente sem quebrar o loop de entrada
                # (Isso é uma otimização para o relógio, mas redesenhar tudo ainda é aceitável)
                # Para uma atualização mais suave, seria necessário um timer.
                # Por simplicidade, o relógio só atualiza quando uma ação ocorre.
                time.sleep_ms(50)
