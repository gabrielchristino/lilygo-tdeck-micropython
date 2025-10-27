"""
App Runner Module - Usa execfile para rodar apps.

Esta abordagem é mais robusta em termos de memória do que __import__.
"""

import gc
import time
import st7789py as st7789
from romfonts import vga1_8x8 as font

def run_app(app_path, hardware_globals):
    """
    Executa um aplicativo usando execfile.

    Args:
        app_path (str): O caminho para o arquivo __init__.py do aplicativo.
        hardware_globals (dict): Um dicionário contendo as instâncias de hardware
                                 (display, touch, etc.) para passar para o app.
    """
    display = hardware_globals['display']
    sound = hardware_globals['sound']

    try:
        sound.play_confirm()
        display.fill(st7789.BLACK)
        display.text(font, "Carregando app...", 10, 100, st7789.WHITE, st7789.BLACK)

        # Limpa a memória antes de executar o novo script
        gc.collect()

        # Cria um dicionário de globais para o script do app
        # Inclui os objetos de hardware e o próprio __name__
        app_globals = hardware_globals.copy()
        app_globals['__name__'] = '__main__'

        print(f"Executando script: {app_path}")
        exec(open(app_path).read(), app_globals)

        return True

    except Exception as e:
        print(f"Erro ao executar app {app_path}: {e}")
        display.fill(st7789.color565(100, 0, 0))  # Fundo vermelho
        display.text(font, "ERRO AO EXECUTAR APP", 20, 80, st7789.WHITE, st7789.color565(100, 0, 0))
        # Tenta exibir a mensagem de erro real
        try:
            display.text(font, str(e)[:35], 10, 110, st7789.WHITE, st7789.color565(100, 0, 0))
        except:
            pass
        time.sleep(4)
        return False