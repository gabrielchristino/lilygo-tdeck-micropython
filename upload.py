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

def run_command(command, ignore_not_found=False, ignore_exists=False):
    """Executa um comando no terminal e imprime a saída."""
    print(f"Executando: {' '.join(command)}")
    try:
        # Nota: Usamos check=True para levantar CalledProcessError em caso de falha.
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(f"Erro: {result.stderr}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Falha ao executar comando: {e}")
        print(f"Saída de erro:\n{e.stderr}")
        
        # 1. Tratamento para 'No such file or directory' (usado em 'rm -r')
        if ignore_not_found and "No such file or directory" in e.stderr:
            print("Info: O arquivo/diretório não existia, o que é esperado. Continuando...")
            return True
        
        # 2. Tratamento para 'File exists' (usado em 'mkdir')
        if ignore_exists and "File exists" in e.stderr:
            print("Info: O diretório já existia, o que é esperado. Continuando...")
            return True
            
        # Se for o erro persistente de -r, ainda falha e retorna False para a cópia
        # TODO: Se o problema de -r for resolvido, esta parte será executada
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
    
    # Padroniza para 'mpremote fs cp' para maior robustez
    if item['type'] == 'file':
        # Comando para copiar um arquivo: mpremote fs cp local/arquivo.py :remoto/arquivo.py
        command = ['mpremote', 'fs', 'cp', item['local_path'], f":{item['remote_path']}"]
        return run_command(command)
    
    elif item['type'] == 'app':
        # Para um app, primeiro garantimos que o diretório de staging exista no dispositivo
        print(f"Preparando para subir o app '{item['name']}'...")
        
        # 1. Cria o diretório de staging (agora usa ignore_exists=True para sucesso)
        # Se o comando falhar, mas for por 'File exists', ele retorna True e continua.
        if not run_command(['mpremote', 'fs', 'mkdir', 'update_stage'], ignore_exists=True):
            print("Erro fatal ao tentar criar ou verificar o diretório 'update_stage' remoto.")
            return False

        # 2. Removemos a versão antiga do app no staging, se existir (ignora 'No such file')
        run_command(['mpremote', 'fs', 'rm', '-r', f":{item['remote_path']}"], ignore_not_found=True)
        
        # 3. Garantimos que o diretório do app exista no dispositivo antes de copiar o conteúdo
        run_command(['mpremote', 'fs', 'mkdir', f":{item['remote_path']}"], ignore_exists=True)
        
        # 4. Copiamos o CONTEÚDO da pasta do app (solução robusta sem depender do shell)
        local_dir = item['local_path'] # Ex: 'update_stage/sketch'
        remote_dir = f":{item['remote_path']}" # Ex: ':update_stage/sketch'

        # Lista todos os itens dentro do diretório local
        local_items_to_copy = os.listdir(local_dir)

        # Constrói a lista de caminhos de ORIGEM
        sources = [os.path.join(local_dir, f) for f in local_items_to_copy]

        # O DESTINO é sempre o último argumento
        destination = [remote_dir]

        # O comando completo será: mpremote fs cp -r [sources...] [destination]
        # Note que a flag '-r' ainda é necessária se houver subdiretórios no app!
        command = ['mpremote', 'fs', 'cp', '-r'] + sources + destination

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
            
            # Verifica se um reboot é necessário (upload de app ou do launcher)
            uploaded_an_app = any(upload_items[i]['type'] == 'app' for i in selected_indices if 0 <= i < len(upload_items))
            uploaded_launcher = any(upload_items[i]['name'] == 'lib/app_launcher.py' for i in selected_indices if 0 <= i < len(upload_items))

            if uploaded_an_app or uploaded_launcher:
                print("\nATENÇÃO:")
                if uploaded_an_app:
                    print("-> Um ou mais apps foram atualizados (requer reboot para instalar).")
                if uploaded_launcher:
                    print("-> O app_launcher.py foi atualizado (requer reboot para aplicar).")
                
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