"""
Sketch App - Um aplicativo de desenho simples para o T-Deck.

Permite criar desenhos em uma tela, salvá-los e visualizá-los.
"""

import time
import st7789py as st7789
from romfonts import vga1_8x8 as font
import os as _os

# --- Constantes ---
BG_COLOR = st7789.color565(20, 20, 30)
TEXT_COLOR = st7789.WHITE
HIGHLIGHT_COLOR = st7789.CYAN
CURSOR_COLOR = st7789.RED
DRAW_COLOR = st7789.WHITE

SKETCH_DIR = '/sd/app/sketch/drawings'

class SketchApp:
    def __init__(self, display, touch, trackball, i2c, sound):
        self.display = display
        self.trackball = trackball
        self.touch = touch
        self.sound = sound
        
        self.mode = 'main_menu' # 'main_menu', 'file_browser', 'drawing', 'viewing'
        self.saved_files = []
        self.selected_index = 0
        
        # Estado do canvas de desenho
        self.cursor_x = self.display.width // 2
        self.cursor_y = self.display.height // 2
        
        # Buffer para o desenho (1-bit: 320*240 / 8 = 9600 bytes)
        # Usamos um buffer para não ter que ler da tela, o que é lento.
        self.draw_buffer = bytearray((self.display.width * self.display.height) // 8)

    def _ensure_dir_exists(self):
        """Garante que o diretório de desenhos exista."""
        try:
            _os.mkdir(SKETCH_DIR)
        except OSError:
            pass # Diretório já existe

    def _load_saved_files(self):
        """Carrega a lista de desenhos salvos."""
        self._ensure_dir_exists()
        self.saved_files = sorted([f for f in _os.listdir(SKETCH_DIR) if f.endswith('.sketch')], reverse=True)

    # --- Funções de Desenho e Arquivo ---

    def _set_pixel_in_buffer(self, x, y, state):
        """Define um pixel no buffer de 1-bit."""
        if not (0 <= x < self.display.width and 0 <= y < self.display.height):
            return
        index = (y * self.display.width + x) // 8
        bit = 7 - ((y * self.display.width + x) % 8)
        if state:
            self.draw_buffer[index] |= (1 << bit)
        else:
            self.draw_buffer[index] &= ~(1 << bit)

    def _save_drawing(self):
        """Salva o buffer de desenho em um arquivo."""
        self._ensure_dir_exists()
        t = time.localtime()
        filename = f"desenho_{t[0]:04d}{t[1]:02d}{t[2]:02d}_{t[3]:02d}{t[4]:02d}{t[5]:02d}.sketch"
        filepath = f"{SKETCH_DIR}/{filename}"
        
        try:
            with open(filepath, 'wb') as f:
                # Salva as dimensões para referência futura
                f.write(bytes([self.display.width // 256, self.display.width % 256]))
                f.write(bytes([self.display.height // 256, self.display.height % 256]))
                f.write(self.draw_buffer)
            return True
        except OSError:
            return False

    def _load_drawing_to_display(self, filename):
        """Carrega um desenho do arquivo e o exibe na tela."""
        filepath = f"{SKETCH_DIR}/{filename}"
        try:
            with open(filepath, 'rb') as f:
                f.read(4) # Pula as dimensões por enquanto
                buffer = f.read()
                
                self.display.fill(BG_COLOR)
                for y in range(self.display.height):
                    for x in range(self.display.width):
                        index = (y * self.display.width + x) // 8
                        bit = 7 - ((y * self.display.width + x) % 8)
                        if (buffer[index] >> bit) & 1:
                            self.display.pixel(x, y, DRAW_COLOR)
            return True
        except OSError:
            return False

    # --- Telas (Modos) do Aplicativo ---

    def run_main_menu(self):
        """Tela do menu principal."""
        menu_items = ["Novo Desenho", "Ver Salvos"]
        self.selected_index = 0

        while self.mode == 'main_menu':
            self.display.fill(BG_COLOR)
            self.display.text(font, "App de Desenho", 10, 10, TEXT_COLOR, BG_COLOR)
            
            for i, item in enumerate(menu_items):
                color = HIGHLIGHT_COLOR if i == self.selected_index else TEXT_COLOR
                self.display.text(font, item, 40, 80 + i * 30, color, BG_COLOR)

            direction, click = self.trackball.get_direction()
            if direction in ['up', 'down']:
                self.selected_index = 1 - self.selected_index # Alterna entre 0 e 1
                self.sound.play_navigation()
            
            if click:
                self.sound.play_confirm()
                if self.selected_index == 0:
                    self.mode = 'drawing'
                else:
                    self._load_saved_files()
                    self.mode = 'file_browser'
            
            time.sleep_ms(50)

    def run_file_browser(self):
        """Tela para visualizar arquivos salvos."""
        self.selected_index = 0
        
        while self.mode == 'file_browser':
            self.display.fill(BG_COLOR)
            self.display.text(font, "Desenhos Salvos (Voltar=Direita)", 10, 10, TEXT_COLOR, BG_COLOR)

            if not self.saved_files:
                self.display.text(font, "Nenhum desenho salvo.", 10, 50, TEXT_COLOR, BG_COLOR)
            else:
                for i, filename in enumerate(self.saved_files):
                    if i > 10: break # Limita a exibição
                    color = HIGHLIGHT_COLOR if i == self.selected_index else TEXT_COLOR
                    self.display.text(font, filename.replace('.sketch', ''), 10, 40 + i * 15, color, BG_COLOR)

            direction, click = self.trackball.get_direction()
            if direction == 'up':
                self.selected_index = max(0, self.selected_index - 1)
                self.sound.play_navigation()
            elif direction == 'down':
                self.selected_index = min(len(self.saved_files) - 1, self.selected_index + 1)
                self.sound.play_navigation()
            elif direction == 'right': # Sair do browser
                self.mode = 'main_menu'
                self.sound.play_navigation()

            if click and self.saved_files:
                self.sound.play_confirm()
                self.run_viewing_canvas(self.saved_files[self.selected_index])

            time.sleep_ms(50)

    def run_viewing_canvas(self, filename):
        """Tela para visualizar um desenho salvo (read-only)."""
        if not self._load_drawing_to_display(filename):
            return # Falha ao carregar
        
        # Aguarda um clique ou movimento para a direita para sair
        while True:
            direction, click = self.trackball.get_direction()
            if click or direction == 'right':
                self.sound.play_navigation()
                return # Volta para o file browser
            time.sleep_ms(50)

    def run_drawing_canvas(self):
        """Tela principal de desenho."""
        # Limpa o buffer e a tela
        self.draw_buffer = bytearray(len(self.draw_buffer))
        self.display.fill(BG_COLOR)
        self.display.text(font, "Direita=Sair/Salvar", 10, 230, TEXT_COLOR, BG_COLOR)
        
        last_cursor_x, last_cursor_y = self.cursor_x, self.cursor_y
        is_drawing = False

        while self.mode == 'drawing':
            # Apaga o cursor antigo (desenhando um pixel da cor de fundo)
            self.display.pixel(last_cursor_x, last_cursor_y, BG_COLOR)
            # Se o cursor estava sobre um pixel desenhado, redesenha-o
            index = (last_cursor_y * self.display.width + last_cursor_x) // 8
            bit = 7 - ((last_cursor_y * self.display.width + last_cursor_x) % 8)
            if (self.draw_buffer[index] >> bit) & 1:
                self.display.pixel(last_cursor_x, last_cursor_y, DRAW_COLOR)

            # --- NOVO: Lógica de Desenho por Toque ---
            event_type, tx, ty = self.touch.read()
            if event_type == self.touch.TAP or event_type == self.touch.DRAG:
                # Desenha um pequeno círculo para um traço mais grosso e fácil
                self.display.fill_circle(tx, ty, 2, DRAW_COLOR)
                # Atualiza o buffer para os pixels desenhados (simplificado para o ponto central)
                self._set_pixel_in_buffer(tx, ty, True)
                # O som de toque pode ser muito repetitivo, então é opcional
                # self.sound.play_keypress()

            direction, click = self.trackball.get_direction()

            # Movimento do cursor
            if direction == 'up': self.cursor_y = max(0, self.cursor_y - 1)
            elif direction == 'down': self.cursor_y = min(self.display.height - 1, self.cursor_y + 1)
            elif direction == 'left': self.cursor_x = max(0, self.cursor_x - 1)
            elif direction == 'right':
                # Sair e salvar
                self.sound.play_confirm()
                if self._save_drawing():
                    self.display.text(font, "Salvo!", 200, 230, st7789.GREEN, BG_COLOR)
                else:
                    self.display.text(font, "Falha!", 200, 230, st7789.RED, BG_COLOR)
                time.sleep(1)
                self.mode = 'main_menu'
                return

            # Lógica de desenho
            if click:
                is_drawing = not is_drawing # Alterna o modo de desenho
                self.sound.play_keypress()

            if is_drawing:
                self._set_pixel_in_buffer(self.cursor_x, self.cursor_y, True)
                self.display.pixel(self.cursor_x, self.cursor_y, DRAW_COLOR)

            # Desenha o novo cursor
            self.display.pixel(self.cursor_x, self.cursor_y, CURSOR_COLOR)
            last_cursor_x, last_cursor_y = self.cursor_x, self.cursor_y

            time.sleep_ms(10) # Delay pequeno para um movimento mais fluido

    def run(self):
        """Ponto de entrada principal do aplicativo."""
        while True:
            if self.mode == 'main_menu':
                self.run_main_menu()
            elif self.mode == 'file_browser':
                self.run_file_browser()
            elif self.mode == 'drawing':
                self.run_drawing_canvas()
            else: # Se o modo for desconhecido, volta ao menu
                self.mode = 'main_menu'

# --- Ponto de Entrada do App ---
try:
    app = SketchApp(display, touch, trackball, i2c, sound)
    app.run()
except Exception as e:
    _display = globals().get('display')
    if _display:
        _display.fill(st7789.RED)
        _display.text(font, "ERRO NO APP SKETCH", 10, 10, st7789.WHITE, st7789.RED)
        _display.text(font, str(e)[:35], 10, 30, st7789.WHITE, st7789.RED)
        time.sleep(5)