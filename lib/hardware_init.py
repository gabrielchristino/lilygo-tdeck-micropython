"""
Módulo de Inicialização Centralizada de Hardware para o T-Deck.

Este script inicializa todos os componentes de hardware (display, I2C, touch,
trackball, som) uma única vez para evitar conflitos e uso excessivo de memória.
"""

import machine
import time
import tft_config as tft
from lib.touch import Touch
from lib.trackball import Trackball
from lib.sound import SoundManager

def init_hardware():
    """
    Inicializa todos os periféricos e retorna suas instâncias.
    Esta função deve ser chamada apenas uma vez no boot.
    """
    print("Inicializando hardware centralizado...")

    # Habilita a alimentação dos periféricos (teclado, touch)
    machine.Pin(tft.PERIPHERAL_PIN, machine.Pin.OUT, value=1)
    time.sleep(0.2)

    # Cria a instância do display. A função config() cuidará da sua própria inicialização SPI.
    display = tft.config()

    # Cria a instância compartilhada do barramento I2C
    i2c = machine.SoftI2C(scl=machine.Pin(8), sda=machine.Pin(18), freq=400000)

    # Inicializa os periféricos que usam I2C ou outros pinos
    touch = tft.config_touch(i2c)
    trackball = Trackball()
    sound = SoundManager()

    print("Hardware inicializado com sucesso.")

    return display, touch, trackball, i2c, sound