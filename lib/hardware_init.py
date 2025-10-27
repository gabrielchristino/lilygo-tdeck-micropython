"""
Módulo de Inicialização Centralizada de Hardware para o T-Deck.

Este script inicializa todos os componentes de hardware (display, I2C, touch,
trackball, som) uma única vez para evitar conflitos e uso excessivo de memória.
"""

import machine
import time
import os
import tft_config as tft
from lib.touch import Touch
from lib.trackball import Trackball
from lib.sound import SoundManager
from lib.sdcard import _SDCard

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

    # Inicializa e monta o cartão SD
    try:
        spi = machine.SPI(1, baudrate=1000000, sck=machine.Pin(40), mosi=machine.Pin(41), miso=machine.Pin(38))
        cs = machine.Pin(39, machine.Pin.OUT)
        sd = _SDCard(spi, cs)
        os.mount(sd, '/sd')
        print("SD card montado em /sd")
    except Exception as e:
        print(f"Erro ao montar SD card: {e}")

    print("Hardware inicializado com sucesso.")

    return display, touch, trackball, i2c, sound
