"""
Notepad App - Bloco de Notas Simplificado e Robusto

Permite criar, visualizar e editar notas de texto, com um botão para sair.
"""

import time
import st7789py as st7789
from romfonts import vga1_8x8 as font
import os as _os # Importa 'os' com um alias seguro

# --- Constantes ---
BG_COLOR = st7789.color565(20, 20, 30)
TEXT_COLOR = st7789.WHITE
HIGHLIGHT_COLOR = st7789.CYAN
INPUT_BG_COLOR = st7789.color565(30, 30, 50)
KBD_I2C_ADDR = 0x55
NOTES_DIR = '/sd/app/notepad/notes'

class NotepadApp:
    def __init__(self, display, touch, trackball, i2c, sound):
        self.display = display
        self.trackball = trackball
        self.i2c = i2c
        self.sound = sound
        self.notes = []
        self.focused_element = 'input'  # 'list', 'input', ou 'exit'
        self.selected_note_index = 0
        self.active_text = "" # Texto ativo na caixa de edição/criação
        self.editing_filename = None # Nome do arquivo que está sendo editado

    def draw_header(self, text):
        self.display.fill(BG_COLOR)
        self.display.text(font, text, 10, 10, TEXT_COLOR, BG_COLOR)

    def get_key_simple(self):
        try:
            key = self.i2c.readfrom(KBD_I2C_ADDR, 1)
            if key != b'\x00': return key
        except OSError: pass
        return None

    def load_notes(self):
        """Carrega os nomes dos arquivos e uma prévia do conteúdo de cada nota."""
        self.notes = []
        try:
            # Garante que o diretório de notas exista
            _os.mkdir(NOTES_DIR)
        except OSError:
            pass # Diretório já existe
        
        filenames = sorted(_os.listdir(NOTES_DIR), reverse=True)
        for filename in filenames:
            try:
                with open(f"{NOTES_DIR}/{filename}", 'r') as f:
                    preview = f.readline().strip() # Lê apenas a primeira linha
                    self.notes.append({'filename': filename, 'preview': preview})
            except Exception:
                pass # Ignora arquivos que não podem ser lidos

    def save_note(self, content, filename=None):
        """Salva o conteúdo em um arquivo de nota."""
        if not content: return # Não salva notas vazias

        if filename is None:
            # Cria um nome de arquivo baseado na data/hora atual
            t = time.localtime()
            filename = f"nota_{t[0]:04d}{t[1]:02d}{t[2]:02d}_{t[3]:02d}{t[4]:02d}{t[5]:02d}.txt"
        
        filepath = f"{NOTES_DIR}/{filename}"
        try:
            with open(filepath, 'w') as f:
                f.write(content)
            self.load_notes() # Recarrega a lista de notas
        except Exception:
            pass # Falha silenciosa

    def read_note_content(self, filename):
        """Lê o conteúdo de um arquivo de nota."""
        filepath = f"{NOTES_DIR}/{filename}"
        try:
            with open(filepath, 'r') as f: return f.read()
        except Exception:
            return ""

    def draw_main_ui(self):
        """Desenha a UI principal com a lista de notas e a caixa de nova nota."""
        self.draw_header("Bloco de Notas")
        
        # Desenha a lista de notas salvas
        for i, note_file in enumerate(self.notes):
            if i > 8: break # Limita a 9 notas visíveis na tela
            y = 40 + i * 15
            is_list_item_focused = (self.focused_element == 'list' and i == self.selected_note_index)
            color = HIGHLIGHT_COLOR if is_list_item_focused else TEXT_COLOR
            # Mostra a prévia do conteúdo da nota
            self.display.text(font, f"{note_file['preview'][:38]}", 10, y, color, BG_COLOR)

        # Desenha a caixa de entrada para nova nota
        is_input_focused = (self.focused_element == 'input')
        new_note_box_y = 200
        input_width = self.display.width - 100 # Largura da caixa de texto
        exit_button_x = input_width + 20 # Posição do botão Sair
        self.display.text(font, "Nova Nota:", 10, new_note_box_y - 12, TEXT_COLOR, BG_COLOR)
        
        # Desenha a caixa e a borda de foco
        self.display.fill_rect(10, new_note_box_y, input_width, 20, INPUT_BG_COLOR)
        if is_input_focused:
            self.display.rect(10, new_note_box_y, input_width, 20, HIGHLIGHT_COLOR)
        else:
            self.display.rect(10, new_note_box_y, input_width, 20, TEXT_COLOR)
            
        self.display.text(font, self.active_text, 15, new_note_box_y + 6, TEXT_COLOR, INPUT_BG_COLOR)

        # Desenha o botão Sair
        is_exit_focused = (self.focused_element == 'exit')
        color = HIGHLIGHT_COLOR if is_exit_focused else TEXT_COLOR
        self.display.text(font, "[ Sair ]", exit_button_x, new_note_box_y + 6, color, BG_COLOR)

    def run(self):
        """Loop principal do aplicativo."""
        self.load_notes()

        while True:
            self.draw_main_ui()
            
            # Loop de entrada da tela principal
            while True:
                key = self.get_key_simple()
                direction, click = self.trackball.get_direction()

                # --- Processa a entrada do teclado (apenas para a caixa de texto) ---
                if key and self.focused_element == 'input':
                        if key == b'\r': # Enter
                            self.sound.play_confirm()
                            self.save_note(self.active_text, self.editing_filename)
                            self.active_text = "" # Limpa a caixa
                            self.editing_filename = None # Sai do modo de edição
                            break # Sai para redesenhar a lista
                        elif key == b'\x08': # Backspace
                            self.active_text = self.active_text[:-1]
                        else:
                            try:
                                if len(self.active_text) < 200: # Limite de caracteres por nota
                                    self.active_text += key.decode('utf-8')
                            except UnicodeError: pass
                        self.sound.play_keypress()
                        break # Redesenha a caixa de texto

                # Processa a navegação do trackball
                if direction:
                    if self.focused_element == 'list':
                        if direction == 'up': self.selected_note_index = max(0, self.selected_note_index - 1)
                        elif direction == 'down':
                            self.selected_note_index += 1
                            if self.selected_note_index >= len(self.notes):
                                self.focused_element = 'input' # Da lista para a caixa de texto
                    elif self.focused_element in ['input', 'exit']:
                        if direction == 'up': self.focused_element = 'list' # Da parte de baixo para a lista
                        elif direction == 'left': self.focused_element = 'input'
                        elif direction == 'right': self.focused_element = 'exit'

                    self.sound.play_navigation()
                    break # Sai para redesenhar a seleção

                # Processa o clique do trackball para Sair
                if click and self.focused_element == 'exit':
                    return # Termina o método run() e fecha o app

                # Processa o clique do trackball para editar uma nota
                if click and self.focused_element == 'list':
                    self.sound.play_confirm()
                    note_to_edit = self.notes[self.selected_note_index]
                    self.editing_filename = note_to_edit['filename']
                    self.active_text = self.read_note_content(self.editing_filename)
                    self.focused_element = 'input' # Move o foco para a caixa de texto
                    break # Sai para redesenhar a tela principal após a edição

                time.sleep_ms(50)

# --- Ponto de Entrada do App ---
try:
    app = NotepadApp(display, touch, trackball, i2c, sound)
    app.run()
except Exception as e:
    print(f"!!! ERRO ao executar Bloco de Notas: {e}")
    # Tenta exibir o erro na tela
    _display = globals().get('display')
    if _display:
        _display.fill(st7789.RED)
        _display.text(font, "ERRO NO APP", 10, 10, st7789.WHITE, st7789.RED)
        try:
            _display.text(font, str(e)[:35], 10, 30, st7789.WHITE, st7789.RED)
        except: pass
        time.sleep(5)
