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
        menu_items = ["Novo Desenho", "Ver Salvos", "[ Sair ]"]
        self.selected_index = 0

        # Função auxiliar para desenhar o menu e evitar repetição de código
        def draw_menu():
            self.display.fill(BG_COLOR)
            self.display.text(font, "App de Desenho", 10, 10, TEXT_COLOR, BG_COLOR)
            for i, item in enumerate(menu_items):
                color = HIGHLIGHT_COLOR if i == self.selected_index else TEXT_COLOR
                self.display.text(font, item, 40, 60 + i * 30, color, BG_COLOR)

        draw_menu() # Desenha o menu uma vez no início

        while self.mode == 'main_menu':
            direction, click = self.trackball.get_direction()
            
            if direction in ['up', 'down']:
                if direction == 'up':
                    self.selected_index = (self.selected_index - 1 + len(menu_items)) % len(menu_items)
                else: # down
                    self.selected_index = (self.selected_index + 1) % len(menu_items)
                self.sound.play_navigation()
                draw_menu() # Redesenha o menu apenas quando a seleção muda
            
            if click:
                self.sound.play_confirm()
                if self.selected_index == 0:
                    self.mode = 'drawing'
                elif self.selected_index == 1:
                    self._load_saved_files()
                    self.mode = 'file_browser'
                elif self.selected_index == 2:
                    self.mode = 'exit' # Sinaliza para o loop principal sair
            
            time.sleep_ms(50)

    def run_file_browser(self):
        """Tela para visualizar arquivos salvos."""
        self.selected_index = 0
        old_selected_index = -1

        # Função auxiliar para desenhar um item da lista
        def draw_list_item(index, is_selected):
            color = HIGHLIGHT_COLOR if is_selected else TEXT_COLOR
            y_pos = 60 + index * 30 # Posição e espaçamento padronizados
            
            if index < len(self.saved_files):
                # É um arquivo de desenho
                text = self.saved_files[index].replace('.sketch', '')
                self.display.text(font, text[:30], 40, y_pos, color, BG_COLOR) # Recuo padronizado
            else:
                # É o botão "Voltar"
                self.display.text(font, "[ Voltar ]", 40, y_pos, color, BG_COLOR) # Recuo padronizado

        # Desenha a tela inicial uma vez
        self.display.fill(BG_COLOR)
        self.display.text(font, "Desenhos Salvos", 10, 10, TEXT_COLOR, BG_COLOR)

        if not self.saved_files:
            self.display.text(font, "Nenhum desenho salvo.", 10, 50, TEXT_COLOR, BG_COLOR)
        
        # Desenha todos os itens da lista inicialmente
        for i in range(len(self.saved_files) + 1): # +1 para o botão Voltar
            if i > 10: break
            draw_list_item(i, i == self.selected_index)

        while self.mode == 'file_browser':
            direction, click = self.trackball.get_direction()

            if direction:
                old_selected_index = self.selected_index
                if direction == 'up':
                    self.selected_index = max(0, self.selected_index - 1)
                elif direction == 'down':
                    # O limite agora é o número de arquivos + o botão Voltar
                    self.selected_index = min(len(self.saved_files), self.selected_index + 1)
                
                if old_selected_index != self.selected_index:
                    self.sound.play_navigation()
                    # Redesenha apenas os itens afetados para evitar piscar
                    draw_list_item(old_selected_index, False) # Apaga o highlight antigo
                    draw_list_item(self.selected_index, True)  # Desenha o novo highlight

            if click:
                if self.selected_index < len(self.saved_files): # Clicou em um arquivo
                    self.sound.play_confirm()
                    self.run_viewing_canvas(self.saved_files[self.selected_index])
                    # Após voltar, redesenha a tela do browser
                    self.display.fill(BG_COLOR)
                    self.display.text(font, "Desenhos Salvos", 10, 10, TEXT_COLOR, BG_COLOR)
                    for i in range(len(self.saved_files) + 1):
                        if i > 5: break # Limita a 5 itens visíveis para não sobrepor o texto inferior
                        draw_list_item(i, i == self.selected_index)
                else: # Clicou em "Voltar"
                    self.sound.play_navigation()
                    self.mode = 'main_menu'

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

        while self.mode == 'drawing':
            # Lógica de Desenho por Toque
            event_type, tx, ty = self.touch.read()
            if event_type == self.touch.TAP or event_type == self.touch.DRAG:
                # Desenha um pequeno círculo para um traço mais grosso e fácil
                self.display.fill_circle(tx, ty, 2, DRAW_COLOR)
                # Atualiza o buffer para os pixels desenhados (simplificado para o ponto central)
                self._set_pixel_in_buffer(tx, ty, True)

            direction, click = self.trackball.get_direction()

            # Lógica para salvar e sair com um clique
            if click:
                self.sound.play_confirm()
                if self._save_drawing():
                    self.display.text(font, "Salvo!", 200, 230, st7789.GREEN, BG_COLOR)
                else:
                    self.display.text(font, "Falha!", 200, 230, st7789.RED, BG_COLOR)
                time.sleep_ms(1000)
                self.mode = 'main_menu'
                return

            # Um pequeno delay para não sobrecarregar a CPU
            time.sleep_ms(20)

    def run(self):
        """Ponto de entrada principal do aplicativo."""
        while True:
            if self.mode == 'main_menu':
                self.run_main_menu()
            elif self.mode == 'file_browser':
                self.run_file_browser()
            elif self.mode == 'drawing': # type: ignore
                self.run_drawing_canvas()
            elif self.mode == 'exit':
                break # Sai do loop principal do app
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