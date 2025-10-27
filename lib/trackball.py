"""Trackball control module for T-Deck"""

from machine import Pin
import time

class Trackball:
    def __init__(self):
        # Trackball pins
        self.tb_up = Pin(3, mode=Pin.IN, pull=Pin.PULL_UP)
        self.tb_down = Pin(15, mode=Pin.IN, pull=Pin.PULL_UP)
        self.tb_left = Pin(1, mode=Pin.IN, pull=Pin.PULL_UP)
        self.tb_right = Pin(2, mode=Pin.IN, pull=Pin.PULL_UP)
        self.tb_click = Pin(0, mode=Pin.IN, pull=Pin.PULL_UP)

        # State variables
        self.tb_int = False
        self.tb_up_count = 1
        self.tb_down_count = 1
        self.tb_left_count = 1
        self.tb_right_count = 1
        self.tb_click_count = 0

        # Configure interrupts
        self.tb_up.irq(trigger=Pin.IRQ_FALLING, handler=self.button_isr)
        self.tb_down.irq(trigger=Pin.IRQ_FALLING, handler=self.button_isr)
        self.tb_left.irq(trigger=Pin.IRQ_FALLING, handler=self.button_isr)
        self.tb_right.irq(trigger=Pin.IRQ_FALLING, handler=self.button_isr)
        self.tb_click.irq(trigger=Pin.IRQ_FALLING, handler=self.button_isr)

        # Power on keyboard (shared with trackball)
        self.kbd_pwr = Pin(10, Pin.OUT)
        self.kbd_pwr.on()
        time.sleep(0.5)

    def button_isr(self, pin):
        """Interrupt handler for trackball buttons"""
        self.tb_int = True

        TRACK_SPEED = 4
        if pin == self.tb_up:
            self.tb_up_count <<= TRACK_SPEED
        if pin == self.tb_down:
            self.tb_down_count <<= TRACK_SPEED
        if pin == self.tb_left:
            self.tb_left_count <<= TRACK_SPEED
        if pin == self.tb_right:
            self.tb_right_count <<= TRACK_SPEED
        if pin == self.tb_click:
            self.tb_click_count += 1

    def get_direction(self):
        """Get the current trackball direction and reset counters"""
        if not self.tb_int:
            return None, False

        direction = None
        click = self.tb_click_count > 0

        # Determine primary direction (largest count)
        counts = {
            'up': self.tb_up_count,
            'down': self.tb_down_count,
            'left': self.tb_left_count,
            'right': self.tb_right_count
        }

        max_count = max(counts.values())
        if max_count > 1:  # Only consider if there's actual movement
            direction = max(counts, key=counts.get)

        # Reset state
        self.tb_int = False
        self.tb_up_count = 1
        self.tb_down_count = 1
        self.tb_left_count = 1
        self.tb_right_count = 1
        self.tb_click_count = 0

        return direction, click
