"""Exemplo 1 - Aplicação de Demonstração"""

import time
import tft_config as tft
import st7789py as st7789
from romfonts import vga1_8x8 as font

# Os objetos de hardware (display, touch, etc.) são injetados como globais.
print("Executando Exemplo 1")

# Definir cores
BG_COLOR = st7789.color565(0, 100, 0)  # Verde
FG_COLOR = st7789.WHITE

display.fill(BG_COLOR)

# Desenhar texto
display.text(font, "EXEMPLO 1", 60, 60, FG_COLOR, BG_COLOR)
display.text(font, "Aplicacao carregada!", 20, 100, FG_COLOR, BG_COLOR)

# Aguardar 10 segundos antes de retornar ao launcher
time.sleep(10)
