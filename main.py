print("main")
import machine
import st7789py as st7789
import tft_config as tft
from romfonts import vga1_8x8 as font

from lib.material_components import Button
from lib.st7789py import ST7789, color565

# Setup display object as tft
tft = tft.config()
tft.fill(st7789.color565(128, 128, 128))


button1 = Button(
    x=50, y=50, w=140, h=40,
    text="Button 1",
    bg_color=color565(33, 150, 243),
    text_color=color565(255, 255, 255),
    font=font,
).draw(tft)

button2 = Button(
    x=50, y=100, w=140, h=40,
    text="Button 2",
    bg_color=color565(233, 30, 99),
    text_color=color565(255, 255, 255),
    font=font,
    border_radius=12,
).draw(tft)

button3 = Button(
    x=50, y=150, w=140, h=40,
    text="Button 3",
    bg_color=color565(76, 175, 80),
    text_color=color565(255, 255, 255),
    font=font,
    border_radius=0,
).draw(tft)


# import utime
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
#     if not sta_if.isconnected():
#         print('connecting to network...')
#         sta_if.active(True)
#         sta_if.connect('GTI-AP314', 'carsled100')
#         while not sta_if.isconnected():
#             pass
#     print('network config:', sta_if.ifconfig())


# def get_key():
#     ch = i2c.readfrom(0x55, 1)
#     #if ch != 0:
#     return ch


# def split_rows(input_string, row_delimiter='\r', chunk_size=40):
#     rows = input_string.split(row_delimiter)

#     for row in rows:
#         for i in range(0, len(row), chunk_size):
#             chunk = row[i:i+chunk_size]
#             history_buf.append(chunk)

#     if len(history_buf) > 11:
#         del history_buf[0:len(history_buf)-11]

#     # print(f"{history_buf=}")


# def chat_history(buf):
#     split_rows(buf.decode())

#     for txt in history_buf:

#         if txt[0:3] == 'me>':
#             tft.text(font, txt[0:3], 0, (history_buf.index(txt)+1)*16, st7789.GREEN, st7789.BLACK)
#             tft.text(font, txt[3:], 24, (history_buf.index(txt)+1)*16, st7789.WHITE, st7789.BLACK)
#         elif txt[0:4] == 'oth>':
#             tft.text(font, txt[0:4], 0, (history_buf.index(txt)+1)*16, st7789.RED, st7789.BLACK)
#             tft.text(font, txt[4:], 24, (history_buf.index(txt)+1)*16, st7789.WHITE, st7789.BLACK)
#         else:
#             tft.text(font, txt, 0, (history_buf.index(txt)+1)*16, st7789.WHITE, st7789.BLACK)


# def cmd_line(cmd_buf):
#     for rows in cmd_buf:
#         tft.text(font, cmd_buf.decode(), 40, 222, st7789.WHITE, st7789.BLACK)


# def draw_navbar(bat, rssi=0):
#     # draw navbar
#     for i in range(0,318,8):
#         tft.text(font, "-", i, 0, st7789.BLUE, st7789.BLUE)
#     tft.text(font, f"bat:{bat}V", 0, 0, st7789.WHITE, st7789.BLUE)
#     tft.text(font, f"rssi:{rssi}", 90, 0, st7789.WHITE, st7789.BLUE)


# def update_bat():
#     global bat_time_update
#     global RSSI
#     if time.ticks_diff(bat_time_update, time.ticks_ms()) < 0:
#         battery_voltage=((bat.read_u16() * 3.3) / 65535)/ (100/200)
#         #update every minute
#         bat_time_update = time.ticks_add(time.ticks_ms(), 60000)
#         draw_navbar(round(battery_voltage,2), RSSI)

# #enable keyboard
# kbd_pwr.on()
# utime.sleep(.5)


# #draw red delimiter line
# for i in range(0,318,8):
#     tft.text(font, "-", i, 206, st7789.BLUE, st7789.BLACK)

# while True:

#     update_bat()

#     a = get_key()

#     if a != b'\x00':
#         print(a)
#         # handle backspace
#         if a == b'\x08':
#             #delete last char including backspace byte
#             cmd_buf=cmd_buf[:-1]
#             tft.text(font, clean_input, 0, 222, st7789.BLACK, st7789.BLACK)
#             tft.text(font, cmd_buf.decode(), 0 , 222, st7789.BLACK, st7789.BLACK)
#         else:
#             cmd_buf +=a

#         if a == b'\r':
#             print("Sending...")
#             sound.click()
#             chat_history(b'me> '+ cmd_buf)
#             tft.text(font, clean_input, 0, 222, st7789.BLACK, st7789.BLACK)
#             cmd_buf=b''

#         cmd_line(cmd_buf)

# kbd_pwr.off()