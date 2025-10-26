# /lib/touch.py
# Driver do GT911 e detecção de gestos para MicroPython

import machine
import time

# Endereços de registradores do GT911
_GT911_I2C_ADDR = 0x5D
_GT911_READ_COORD_ADDR = 0x814E
_GT911_CONFIG_ADDR = 0x8047

class Touch:
    """
    Driver de Touch para o T-Deck (GT911) em MicroPython.

    Fornece funções para inicializar e ler eventos de toque, incluindo:
    - Toque rápido (Tap)
    - Toque longo (LongTap)
    - Arrastar (Drag)

    Após um arrasto, não dispara Tap/LongTap ao soltar.
    """

    # Tipos de Eventos
    NONE = 0
    TAP = 1
    LONG_TAP = 2
    DRAG = 3

    # --- Parâmetros de detecção de gestos ---
    LONG_TAP_THRESHOLD_MS = 2000  # ms para clique longo
    TOUCH_RELEASE_GRACE_MS = 100  # ms para considerar toque liberado
    DRAG_MIN_DIST_PX = 2          # pixels para detectar arrasto
    NOISE_FILTER_MS = 30          # ignora toques mais curtos que isso

    def __init__(self, i2c, int_pin=-1, rst_pin=-1, width=320, height=240, swap_xy=True, mirror_y=True):
        """
        Inicializa o driver de touch.
        :param i2c: Objeto I2C configurado (machine.I2C).
        :param int_pin: Pino de interrupção do touch.
        :param rst_pin: Pino de reset do touch (opcional).
        :param width: Largura da tela.
        :param height: Altura da tela.
        :param swap_xy: Inverter eixos X e Y.
        :param mirror_y: Espelhar eixo Y.
        """
        self.i2c = i2c
        self.width = width
        self.height = height
        self.swap_xy = swap_xy
        self.mirror_y = mirror_y

        if int_pin != -1:
            self.int_pin = machine.Pin(int_pin, machine.Pin.IN)
        if rst_pin != -1:
            self.rst_pin = machine.Pin(rst_pin, machine.Pin.OUT)
            # Realiza o ciclo de reset
            self.rst_pin.value(0)
            time.sleep_ms(10)
            self.rst_pin.value(1)
            time.sleep_ms(50)

        # Estado da máquina de gestos
        self._touch_down = False
        self._touch_down_time = 0
        self._last_seen_touch_time = 0
        self._prev_x, self._prev_y = -1, -1
        self._last_touch_x, self._last_touch_y = 0, 0
        self._was_dragging = False

    def _write_reg(self, reg, value):
        """Escreve um byte em um registrador de 16 bits."""
        self.i2c.writeto_mem(_GT911_I2C_ADDR, reg, bytes([value]), addrsize=16)

    def _read_reg(self, reg, nbytes=1):
        """Lê bytes de um registrador de 16 bits."""
        return self.i2c.readfrom_mem(_GT911_I2C_ADDR, reg, nbytes, addrsize=16)

    def read(self):
        """
        Lê o estado do touch e retorna um evento:
        - (Touch.DRAG, x, y): enquanto arrastando
        - (Touch.TAP, x, y): clique rápido
        - (Touch.LONG_TAP, x, y): clique longo
        - (Touch.NONE, 0, 0): nenhum evento novo
        """
        status_byte = self._read_reg(_GT911_READ_COORD_ADDR, 1)[0]
        
        # Limpa o buffer de status para a próxima leitura
        self._write_reg(_GT911_READ_COORD_ADDR, 0)

        now_pressed = (status_byte & 0x80) != 0
        num_points = status_byte & 0x0F

        if now_pressed and num_points > 0:
            # Lê apenas o primeiro ponto de toque (8 bytes)
            data = self._read_reg(_GT911_READ_COORD_ADDR + 1, 8)
            x = (data[2] << 8) | data[1]
            y = (data[4] << 8) | data[3]

            # Aplica transformações de coordenada
            if self.swap_xy:
                x, y = y, x
            if self.mirror_y:
                y = self.height - 1 - y
            
            self._last_touch_x = x
            self._last_touch_y = y

            if not self._touch_down:
                # Primeiro toque detectado
                self._touch_down_time = time.ticks_ms()
                self._touch_down = True
                self._prev_x = x
                self._prev_y = y
                self._was_dragging = False
            else:
                # Toque continua, verifica se é um arrasto
                dist_x = abs(x - self._prev_x)
                dist_y = abs(y - self._prev_y)
                if dist_x > self.DRAG_MIN_DIST_PX or dist_y > self.DRAG_MIN_DIST_PX:
                    self._prev_x = x
                    self._prev_y = y
                    self._was_dragging = True
                    self._last_seen_touch_time = time.ticks_ms()
                    return (self.DRAG, x, y)
            
            self._last_seen_touch_time = time.ticks_ms()

        else: # Não está pressionado
            if self._touch_down and time.ticks_diff(time.ticks_ms(), self._last_seen_touch_time) > self.TOUCH_RELEASE_GRACE_MS:
                duration = time.ticks_diff(time.ticks_ms(), self._touch_down_time)
                self._touch_down = False
                self._prev_x, self._prev_y = -1, -1

                # Se estava arrastando, não gera evento de toque ao soltar
                if self._was_dragging:
                    self._was_dragging = False
                    return (self.NONE, 0, 0)

                # Verifica se foi toque longo ou rápido
                if duration >= self.LONG_TAP_THRESHOLD_MS:
                    return (self.LONG_TAP, self._last_touch_x, self._last_touch_y)
                elif duration > self.NOISE_FILTER_MS:
                    return (self.TAP, self._last_touch_x, self._last_touch_y)

        return (self.NONE, 0, 0)


