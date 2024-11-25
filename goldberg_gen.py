import os
import shutil
import subprocess
import tkinter as tk
import concurrent.futures
from tkinter import filedialog
from curl_cffi import requests

# Supress subprocess window
startupinfo = subprocess.STARTUPINFO()
startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
startupinfo.wShowWindow = subprocess.SW_HIDE

SEVENZIP_PATH = os.path.join("assets", "7zip", "7z.exe")
GOLDBERG_URL = "https://github.com/Detanup01/gbe_fork/releases/latest/download/emu-win-release.7z"
EMU_FOLDER = os.path.join("assets", "goldberg_emu")
ARCHIVE_NAME = "emu-win-release.7z"

# Debug
# print(f"EMU Dir: {EMU_FOLDER}")
# print(f"7z Path: {SEVENZIP_PATH}")

# Setting-Up Latest Emulator
def download_goldberg():
    os.makedirs(EMU_FOLDER, exist_ok=True)
    archive_path = os.path.join(EMU_FOLDER, ARCHIVE_NAME)
    
    if os.path.exists(archive_path):
        return archive_path
    
    print("Downloading Goldberg emulator...")
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.5 Safari/605.1.15"}
    
    try:
        with requests.Session(headers=headers) as session:
            response = session.get(GOLDBERG_URL)
            response.raise_for_status()
            
            with open(archive_path, 'wb') as f:
                f.write(response.content)
        
        print("Download completed successfully.")
        return archive_path
    except Exception as e:
        print(f"Failed to download Goldberg emulator: {str(e)}")
        raise

