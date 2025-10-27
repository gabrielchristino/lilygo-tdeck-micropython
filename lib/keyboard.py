"""Keyboard handling module for T-Deck"""

KBD_I2C_ADDR = 0x55

def get_key(i2c):
    """Lê um caractere do teclado via I2C."""
    try:
        key = i2c.readfrom(KBD_I2C_ADDR, 1)
        if key != b'\x00':
            return key
    except OSError as e:
        print(f"Erro ao ler do teclado I2C: {e}")
    return None
