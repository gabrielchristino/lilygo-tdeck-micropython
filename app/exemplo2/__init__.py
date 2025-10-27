"""Exemplo 2 - Aplicação Interativa"""

import time
import st7789py as st7789
from romfonts import vga1_8x8 as font
from lib.touch import Touch

# Os objetos de hardware (display, touch, etc.) são injetados como globais.
print("Executando Exemplo 2")

# O display e o touch são recebidos como argumentos, não inicializados aqui.
BG_COLOR = st7789.color565(0, 0, 100) # Azul
display.fill(BG_COLOR)
display.text(font, "EXEMPLO 2", 60, 60, st7789.WHITE, BG_COLOR)
display.text(font, "Toque para sair", 30, 100, st7789.WHITE, BG_COLOR)

# Loop até toque
while True:
    event_type, x, y = touch.read()
    if event_type == Touch.TAP:
        break
    time.sleep_ms(50)
