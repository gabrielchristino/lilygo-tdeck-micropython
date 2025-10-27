"""Sound effects module for T-Deck"""

from machine import Pin, I2S
import math
import struct

class SoundManager:
    def __init__(self):
        # Initialize I2S for audio output
        self.i2s = I2S(0,
                      sck=Pin(7),
                      ws=Pin(5),
                      sd=Pin(6),
                      mode=I2S.TX,
                      bits=16,
                      format=I2S.MONO,
                      rate=22050,
                      ibuf=40000)

        self.TONE_FREQUENCY_IN_HZ = 440
        self.SAMPLE_SIZE_IN_BITS = 16
        self.SAMPLE_RATE_IN_HZ = 22_050

    def make_tone(self, rate, bits, frequency):
        """Create a buffer containing the pure tone samples"""
        samples_per_cycle = rate // frequency
        sample_size_in_bytes = bits // 8
        samples = bytearray(samples_per_cycle * sample_size_in_bytes)
        volume_reduction_factor = 8  # volume!
        range_val = pow(2, bits) // 2 // volume_reduction_factor

        if bits == 16:
            format_str = "<h"
        else:  # assume 32 bits
            format_str = "<l"

        for i in range(samples_per_cycle):
            sample = range_val + int((range_val - 1) * math.sin(2 * math.pi * i / samples_per_cycle))
            struct.pack_into(format_str, samples, i * sample_size_in_bytes, sample)

        return samples

    def play_click(self):
        """Play a short click sound"""
        click = self.make_tone(self.SAMPLE_RATE_IN_HZ, self.SAMPLE_SIZE_IN_BITS, self.TONE_FREQUENCY_IN_HZ)
        tone = bytearray()

        for i in range(50):  # Shorter click sound
            tone = tone + click

        self.i2s.write(tone)

    def play_keypress(self):
        """Play sound for key press"""
        # Slightly different tone for key presses
        click = self.make_tone(self.SAMPLE_RATE_IN_HZ, self.SAMPLE_SIZE_IN_BITS, self.TONE_FREQUENCY_IN_HZ + 100)
        tone = bytearray()

        for i in range(30):  # Even shorter for key presses
            tone = tone + click

        self.i2s.write(tone)

    def play_navigation(self):
        """Play sound for navigation (trackball movement)"""
        # Higher pitched, shorter sound for navigation
        click = self.make_tone(self.SAMPLE_RATE_IN_HZ, self.SAMPLE_SIZE_IN_BITS, self.TONE_FREQUENCY_IN_HZ + 200)
        tone = bytearray()

        for i in range(20):  # Very short navigation sound
            tone = tone + click

        self.i2s.write(tone)
