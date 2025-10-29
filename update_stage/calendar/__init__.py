"""
Calendar App - Calendário com Eventos

Permite visualizar o calendário, navegar entre meses/dias e criar eventos.
"""

import time
import st7789py as st7789
from romfonts import vga1_8x8 as font
import os as _os # Importa 'os' com um alias seguro

# --- Constantes ---
BG_COLOR = st7789.color565(20, 20, 30)
TEXT_COLOR = st7789.WHITE
HEADER_COLOR = st7789.YELLOW
HIGHLIGHT_COLOR = st7789.CYAN
INPUT_BG_COLOR = st7789.color565(30, 30, 50) # Cor do fundo da caixa de texto
EVENT_INDICATOR_COLOR = st7789.RED
KBD_I2C_ADDR = 0x55
EVENTS_DIR = '/sd/app/calendar/events'

MONTH_NAMES = ["", "Janeiro", "Fevereiro", "Marco", "Abril", "Maio", "Junho", 
             "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
DAY_ABBREVIATIONS = ["D", "S", "T", "Q", "Q", "S", "S"]

class CalendarApp:
    def __init__(self, display, touch, trackball, i2c, sound):
        self.display = display
        self.trackball = trackball
        self.i2c = i2c
        self.sound = sound
        
        # Estado do calendário
        now = time.localtime()
        self.year = now[0]
        self.month = now[1]
        self.selected_day = now[2]
        
        self.events = {} # Cache de eventos para o mês atual
        self.focused_element = 'calendar' # 'calendar' ou 'exit'

    # --- Funções de Lógica de Calendário ---
    def is_leap(self, year):
        return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)

    def days_in_month(self, year, month):
        if month == 2:
            return 29 if self.is_leap(year) else 28
        elif month in [4, 6, 9, 11]:
            return 30
        else:
            return 31

    def first_day_of_month(self, year, month):
        # time.mktime e localtime são pesados, mas a forma mais fácil
        # tm_wday: 0=Seg, 6=Dom. Queremos Dom=0, Seg=1, ...
        first_day_tuple = (year, month, 1, 0, 0, 0, 0, 0)
        t = time.mktime(first_day_tuple)
        weekday = time.localtime(t)[6]
        return (weekday + 1) % 7

    # --- Funções de UI e Eventos ---
    def draw_header(self, text):
        self.display.fill(BG_COLOR)
        self.display.text(font, text, 10, 10, TEXT_COLOR, BG_COLOR)

    def get_key_simple(self):
        try:
            key = self.i2c.readfrom(KBD_I2C_ADDR, 1)
            if key != b'\x00': return key
        except OSError: pass
        return None

    def load_events_for_month(self):
        """Verifica quais dias do mês atual têm eventos."""
        self.events = {}
        try:
            _os.mkdir(EVENTS_DIR)
        except OSError: pass # Diretório já existe

        prefix = f"{self.year:04d}-{self.month:02d}-"
        for filename in _os.listdir(EVENTS_DIR):
            if filename.startswith(prefix):
                try:
                    day = int(filename.split('-')[2].split('.')[0])
                    self.events[day] = True
                except (ValueError, IndexError):
                    pass

    def _confirm_delete_ui(self):
        """Mostra uma UI de confirmação para apagar um evento."""
        self.display.fill_rect(40, 80, 240, 80, BG_COLOR) # Limpa a área do modal
        self.display.rect(40, 80, 240, 80, HIGHLIGHT_COLOR) # Borda Ciano
        self.display.text(font, "Apagar este evento?", 60, 95, TEXT_COLOR, BG_COLOR)
        
        confirm_focus = 'no' # 'yes' ou 'no'
        
        while True:
            yes_color = HIGHLIGHT_COLOR if confirm_focus == 'yes' else TEXT_COLOR
            no_color = HIGHLIGHT_COLOR if confirm_focus == 'no' else TEXT_COLOR
            self.display.text(font, "[ Nao ]", 60, 130, no_color, BG_COLOR)
            self.display.text(font, "[ Sim ]", 180, 130, yes_color, BG_COLOR)

            direction, click = self.trackball.get_direction()
            key = self.get_key_simple()

            if direction and direction in ['left', 'right']:
                confirm_focus = 'yes' if confirm_focus == 'no' else 'no'
                self.sound.play_navigation()
            
            if click or (key and key == b'\r'):
                self.sound.play_confirm()
                # A tela de confirmação é limpa pelo redesenho do editor principal
                return confirm_focus == 'yes'
            
            # Se o usuário pressionar qualquer outra tecla, cancela
            if key and key != b'\r':
                self.sound.play_navigation()
                return False

            time.sleep_ms(50)

    def _draw_event_editor(self, content, editor_focus):
        """Desenha a UI do editor de eventos."""
        # Limpa a área de texto e o rodapé
        self.display.fill_rect(10, 40, self.display.width - 20, 170, BG_COLOR)
        self.display.fill_rect(0, 220, self.display.width, 20, BG_COLOR)
        
        # Divide o conteúdo em linhas e desenha cada uma
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if i > 18: break # Limita o número de linhas visíveis
            self.display.text(font, line, 15, 46 + i * (font.HEIGHT + 2), TEXT_COLOR, BG_COLOR)
        
        # Desenha o botão Salvar
        is_button_focused = (editor_focus == 'save_button')
        save_color = HIGHLIGHT_COLOR if is_button_focused else TEXT_COLOR
        self.display.text(font, "[ Salvar ]", 10, 225, save_color, BG_COLOR)

        # Desenha o botão Apagar
        is_del_button_focused = (editor_focus == 'delete_button')
        del_color = HIGHLIGHT_COLOR if is_del_button_focused else TEXT_COLOR
        self.display.text(font, "[ Apagar ]", 120, 225, del_color, BG_COLOR)

    def edit_event_ui(self, year, month, day):
        """Abre uma UI para editar o evento de um dia específico."""
        filename = f"{year:04d}-{month:02d}-{day:02d}.txt"
        filepath = f"{EVENTS_DIR}/{filename}"
        content = ""
        try:
            with open(filepath, 'r') as f:
                content = f.read()
        except OSError: pass # Arquivo não existe ainda

        editor_focus = 'text' # 'text', 'save_button', ou 'delete_button'
        self.draw_header(f"Evento: {day}/{month}/{year}")

        while True:
            # --- Loop Externo: Desenha a tela ---
            # Limpa a área de conteúdo, mas preserva o cabeçalho
            self.display.fill_rect(0, 35, self.display.width, 205, BG_COLOR)

            # Define a área da caixa de texto e desenha o fundo e o contorno
            text_area_x, text_area_y = 8, 38
            text_area_w, text_area_h = self.display.width - 16, 180
            self.display.fill_rect(text_area_x, text_area_y, text_area_w, text_area_h, INPUT_BG_COLOR)
            self.display.rect(text_area_x, text_area_y, text_area_w, text_area_h, TEXT_COLOR)
            
            # Desenha o texto do evento dentro da caixa
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if i > 17: break # Limita linhas visíveis para caber na caixa
                self.display.text(font, line, text_area_x + 5, text_area_y + 5 + i * (font.HEIGHT + 2), TEXT_COLOR, INPUT_BG_COLOR)

            # Desenha botões
            save_color = HIGHLIGHT_COLOR if editor_focus == 'save_button' else TEXT_COLOR
            del_color = HIGHLIGHT_COLOR if editor_focus == 'delete_button' else TEXT_COLOR
            self.display.text(font, "[ Salvar ]", 10, 225, save_color, BG_COLOR)
            self.display.text(font, "[ Apagar ]", 120, 225, del_color, BG_COLOR)
            
            # --- Loop Interno: Aguarda entrada ---
            while True:
                key = self.get_key_simple()
                direction, click = self.trackball.get_direction()

                # Processa teclado (edição de texto)
                if key:
                    if key == b'\r': content += '\n'
                    elif key == b'\x08': content = content[:-1]
                    else:
                        try: content += key.decode('utf-8')
                        except UnicodeError: pass
                    self.sound.play_keypress()
                    break # Quebra para redesenhar o texto

                # Processa navegação do trackball
                if direction:
                    if direction in ['left', 'right']:
                        editor_focus = 'delete_button' if editor_focus == 'save_button' else 'save_button'
                        self.sound.play_navigation()
                        break # Quebra para redesenhar o foco

                # Processa cliques do trackball
                if click:
                    if editor_focus == 'save_button':
                        self.sound.play_confirm()
                        try:
                            with open(filepath, 'w') as f: f.write(content)
                        except OSError: pass
                        return # Sai da tela de edição
                    elif editor_focus == 'delete_button':
                        if self._confirm_delete_ui():
                            try: _os.remove(filepath)
                            except OSError: pass
                            return # Sai da tela de edição
                        else:
                            break # Redesenha a tela se o usuário cancelou
                
                time.sleep_ms(20)

    def draw_calendar_ui(self):
        """Desenha a UI principal do calendário."""
        month_name = MONTH_NAMES[self.month]
        # Centraliza o cabeçalho e adiciona setas
        header_text = f"{month_name} {self.year}"
        header_x = (self.display.width - len(header_text) * font.WIDTH) // 2
        self.draw_header("") # Limpa a tela
        self.display.text(font, "<<", 10, 10, TEXT_COLOR, BG_COLOR)
        self.display.text(font, ">>", self.display.width - 30, 10, TEXT_COLOR, BG_COLOR)
        self.display.text(font, header_text, header_x, 10, TEXT_COLOR, BG_COLOR)
        
        # Desenha os dias da semana
        for i, day_abbr in enumerate(DAY_ABBREVIATIONS):
            self.display.text(font, day_abbr, 15 + i * 45, 30, HEADER_COLOR, BG_COLOR)

        # Lógica de desenho do grid de dias
        first_day = self.first_day_of_month(self.year, self.month)
        days_count = self.days_in_month(self.year, self.month)
        
        day_num = 1
        for row in range(6):
            for col in range(7):
                if (row == 0 and col < first_day) or day_num > days_count:
                    continue
                
                x = 10 + col * 45
                y = 50 + row * 28
                
                is_focused = (self.focused_element == 'calendar' and day_num == self.selected_day)
                color = HIGHLIGHT_COLOR if is_focused else TEXT_COLOR
                
                self.display.text(font, f"{day_num:2}", x, y, color, BG_COLOR)
                
                # Desenha indicador de evento
                if self.events.get(day_num):
                    self.display.fill_circle(x + 8, y + 12, 2, EVENT_INDICATOR_COLOR)

                day_num += 1
        
        # Desenha o botão Sair
        is_exit_focused = (self.focused_element == 'exit')
        exit_color = HIGHLIGHT_COLOR if is_exit_focused else TEXT_COLOR
        self.display.text(font, "[ Sair ]", 10, 225, exit_color, BG_COLOR)

    def run(self):
        """Loop principal do aplicativo."""
        self.load_events_for_month()

        while True:
            self.draw_calendar_ui()
            
            while True:
                key = self.get_key_simple()
                direction, click = self.trackball.get_direction()

                # --- Processa a navegação e ações ---
                if key:
                    if key == b'a' or key == b'A': # Mês anterior
                        self.month -= 1 # type: ignore
                        if self.month < 1:
                            self.month = 12
                            self.year -= 1
                        self.load_events_for_month()
                        break
                    elif key == b'd' or key == b'D': # Próximo mês
                        self.month += 1
                        if self.month > 12: # type: ignore
                            self.month = 1
                            self.year += 1
                        self.load_events_for_month()
                        break

                if direction: # Navegação com o Trackball
                    if self.focused_element == 'calendar':
                        days_count = self.days_in_month(self.year, self.month)
                        if direction == 'up': self.selected_day = max(1, self.selected_day - 7)
                        elif direction == 'down':
                            self.selected_day += 7
                            if self.selected_day > days_count:
                                self.focused_element = 'exit' # Vai para o botão Sair
                        elif direction == 'left':
                            self.selected_day = max(1, self.selected_day - 1)
                        elif direction == 'right':
                            self.selected_day = min(days_count, self.selected_day + 1)
                    elif self.focused_element == 'exit':
                        if direction == 'up': self.focused_element = 'calendar' # Volta para o calendário
                    
                    self.sound.play_navigation()
                    break # Quebra para redesenhar a seleção

                if click:
                    if self.focused_element == 'calendar':
                        self.sound.play_confirm()
                        self.edit_event_ui(self.year, self.month, self.selected_day)
                        self.load_events_for_month() # Recarrega eventos caso um novo tenha sido criado
                        break
                    elif self.focused_element == 'exit':
                        return # Fecha o app
                
                time.sleep_ms(50)

# --- Ponto de Entrada do App ---
try:
    app = CalendarApp(display, touch, trackball, i2c, sound)
    app.run()
except Exception as e:
    _display = globals().get('display')
    if _display:
        _display.fill(st7789.RED)
        _display.text(font, "ERRO NO APP", 10, 10, st7789.WHITE, st7789.RED)
        try:
            _display.text(font, str(e)[:35], 10, 30, st7789.WHITE, st7789.RED)
        except: pass
        time.sleep(5)
