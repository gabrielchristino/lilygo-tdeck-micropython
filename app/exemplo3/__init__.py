"""Exemplo 3 - Aplicação com Contador"""

import time
import st7789py as st7789
from romfonts import vga1_8x8 as font

# Os objetos de hardware (display, touch, etc.) são injetados como globais.
print("Executando Exemplo 3")

# Definir cores para facilitar a leitura
BG_COLOR = st7789.color565(100, 0, 100)  # Magenta
FG_COLOR = st7789.WHITE
ACCENT_COLOR = st7789.YELLOW

display.fill(BG_COLOR)
display.text(font, "EXEMPLO 3", 60, 60, FG_COLOR, BG_COLOR)

contador = 0
# Exibe o texto inicial do contador
display.text(font, f"Cliques: {contador}", 30, 100, FG_COLOR, BG_COLOR)

while contador < 10:
    direction, click = trackball.get_direction()
    if click:
        contador += 1
        # Limpa a área do contador e redesenha o novo valor
        display.fill_rect(30, 100, 200, 20, BG_COLOR)
        display.text(font, f"Cliques: {contador}", 30, 100, FG_COLOR, BG_COLOR)
    time.sleep_ms(50)

display.text(font, "Fim!", 100, 130, ACCENT_COLOR, BG_COLOR)
time.sleep(2)
