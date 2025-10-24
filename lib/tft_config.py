import machine
import st7789py as st7789
_DISPLAY_HEIGHT = const(240)
_DISPLAY_WIDTH = const(320)
_DISPLAY_SPI_ID = const(1)
_DISPLAY_BAUDRATE = const(80_000_000)
_DISPLAY_SCK = const(40)
_DISPLAY_MOSI = const(41)
_DISPLAY_MISO = const(38)
_DISPLAY_RESET = const(None)
_DISPLAY_CS = const(12)
_DISPLAY_DC = const(11)
_DISPLAY_BACKLIGHT = const(42)
_DISPLAY_ROTATION = const(1)
_PERIPHERAL = const(10)

def config():
    machine.Pin(_PERIPHERAL, machine.Pin.OUT, value=1)
    return st7789.ST7789(machine.SPI(
                _DISPLAY_SPI_ID,
                baudrate=_DISPLAY_BAUDRATE,
                sck=machine.Pin(_DISPLAY_SCK),
                mosi=machine.Pin(_DISPLAY_MOSI),
                miso=machine.Pin(_DISPLAY_MISO),
                ),
                _DISPLAY_HEIGHT,
                _DISPLAY_WIDTH,
                reset=_DISPLAY_RESET,
                dc=machine.Pin(_DISPLAY_DC, machine.Pin.OUT),
                cs=machine.Pin(_DISPLAY_CS, machine.Pin.OUT),
                backlight=machine.Pin(_DISPLAY_BACKLIGHT, machine.Pin.OUT),
                rotation=_DISPLAY_ROTATION)