"""Main application - App Launcher"""

import time
import tft_config as tft
import st7789py as st7789
from romfonts import vga1_8x8 as font
from lib.app_launcher import AppLauncher
from lib.hardware_init import init_hardware

# --- Inicialização ---
print("Inicializando T-Deck...")
try:
    # Inicializa todo o hardware uma única vez
    display, touch, trackball, i2c, sound = init_hardware()
except Exception as e:
    print(f"Falha crítica na inicialização do hardware: {e}")
    # Loop infinito em caso de falha de hardware para evitar mais erros
    while True: time.sleep(1)

# --- Execução Principal ---
print("Iniciando launcher de apps...")
# Cria o launcher UMA ÚNICA VEZ, passando os objetos de hardware.
launcher = AppLauncher(display, touch, trackball, i2c, sound)

# Inicia o loop infinito do launcher. Ele agora gerencia o retorno dos apps.
launcher.run_launcher()
