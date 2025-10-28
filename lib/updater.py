"""
App Updater Module

Handles updating apps on the SD card from a staging directory in internal flash.
"""
import os as _os # Importa 'os' com um alias para evitar conflitos
import gc
import st7789py as st7789

def delete_recursive(path):
    """Recursively delete a file or directory."""
    try:
        if _os.stat(path)[0] & 0x4000:  # Check if it's a directory
            for item in _os.listdir(path):
                delete_recursive(f"{path}/{item}")
            _os.rmdir(path)
        else:  # It's a file
            _os.remove(path)
        print(f"Deleted: {path}")
    except OSError as e:
        if e.args[0] == 2: # ENOENT - File/dir not found
            pass # It's okay if it doesn't exist
        else:
            print(f"Error deleting {path}: {e}")

def copy_recursive(source, dest, display, font):
    """Recursively copy a file or directory."""
    for item in _os.listdir(source):
        source_path = f"{source}/{item}"
        dest_path = f"{dest}/{item}"
        
        if _os.stat(source_path)[0] & 0x4000: # É um diretório
            print(f"Creating dir: {dest_path}")
            try:
                _os.mkdir(dest_path)
            except OSError:
                pass # Diretório provavelmente já existe
            copy_recursive(source_path, dest_path, display, font)
        else: # É um arquivo
            # Exibe o nome do arquivo sendo copiado
            display.fill_rect(10, 100, 300, 10, st7789.color565(0, 0, 20)) # Limpa a linha anterior
            display.text(font, f"Copiando: {item}", 10, 100, st7789.WHITE)
            print(f"Copying: {source_path} -> {dest_path}")
            with open(source_path, 'rb') as f_source, open(dest_path, 'wb') as f_dest:
                while True:
                    chunk = f_source.read(512)
                    if not chunk:
                        break
                    f_dest.write(chunk)

def run_update_process(display):
    """
    Main update process. Checks for content in /update_stage, and replaces apps on SD card.
    Returns True if an update was performed, False otherwise.
    """
    UPDATE_STAGE_DIR = '/update_stage'
    SD_APP_DIR = '/sd/app'
    
    try:
        # Verifica se o diretório de staging existe e não está vazio
        staged_items = _os.listdir(UPDATE_STAGE_DIR)
        if not staged_items:
            return False
    except OSError:
        # /update_stage não existe, não há atualização a fazer
        return False

    # --- Update process starts ---
    from romfonts import vga1_8x8 as font

    display.fill(st7789.color565(0, 0, 20))
    display.text(font, "Atualizacao encontrada...", 10, 10, st7789.WHITE)
    display.text(font, "Nao desligue o dispositivo.", 10, 30, st7789.YELLOW)

    try:
        # Verifica se o diretório /sd/app existe antes de continuar
        _os.stat(SD_APP_DIR)
    except OSError:
        display.text(font, "ERRO: Cartao SD nao encontrado!", 10, 60, st7789.RED)
        display.text(font, "Verifique o cartao e reinicie.", 10, 80, st7789.RED)
        # Limpa o staging para não tentar de novo no próximo boot
        delete_recursive(UPDATE_STAGE_DIR)
        return True # Retorna True para forçar a reinicialização no main.py

    try:
        for app_folder_name in staged_items:
            source_app_path = f"{UPDATE_STAGE_DIR}/{app_folder_name}"
            target_app_path = f"{SD_APP_DIR}/{app_folder_name}"

            display.text(font, f"Atualizando app: {app_folder_name}", 10, 60, st7789.WHITE)
            
            # 1. Remove a versão antiga no SD card
            display.text(font, "Removendo versao antiga...", 10, 80, st7789.WHITE)
            delete_recursive(target_app_path)
            gc.collect()

            # 2. Copia a nova versão do staging para o SD card
            _os.mkdir(target_app_path) # Cria a pasta base do app no SD
            copy_recursive(source_app_path, target_app_path, display, font)
            gc.collect()

        # 3. Limpa o diretório de staging
        display.text(font, "Finalizando...", 10, 100, st7789.WHITE)
        delete_recursive(UPDATE_STAGE_DIR)

        display.text(font, "Atualizacao concluida!", 10, 120, st7789.GREEN)
        display.text(font, "Reiniciando...", 10, 140, st7789.GREEN)
        
    except Exception as e:
        display.text(font, "ERRO NA ATUALIZACAO!", 10, 80, st7789.RED)
        display.text(font, str(e), 10, 100, st7789.RED)

    return True
