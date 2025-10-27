# /home/gabriel/Documents/tdeck/teste base/main.py

import machine
import time
import tft_config as tft
import st7789py as st7789
from romfonts import vga1_8x8 as font
from lib.material_components import TextInput, NumericInput
from lib.touch import Touch # A classe Touch ainda é necessária para os tipos de evento

# --- Inicialização ---
# 1. Inicializa o display
display = tft.config()
display.fill(st7789.color565(30, 30, 30)) # Fundo cinza escuro

# 2. Inicializa I2C, Teclado e Touch

# Pinos do teclado e I2C
KBD_INT_PIN = 46
KBD_I2C_ADDR = 0x55
I2C_SCL_PIN = 8
I2C_SDA_PIN = 18
I2C_FREQ = 400000

# Habilita a alimentação dos periféricos (teclado e touch)
machine.Pin(tft.PERIPHERAL_PIN, machine.Pin.OUT, value=1)
time.sleep(0.2)

# Cria uma única instância I2C para ser compartilhada
i2c = machine.SoftI2C(scl=machine.Pin(I2C_SCL_PIN), sda=machine.Pin(I2C_SDA_PIN), freq=I2C_FREQ)

# Inicializa o touch, passando a instância I2C
touch = tft.config_touch(i2c)

# Configura o pino de interrupção do teclado
kbd_int = machine.Pin(KBD_INT_PIN, machine.Pin.IN)

def get_key():
    """Lê um caractere do teclado via I2C."""
    try:
        key = i2c.readfrom(KBD_I2C_ADDR, 1)
        if key != b'\x00':
            print(f"Key read: {key}")  # Debug: mostra tecla lida
            return key
    except OSError as e:
        print(f"Erro ao ler do teclado I2C: {e}")
    return None

print("Display, Touch e Teclado inicializados.")

# --- Desenha a UI ---
text_input = TextInput(
    x=40, y=50, w=240, h=40,
    placeholder="Digite seu nome...",
    bg_color=st7789.color565(66, 66, 66),
    text_color=st7789.WHITE,
    font=font,
).draw(display)

numeric_input = NumericInput(
    x=40, y=120, w=240, h=40,
    placeholder="Digite sua idade...",
    bg_color=st7789.color565(66, 66, 66),
    text_color=st7789.WHITE,
    font=font,
).draw(display)

# Lista de campos de entrada para gerenciar o foco
inputs = [text_input, numeric_input]
focused_input = None

# --- Loop Principal ---
while True:
    # 1. Processa eventos de toque para dar foco aos campos
    event_type, x, y = touch.read()

    if event_type == Touch.TAP:
        new_focus = None
        for inp in inputs:
            # O método is_touched já existe na classe base InputBase
            if inp.is_touched((x, y)):
                new_focus = inp
                break
        
        # Gerencia a mudança de foco e redesenha os campos
        if new_focus != focused_input:
            if focused_input:
                focused_input.focused = False
                focused_input.draw(display) # Redesenha sem a borda de foco
            
            if new_focus:
                new_focus.focused = True
                new_focus.draw(display) # Redesenha com a borda de foco
            
            focused_input = new_focus

    # 2. Processa a entrada do teclado se um campo estiver focado
    if focused_input:
        key = get_key()
        if key:
            # handle_key retorna True se o texto foi alterado
            if focused_input.handle_key(key):
                # Redesenha apenas o texto do campo para ser mais rápido
                focused_input.draw_text(display)
                print(f"Campo '{focused_input.placeholder}' atualizado: '{focused_input.value}'")
            elif key == b'\r': # Tecla Enter
                print(f"Valor final do campo '{focused_input.placeholder}': {focused_input.value}")

    time.sleep_ms(20) # Pequeno delay para não sobrecarregar a CPU


     import utime
# import sound
# import time


# #utime.sleep(2)
# history_buf=[]
# cmd_buf=bytearray()

# print("Keyboard ready ..\n")
# MAX_WIDTH = 318
# MAX_HEIGHT = 238
# RSSI=0

# #clean input line 40 spaces
# clean_input = '{: <40}'.format("")

# bat = machine.ADC(machine.Pin(4))
# bat.width(machine.ADC.WIDTH_12BIT)
# bat.atten(machine.ADC.ATTN_11DB)

# bat_time_update=time.ticks_add(time.ticks_ms(), 1000)

# kbd_pwr = machine.Pin(10, machine.Pin.OUT)
# kbd_int = machine.Pin(46, machine.Pin.IN)
# i2c = machine.SoftI2C(scl=machine.Pin(8), sda=machine.Pin(18), freq=400000, timeout=50000)


# def do_connect():
#     import network
#     sta_if = network.WLAN(network.STA_IF)
#     if not sta_if.