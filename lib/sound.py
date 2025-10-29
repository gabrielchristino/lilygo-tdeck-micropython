"""Sound effects module for T-Deck"""

from machine import Pin, I2S
import os as _os
import math
import struct

SOUND_CONFIG_FILE = '/sd/config/sound.conf'

class SoundManager:
    def __init__(self):
        self.volume_level = 3 # Nível padrão (0-4), 0 é mudo
        self._load_volume()

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

    def _load_volume(self):
        """Carrega o nível de volume salvo no arquivo de configuração."""
        try:
            with open(SOUND_CONFIG_FILE, 'r') as f:
                level = int(f.read().strip())
                if 0 <= level <= 4:
                    self.volume_level = level
        except (OSError, ValueError):
            # Se o arquivo não existe ou tem valor inválido, usa o padrão e salva.
            self.set_volume(self.volume_level)

    def set_volume(self, level):
        """Define e salva o nível de volume (0=mudo, 1-4=níveis)."""
        if not (0 <= level <= 4):
            return

        self.volume_level = level
        try:
            # Garante que o diretório /sd/config exista
            try: _os.mkdir('/sd/config')
            except OSError: pass
            
            with open(SOUND_CONFIG_FILE, 'w') as f:
                f.write(str(self.volume_level))
        except OSError as e:
            print(f"Erro ao salvar config de som: {e}")

    def make_tone(self, rate, bits, frequency):
        """Create a buffer containing the pure tone samples"""
        samples_per_cycle = rate // frequency
        sample_size_in_bytes = bits // 8
        samples = bytearray(samples_per_cycle * sample_size_in_bytes)
        # Mapeia o nível de volume para um fator de redução (quanto menor, mais alto o som)
        volume_map = [0, 32, 16, 8, 4] # 0:mudo, 1:baixo, 2:médio, 3:alto, 4:máximo
        volume_reduction_factor = volume_map[self.volume_level]
        range_val = pow(2, bits) // 2 // volume_reduction_factor

        if bits == 16:
            format_str = "<h"
        else:  # assume 32 bits
            format_str = "<l"

        for i in range(samples_per_cycle):
            sample = range_val + int((range_val - 1) * math.sin(2 * math.pi * i / samples_per_cycle))
            struct.pack_into(format_str, samples, i * sample_size_in_bytes, sample)

        return samples

    def play_touch_select(self):
        """Play sound for touch field selection - low, pleasant tone"""
        if self.volume_level == 0: return
        click = self.make_tone(self.SAMPLE_RATE_IN_HZ, self.SAMPLE_SIZE_IN_BITS, 330)  # Lower tone (E4)
        tone = bytearray()

        for i in range(60):  # Medium length
            tone = tone + click

        self.i2s.write(tone)

    def play_navigation(self):
        """Play sound for navigation (trackball movement) - quick, high-pitched beep"""
        if self.volume_level == 0: return
        click = self.make_tone(self.SAMPLE_RATE_IN_HZ, self.SAMPLE_SIZE_IN_BITS, 880)  # High tone (A5)
        tone = bytearray()

        for i in range(15):  # Very short
            tone = tone + click

        self.i2s.write(tone)

    def play_keypress(self):
        """Play sound for key press - crisp, short click"""
        if self.volume_level == 0: return
        click = self.make_tone(self.SAMPLE_RATE_IN_HZ, self.SAMPLE_SIZE_IN_BITS, 660)  # Medium-high (E5)
        tone = bytearray()

        for i in range(25):  # Short
            tone = tone + click

        self.i2s.write(tone)

    def play_confirm(self):
        """Play sound for confirmation (Enter/trackball click) - satisfying, two-tone"""
        if self.volume_level == 0: return
        # First tone
        click1 = self.make_tone(self.SAMPLE_RATE_IN_HZ, self.SAMPLE_SIZE_IN_BITS, 523)  # C5
        tone = bytearray()
        for i in range(40):
            tone = tone + click1

        # Second tone (higher)
        click2 = self.make_tone(self.SAMPLE_RATE_IN_HZ, self.SAMPLE_SIZE_IN_BITS, 659)  # E5
        for i in range(40):
            tone = tone + click2

        self.i2s.write(tone)

    def play_click(self):
        """Legacy method - now uses play_confirm for backward compatibility"""
        self.play_confirm()
