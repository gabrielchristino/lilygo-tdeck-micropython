# upload.py - Script para automatizar o upload de arquivos para o T-Deck

import os
import subprocess

# --- Configuração ---
# Caminho para a raiz do seu projeto local
LOCAL_PROJECT_PATH = '.' 

# Diretórios a serem escaneados
LIB_DIR = 'lib'
UPDATE_STAGE_DIR = 'update_stage'

# --- Funções ---

def run_command(command, ignore_not_found=False):
    """Executa um comando no terminal e imprime a saída."""
    print(f"Executando: {' '.join(command)}")
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(f"Erro: {result.stderr}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Falha ao executar comando: {e}")
        print(f"Saída de erro:\n{e.stderr}")
        # Se a flag ignore_not_found for True e o erro for "No such file or directory",
        # consideramos que não é uma falha real e retornamos True.
        if ignore_not_found and "No such file or directory" in e.stderr:
            print("Info: O arquivo/diretório não existia, o que é esperado. Continuando...")
            return True
        return False
    except FileNotFoundError:
        print("Erro: 'mpremote' não encontrado. Certifique-se de que ele está instalado e no seu PATH.")
        return False

def discover_files():
    """Descobre arquivos e apps no projeto para apresentar no menu."""
    items = []
    
    # 1. Adiciona main.py
    if os.path.exists(os.path.join(LOCAL_PROJECT_PATH, 'main.py')):
        items.append({
            'name': 'main.py',
            'type': 'file',
            'local_path': 'main.py',
            'remote_path': 'main.py'
        })

    # 2. Adiciona arquivos da pasta lib/
    lib_path = os.path.join(LOCAL_PROJECT_PATH, LIB_DIR)
    if os.path.isdir(lib_path):
        for filename in os.listdir(lib_path):
            if filename.endswith('.py'):
                items.append({
                    'name': f'lib/{filename}',
                    'type': 'file',
                    'local_path': os.path.join(LIB_DIR, filename),
                    'remote_path': f'lib/{filename}'
                })

    # 3. Adiciona apps da pasta update_stage/
    update_stage_path = os.path.join(LOCAL_PROJECT_PATH, UPDATE_STAGE_DIR)
    if os.path.isdir(update_stage_path):
        for app_name in os.listdir(update_stage_path):
            if os.path.isdir(os.path.join(update_stage_path, app_name)):
                items.append({
                    'name': f'App: {app_name}',
                    'type': 'app',
                    'local_path': os.path.join(UPDATE_STAGE_DIR, app_name),
                    'remote_path': f'update_stage/{app_name}'
                })
    
    return items

def upload_item(item):
    """Faz o upload de um único item (arquivo ou app) para o dispositivo."""
    if item['type'] == 'file':
        # Comando para copiar um arquivo: mpremote cp local/arquivo.py :remoto/arquivo.py
        command = ['mpremote', 'cp', item['local_path'], f":{item['remote_path']}"]
        return run_command(command)
    
    elif item['type'] == 'app':
        # Para um app, primeiro garantimos que o diretório de staging exista no dispositivo
        print(f"Preparando para subir o app '{item['name']}'...")
        run_command(['mpremote', 'fs', 'mkdir', 'update_stage'])
        
        # Depois, removemos a versão antiga do app no staging, se existir
        run_command(['mpremote', 'fs', 'rm', '-r', f":{item['remote_path']}"], ignore_not_found=True)
        
        # Finalmente, copiamos a pasta inteira do app
        # Comando: mpremote cp -r local/pasta/app :remoto/pasta/app
        command = ['mpremote', 'cp', '-r', item['local_path'], f":{item['remote_path']}"]
        return run_command(command)
    
    return False

# --- Execução Principal ---
if __name__ == "__main__":
    print("--- Script de Upload para T-Deck ---")
    
    upload_items = discover_files()
    if not upload_items:
        print("Nenhum arquivo ou app encontrado para upload.")
        exit()

    while True:
        print("\nArquivos e Apps disponíveis para atualização:")
        for i, item in enumerate(upload_items):
            print(f"  {i+1:2d}) {item['name']}")
        print("   0) Sair")
        print("  'all') Atualizar tudo")

        try:
            choice_str = input("\nDigite o(s) número(s) do(s) item(ns) para atualizar (separados por espaço), ou 'all': ").strip().lower()
            
            if choice_str == '0':
                break
            
            selected_indices = []
            if choice_str == 'all':
                selected_indices = list(range(len(upload_items)))
            else:
                selected_indices = [int(x) - 1 for x in choice_str.split()]

            success_count = 0
            fail_count = 0
            
            for index in selected_indices:
                if 0 <= index < len(upload_items):
                    item_to_upload = upload_items[index]
                    print("-" * 30)
                    if upload_item(item_to_upload):
                        success_count += 1
                    else:
                        fail_count += 1
                else:
                    print(f"Índice inválido: {index + 1}")
                    fail_count += 1
            
            print("-" * 30)
            print(f"Resumo: {success_count} item(ns) atualizado(s) com sucesso, {fail_count} falha(s).")
            
            # Após o upload de apps, o dispositivo precisa ser reiniciado
            if any(upload_items[i]['type'] == 'app' for i in selected_indices if 0 <= i < len(upload_items)):
                print("\nATENÇÃO: Um ou mais aplicativos foram atualizados.")
                print("O dispositivo precisa ser reiniciado para que o processo de atualização interno seja executado.")
                reboot_choice = input("Deseja reiniciar o dispositivo agora? (s/n): ").strip().lower()
                if reboot_choice == 's':
                    run_command(['mpremote', 'reset'])
            
            break # Sai do loop após a tentativa de upload

        except ValueError:
            print("Entrada inválida. Por favor, digite números separados por espaço.")
        except Exception as e:
            print(f"Ocorreu um erro inesperado: {e}")
            break

    print("\nScript finalizado.")