# # /main.py

# import machine
# import time
# from lib.touch import Touch # Supondo que o arquivo acima foi salvo em /lib/touch.py

# # --- Configuração dos Pinos do T-Deck ---
# TDECK_I2C_SDA = 18
# TDECK_I2C_SCL = 8
# TDECK_TOUCH_INT = 16
# TDECK_PERI_POWERON = 10 # Pino que alimenta os periféricos

# # Habilita a alimentação dos periféricos
# power_pin = machine.Pin(TDECK_PERI_POWERON, machine.Pin.OUT)
# power_pin.on()
# time.sleep_ms(200) # Aguarda a estabilização

# print("Inicializando I2C e Touch...")

# # Inicializa o barramento I2C
# i2c = machine.SoftI2C(scl=machine.Pin(TDECK_I2C_SCL), sda=machine.Pin(TDECK_I2C_SDA), freq=400000)

# # Cria a instância do driver de touch
# # As configurações de tela (320x240), swap_xy e mirror_y são baseadas no código C++
# touch = Touch(i2c, int_pin=TDECK_TOUCH_INT, width=320, height=240, swap_xy=True, mirror_y=True)

# print("Touch inicializado. Pronto para ler eventos.")

# # Loop principal para ler e processar eventos de toque
# while True:
#     event_type, x, y = touch.read()

#     if event_type == Touch.TAP:
#         print(f"Toque Rápido (Tap) em: ({x}, {y})")
#         # Aqui você pode, por exemplo, desenhar um botão ou abrir um menu
        
#     elif event_type == Touch.LONG_TAP:
#         print(f"Toque Longo (LongTap) em: ({x}, {y})")
#         # Ideal para abrir um menu de contexto ou uma ação secundária
        
#     elif event_type == Touch.DRAG:
#         print(f"Arrastando (Drag) para: ({x}, {y})")
#         # Útil para barras de rolagem, sliders ou mover objetos na tela
    
#     # Pequeno delay para não sobrecarregar a CPU
#     time.sleep_ms(20)

