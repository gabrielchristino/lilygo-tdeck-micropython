"""
Módulo de Inicialização Centralizada de Hardware para o T-Deck.

Este script inicializa todos os componentes de hardware (display, I2C, touch,
trackball, som) uma única vez para evitar conflitos e uso excessivo de memória.
"""

import machine
import time
import os as _os # Importa 'os' com um alias para evitar conflitos
import tft_config as tft
from lib.touch import Touch
from lib.trackball import Trackball
from lib.sound import SoundManager
from lib.sdcard import _SDCard

# Define const para otimização do MicroPython
try:
    from micropython import const
except ImportError:
    const = lambda x: x

# --- Constantes de Hardware Centralizadas ---
_DISPLAY_SPI_ID = const(1)
_DISPLAY_BAUDRATE = const(80_000_000)
_DISPLAY_SCK = const(40)
_DISPLAY_MOSI = const(41)
_DISPLAY_MISO = const(38)
_DISPLAY_CS = const(12)
_DISPLAY_DC = const(11)
_DISPLAY_BACKLIGHT = const(42)
_DISPLAY_RESET = const(None)
_DISPLAY_ROTATION = const(1)


def init_hardware():
    """
    Inicializa todos os periféricos e retorna suas instâncias.
    Esta função deve ser chamada apenas uma vez no boot.
    """
    print("Inicializando hardware centralizado...")

    # Habilita a alimentação dos periféricos (teclado, touch)
    machine.Pin(tft.PERIPHERAL_PIN, machine.Pin.OUT, value=1)
    time.sleep(0.2)

    # --- Criação do Barramento SPI Compartilhado ---
    # O barramento é criado uma única vez e compartilhado entre o display e o SD card.
    shared_spi = machine.SPI(_DISPLAY_SPI_ID,
                             baudrate=_DISPLAY_BAUDRATE,
                             sck=machine.Pin(_DISPLAY_SCK),
                             mosi=machine.Pin(_DISPLAY_MOSI),
                             miso=machine.Pin(_DISPLAY_MISO))

    # Cria a instância do display, passando o barramento SPI compartilhado
    display = tft.config(
        spi=shared_spi,
        dc_pin=_DISPLAY_DC,
        cs_pin=_DISPLAY_CS,
        bl_pin=_DISPLAY_BACKLIGHT
    )

    # Cria a instância compartilhada do barramento I2C
    i2c = machine.SoftI2C(scl=machine.Pin(8), sda=machine.Pin(18), freq=400000)

    # Inicializa os periféricos que usam I2C ou outros pinos
    touch = tft.config_touch(i2c)
    trackball = Trackball()
    sound = SoundManager()

    # Inicializa e monta o cartão SD
    try:
        cs = machine.Pin(39, machine.Pin.OUT)
        # Reutiliza o barramento SPI compartilhado
        sd = _SDCard(shared_spi, cs)
        _os.mount(sd, '/sd')
        print("SD card montado em /sd")
    except Exception as e:
        print(f"Erro ao montar SD card: {e}")

    print("Hardware inicializado com sucesso.")

    return display, touch, trackball, i2c, sound
