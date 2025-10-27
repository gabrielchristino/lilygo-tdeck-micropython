# /home/gabriel/Documents/tdeck/teste base/main.py

import time
from romfonts import vga1_8x8 as font
from lib.hardware_init import init_hardware
from lib.keyboard import get_key
from lib.ui_manager import UIManager
import st7789py as st7789

# --- Inicialização ---
display, touch, i2c, kbd_int = init_hardware()

# --- Configura UI Manager ---
ui_manager = UIManager(display, touch, i2c, font)

# Adiciona campos de entrada
ui_manager.add_text_input(
    x=40, y=50, w=240, h=40,
    placeholder="Digite seu nome...",
    bg_color=st7789.color565(66, 66, 66),
    text_color=st7789.WHITE
)

ui_manager.add_numeric_input(
    x=40, y=120, w=240, h=40,
    placeholder="Digite sua idade...",
    bg_color=st7789.color565(66, 66, 66),
    text_color=st7789.WHITE
)

# --- Loop Principal ---
while True:
    # Processa eventos de toque
    ui_manager.handle_touch()

    # Processa entrada do teclado
    ui_manager.handle_keyboard(get_key)

    time.sleep_ms(20)  # Pequeno delay para não sobrecarregar a CPU
