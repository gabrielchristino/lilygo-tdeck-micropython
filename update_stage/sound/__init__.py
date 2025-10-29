"""
Sound App - Gerenciador de Volume para T-Deck

Permite ajustar o volume do sistema em 5 níveis.
"""

import time
import st7789py as st7789
from romfonts import vga1_8x8 as font

# --- Constantes ---
BG_COLOR = st7789.color565(20, 20, 30)
TEXT_COLOR = st7789.WHITE
BAR_COLOR = st7789.color565(80, 80, 100)
HIGHLIGHT_COLOR = st7789.CYAN

class SoundApp:
    def __init__(self, display, touch, trackball, i2c, sound):
        self.display = display
        self.trackball = trackball
        self.sound = sound
        
        # O nível de volume é carregado do SoundManager
        self.selected_level = self.sound.volume_level

    def draw_ui(self):
        """Desenha a interface de ajuste de volume."""
        self.display.fill(BG_COLOR)
        self.display.text(font, "Ajuste de Volume", 10, 10, TEXT_COLOR, BG_COLOR)
        
        # Nomes dos níveis
        level_names = ["Mudo", "Baixo", "Medio", "Alto", "Maximo"]
        
        # Desenha as 5 barras de volume
        for i in range(5):
            bar_width = 50 + (i * 40)
            bar_y = 60 + i * 30
            
            # Cor da barra e do texto
            color = HIGHLIGHT_COLOR if i == self.selected_level else BAR_COLOR
            text_color = HIGHLIGHT_COLOR if i == self.selected_level else TEXT_COLOR

            # Desenha a barra
            self.display.fill_rect(40, bar_y, bar_width, 20, color)
            
            # Desenha o nome do nível
            self.display.text(font, level_names[i], 45, bar_y + 6, TEXT_COLOR, color)

        self.display.text(font, "Clique para Salvar e Sair", 10, 220, TEXT_COLOR, BG_COLOR)

    def run(self):
        """Loop principal do aplicativo."""
        
        while True:
            self.draw_ui()
            
            # Loop de entrada
            while True:
                direction, click = self.trackball.get_direction()

                if direction:
                    old_level = self.selected_level
                    if direction == 'up':
                        self.selected_level = max(0, self.selected_level - 1)
                    elif direction == 'down':
                        self.selected_level = min(4, self.selected_level + 1)
                    
                    if self.selected_level != old_level:
                        # Toca um som de navegação no volume *novo* para dar feedback
                        self.sound.set_volume(self.selected_level)
                        self.sound.play_navigation()
                        break # Sai para redesenhar

                if click:
                    # Salva a configuração final e sai do app
                    self.sound.set_volume(self.selected_level)
                    self.sound.play_confirm()
                    time.sleep_ms(200) # Pequena pausa para o som tocar
                    return

                time.sleep_ms(50)

# --- Ponto de Entrada do App ---
try:
    app = SoundApp(display, touch, trackball, i2c, sound)
    app.run()
except Exception as e:
    _display = globals().get('display')
    if _display:
        _display.fill(st7789.RED)
        _display.text(font, "ERRO NO APP", 10, 10, st7789.WHITE, st7789.RED)
        _display.text(font, str(e)[:35], 10, 30, st7789.WHITE, st7789.RED)
        time.sleep(5)