def extract_archive(archive_path):
    try:
        cmd = [SEVENZIP_PATH, 'x', f'-o{EMU_FOLDER}', '-y', archive_path]
        subprocess.run(cmd, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
        
        os.remove(archive_path)
        print("Extraction completed.")
        
    except Exception as e:
        print(f"Failed to extract archive: {str(e)}")
        raise

def find_exp_dir():
    for root, dirs, _ in os.walk(EMU_FOLDER):
        if "experimental" in dirs:
            return os.path.join(root, "experimental")

def find_tools_dir():
    for root, dirs, _ in os.walk(EMU_FOLDER):
        if "tools" in dirs:
            tools_dir = os.path.join(root, "tools")
            if "generate_interfaces" in os.listdir(tools_dir):
                return os.path.join(tools_dir, "generate_interfaces")

# dll selection dialogue
def select_steam_api_dll():
    root = tk.Tk()
    root.withdraw()
    
    file_path = filedialog.askopenfilename(
        title="Select steam_api.dll or steam_api64.dll of the Game",
        filetypes=[("path to steam_api(64).dll", "steam_api*.dll")]
    )
    
    if not file_path:
        print("No file selected.")
        return None
    
    filename = os.path.basename(file_path).lower()
    if filename not in ['steam_api.dll', 'steam_api64.dll']:
        print("Invalid file selected. Please select steam_api.dll or steam_api64.dll")
        return None
    
    return file_path

# Setting-Up game dir with required files
def setup_game_dir(game_dir, app_id, dll_path, disable_overlay):
    # Create steam_settings
    settings_dir = os.path.join(game_dir, "steam_settings")
    os.makedirs(settings_dir, exist_ok=True)
    
    dll_name = os.path.basename(dll_path).lower()
    experimental_path = find_exp_dir()
    source_path = os.path.join(experimental_path, "x64" if dll_name == "steam_api64.dll" else "x32")
    
    for file in os.listdir(source_path):
        src_file = os.path.join(source_path, file)
        dst_file = os.path.join(game_dir, file)
        if os.path.isfile(src_file):
            shutil.copy2(src_file, dst_file)
    
    backup_dll_name = f"{dll_name}.o"
    backup_dll_path = os.path.join(game_dir, backup_dll_name)
    shutil.copy2(dll_path, backup_dll_path)
    
    appid_path = os.path.join(settings_dir, "steam_appid.txt")
    with open(appid_path, "w") as f:
        f.write(str(app_id))

    interfaces_path = generate_interfaces(dll_path)
    settings_interfaces_path = os.path.join(settings_dir, "steam_interfaces.txt")
    shutil.move(interfaces_path, settings_interfaces_path)
    
    steam_settings_dir = os.path.join("assets", "steam_settings")
    if os.path.exists(steam_settings_dir):
        for folder in ['fonts', 'sounds']:
            src_folder = os.path.join(steam_settings_dir, folder)
            if os.path.exists(src_folder):
                dst_folder = os.path.join(settings_dir, folder)
                if os.path.exists(dst_folder):
                    shutil.rmtree(dst_folder)
                shutil.copytree(src_folder, dst_folder)
        
        # Handle overlay config
        overlay_src = os.path.join(steam_settings_dir, 'disabled.ini' if disable_overlay else 'enabled.ini')
        if os.path.exists(overlay_src):
            overlay_dst = os.path.join(settings_dir, 'configs.overlay.ini')
            shutil.copy2(overlay_src, overlay_dst)

    return game_dir

def generate_interfaces(dll_path):
    tools_dir = find_tools_dir()
    dll_name = os.path.basename(dll_path).lower()
    generator_exe = "generate_interfaces_x64.exe" if dll_name == "steam_api64.dll" else "generate_interfaces_x32.exe"
    generator_path = os.path.join(tools_dir, generator_exe)

    subprocess.run([generator_path, dll_path], capture_output=True, text=True, cwd=os.path.dirname(dll_path), creationflags=subprocess.CREATE_NO_WINDOW)
        
    interfaces_path = os.path.join(os.path.dirname(dll_path), "steam_interfaces.txt")
    return interfaces_path

# -------------- DLC generation --------------
def fetch_one_dlc(dlc_id):
    dlc_url = f"https://store.steampowered.com/api/appdetails/?filters=basic&appids={dlc_id}"

    try:
        dlc_response = requests.get(dlc_url, timeout=5)
        dlc_response.raise_for_status()
        dlc_data = dlc_response.json()
        
        if str(dlc_id) in dlc_data and dlc_data[str(dlc_id)].get('success'):
            dlc_name = dlc_data[str(dlc_id)].get('data', {}).get('name', f'DLC {dlc_id}')
            return (dlc_id, dlc_name)
        
    except Exception as e:
        print(f"Error fetching DLC {dlc_id}: {e}")

    return None

def fetch_dlc(app_id):
    base_url = f"https://store.steampowered.com/api/appdetails/?filters=basic&appids={app_id}"
    
    try:
        base_response = requests.get(base_url)
        base_response.raise_for_status()
        base_data = base_response.json()
        
        dlc_ids = base_data[str(app_id)].get('data', {}).get('dlc', [])
        if not dlc_ids:
            return {}
        
        print("Generating DLCs...")
        
        dlc_details = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(fetch_one_dlc, dlc_id) for dlc_id in dlc_ids]
            
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if result:
                    dlc_id, dlc_name = result
                    dlc_details[dlc_id] = dlc_name
        
        return dlc_details
    
    except Exception as e:
        print(f"Error fetching DLC details: {e}")
        return {}
    

def create_dlc_config(game_dir, dlc_details):
    if not dlc_details:
        return
    
    settings_dir = os.path.join(game_dir, "steam_settings")
    config_path = os.path.join(settings_dir, "configs.app.ini")
    
    with open(config_path, 'w', encoding='utf-8') as config_file:
        config_file.write("[app::dlcs]\n")
        config_file.write("unlock_all=0\n")
        
        for dlc_id, dlc_name in dlc_details.items():
            config_file.write(f"{dlc_id}={dlc_name}\n")
# -------------- END --------------

def generate_emu(game_dir, app_id, disable_overlay=False):
    try:
        if not os.path.exists(EMU_FOLDER) or not os.listdir(EMU_FOLDER):
            archive_path = download_goldberg()
            extract_archive(archive_path)
        
        dll_path = select_steam_api_dll()
        if not dll_path:
            return False
        
        game_folder = setup_game_dir(game_dir, app_id, dll_path, disable_overlay)
        
        dlc_details = fetch_dlc(app_id)
        create_dlc_config(game_folder, dlc_details)
        
        print("Files generated successfully!")
        print(f"Location: {(game_folder)}")
              
        return True
    
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return False
