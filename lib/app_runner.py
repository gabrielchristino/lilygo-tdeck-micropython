"""
App Runner Module

Executa aplicativos de forma isolada, gerenciando memória e o ciclo de vida.
Esta versão é projetada para funcionar com aplicativos baseados em classes,
garantindo um ambiente de execução limpo a cada vez.
"""

import gc
import sys
import time
import st7789py as st7789
from romfonts import vga1_8x8 as font

def run_app(app_path, hardware_globals):
    """
    Executa um aplicativo, garantindo um ambiente limpo.

    Args:
        app_path (str): O caminho para o arquivo __init__.py do aplicativo.
        hardware_globals (dict): Um dicionário contendo as instâncias de hardware
                                 (display, touch, etc.) para passar para o app.
    """
    display = hardware_globals.get('display')
    sound = hardware_globals.get('sound')

    # --- Etapa 1: Limpeza do ambiente ---
    # Converte o caminho do arquivo em um nome de módulo (ex: /sd/app/wifi -> app.wifi)
    # e remove-o do cache para forçar uma recarga completa.
    app_module_name = app_path.replace('/sd/', '').replace('/', '.').replace('.__init__', '').replace('.py', '')
    if app_module_name in sys.modules:
        del sys.modules[app_module_name]
        print(f"Módulo '{app_module_name}' removido do cache.")

    gc.collect()
    print(f"Memória livre antes de carregar o app: {gc.mem_free()} bytes")

    # --- Etapa 2: Execução do App ---
    try:
        if sound:
            sound.play_confirm()
        if display:
            display.fill(st7789.BLACK)
            display.text(font, "Carregando app...", 10, 100, st7789.WHITE, st7789.BLACK)

        # O app deve definir e instanciar uma classe 'App' e chamar seu método 'run'.
        # As variáveis em hardware_globals estarão disponíveis globalmente para o script.
        print(f"Executando script: {app_path}")
        exec(open(app_path).read(), hardware_globals)
        
        return True

    except Exception as e:
        print(f"!!! ERRO AO EXECUTAR APP '{app_path}': {e}")
        # Exibe uma tela de erro clara no display
        if display:
            display.fill(st7789.color565(100, 0, 0))  # Fundo vermelho escuro
            display.text(font, "ERRO NO APP", 20, 80, st7789.WHITE, st7789.color565(100, 0, 0))
            try:
                # Tenta exibir a mensagem de erro, limitada em tamanho
                display.text(font, str(e)[:35], 10, 110, st7789.WHITE, st7789.color565(100, 0, 0))
            except:
                pass # Evita que a exibição do erro cause outro erro
            time.sleep(5) # Pausa para o usuário ver o erro
        return False

    finally:
        # --- Etapa 3: Limpeza Pós-Execução ---
        # Garante que a memória seja liberada mesmo que o app falhe.
        gc.collect()
        print(f"App finalizado. Memória livre: {gc.mem_free()} bytes")

