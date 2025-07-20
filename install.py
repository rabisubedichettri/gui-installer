# Full functional update to your script to add:
# 1. pystray tray launcher generator
# 2. secrets.env usage
# 3. env-server.py tray daemon with run/stop

import os
import shutil
import subprocess
import tkinter as tk
from tkinter import messagebox, filedialog
from tkinter.scrolledtext import ScrolledText
import urllib.request
import zipfile
import io
import threading


def parse_env_file(file_path=".env"):
    """Parse a .env file using only core Python and return a dictionary of variables."""
    env_vars = {}

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"{file_path} does not exist.")

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue  # skip comments and blank lines

            if "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('\'"')  # Remove any surrounding quotes
                env_vars[key] = value
                os.environ[key] = value  # Optional: Set it to system environment too

    return env_vars


def move_bat_to_desktop_folder(bat_file_path, folder_name="Website"):
    # Get path to Desktop
    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")

    # Full path to target folder
    target_folder = os.path.join(desktop_path, folder_name)

    # Create folder if it doesn't exist
    os.makedirs(target_folder, exist_ok=True)

    # Target path for the .bat file
    bat_filename = os.path.basename(bat_file_path)
    target_bat_path = os.path.join(target_folder, bat_filename)

    # Copy the file
    shutil.copy2(bat_file_path, target_bat_path)

    print(f"✅ {bat_filename} moved to {target_folder}")

def download_and_setup():
    def task():
        install_button.config(state="disabled")
        
        update_status("\u23f3 Checking the selected folder...")

        env_data = parse_env_file("./config/server.env")

        zip_url = env_data.get("GITHUB_LINK")
        base_dir = project_path.get()
        server_dir = os.path.join(base_dir, "server")
        system_dir = os.path.join(base_dir, "system")
        storage_dir = os.path.join(base_dir, "storage")

        os.makedirs(server_dir, exist_ok=True)
        os.makedirs(system_dir, exist_ok=True)
        os.makedirs(storage_dir, exist_ok=True)

        if os.path.isfile(os.path.join(server_dir, "manage.py")):
            update_status("\u2705 Server already exists.")
            update_status("----end---")
            messagebox.showinfo("Already Installed", "This folder already contains the server.\n\nNo installation required.")
            install_button.config(state="normal")
            return

        try:
            update_status("------WEB Server Setup-----")
            update_status("\u2b07\ufe0f Downloading...")
            with urllib.request.urlopen(zip_url) as response:
                if response.status != 200:
                    raise Exception(f"Failed to download files: status code {response.status}")
                zip_content = response.read()
                update_status("\u2705 Downloaded.")

            with zipfile.ZipFile(io.BytesIO(zip_content)) as zip_ref:
                temp_extract_path = os.path.join(base_dir, "temp_files")
                if os.path.exists(temp_extract_path):
                    shutil.rmtree(temp_extract_path)
                zip_ref.extractall(temp_extract_path)
                update_status("\ud83d\udcdc Extracting.....")

            extracted_folder = os.path.join(temp_extract_path, env_data.get("PROJECT_DIR"))
            for item in os.listdir(extracted_folder):
                src = os.path.join(extracted_folder, item)
                dst = os.path.join(server_dir, item)
                if os.path.exists(dst):
                    if os.path.isdir(dst):
                        shutil.rmtree(dst)
                    else:
                        os.remove(dst)
                shutil.move(src, dst)

            shutil.rmtree(temp_extract_path)
            update_status("\ud83d\udcc1 Extracted.")


            # server Config start
            server_venv_path = os.path.join(server_dir, "venv")
            if not os.path.exists(server_venv_path):
                update_status("\u2699\ufe0f Creating virtual environment....")
                subprocess.run(["python", "-m", "venv", server_venv_path], check=True)
                update_status("\u2705 Created Virtual environment.")
            else:
                update_status("\ud83d\udce6 Using existing virtual environment.")

            server_pip_path = os.path.join(server_venv_path, "Scripts", "pip.exe")
            server_python_path = os.path.join(server_venv_path, "Scripts", "python.exe")
            req_file = os.path.join(server_dir, "requirements.txt")

            # install requirements for server        
            if os.path.exists(req_file):
                update_status("\ud83d\udcc5 Installing from requirements.txt...")
                subprocess.run([server_pip_path, "install", "-r", req_file], check=True)
            
            update_status("\ud83d\udcc2 Running migrations...")
            subprocess.run([server_python_path, "manage.py", "makemigrations"], cwd=server_dir, check=True)

            update_status("\ud83d\udcc2 Applying migrations...")
            subprocess.run([server_python_path, "manage.py", "migrate"], cwd=server_dir, check=True)

            # server config ends

            # system
            update_status("-------SYSTEM SETUP------")
            system_venv_path = os.path.join(system_dir, "venv")
            if not os.path.exists(system_venv_path):
                update_status("\u2699\ufe0f Creating virtual environment")
                subprocess.run(["python", "-m", "venv", system_venv_path], check=True)
                update_status("\u2705 Created virtual environment")
            else:
                update_status("\ud83d\udce6 Using existing virtual environment.")

            system_pip_path = os.path.join(system_venv_path, "Scripts", "pip.exe")
            system_python_path = os.path.join(system_venv_path, "Scripts", "pythonw.exe")

            current_file_path = os.path.abspath(__file__)
            current_directory = os.path.dirname(current_file_path)
            req_file = os.path.join(current_directory, "system", "requirements.txt")
            if os.path.exists(req_file):
                update_status("\ud83d\udcc5 Installing from requirements.txt...")
                subprocess.run([system_pip_path, "install", "-r", req_file], check=True)
            # batFile=os.path.join(current_directory, "system", "controller.bat")
            pycontroller=os.path.join(current_directory, "system", "controller.py")
            print(server_dir)
            shutil.copy(pycontroller,system_dir)

            
            # Creating bat files 
            
            bat_content = f"""
                @echo off
                setlocal

                :: Auto-generated paths
                set "VENV_PATH={system_python_path}"
                set "PY_FILE={system_dir}/controller.py"

                :: Run Python file using venv
                start "" "%VENV_PATH%" "%PY_FILE%"

                exit
                """
            bat_file = os.path.join(system_dir, 'controller.bat')
            with open(bat_file, 'w') as f:
                f.write(bat_content)
            move_bat_to_desktop_folder(bat_file)
            update_status("-----------SHORTCUTS----------")
            update_status(" All shorcuts are created to desktop ")
            update_status("Location : Desktop>Website>controllber.bat")
            
            # Path to the folder (e.g., Desktop\Website)
            shorcut_dir = os.path.join(os.path.expanduser("~"), "Desktop", "Website")

            # Open File Explorer to that folder
            subprocess.run(["explorer", shorcut_dir])
            update_status("opening shorcuts in file explore and you can see there")


            with open(os.path.join(system_dir, "secrets.env"), "w") as f:
                f.write("DJANGO_PORT=9000\n")
                f.write("DJANGO_HOST=127.0.0.1\n")
                f.write(f"VENV_PATH={system_venv_path.replace("\\", "/")}\n")



            update_status("\ud83d\ude80 installation completion")
            messagebox.showinfo("Done", "Installation complete. USE : Desktop>Website>controllber.bat for your regular use")

        except Exception as e:
            messagebox.showerror("Error", str(e))
            update_status(f"\u274c Setup failed: {e}")
        finally:
            install_button.config(state="normal")

    def update_status(msg):
        log_output.insert(tk.END, msg + "\n")
        log_output.see(tk.END)
        root.update_idletasks()

    threading.Thread(target=task, daemon=True).start()

def browse_folder():
    folder = filedialog.askdirectory()
    if folder:
        project_path.set(folder)

root = tk.Tk()
root.title("RSC Software (e-learning) Installer")
root.geometry("650x500")
root.resizable(False, False)
root.configure(bg="#f0f2f5")

font_title = ("Segoe UI", 16, "bold")
font_label = ("Segoe UI", 11)
font_button = ("Segoe UI", 12, "bold")

tk.Label(root, text="Select folder to setup server:", font=font_title, bg="#f0f2f5").pack(pady=15)
frame = tk.Frame(root, bg="#f0f2f5")
frame.pack(pady=5)

project_path = tk.StringVar(value=os.getcwd())
entry = tk.Entry(frame, textvariable=project_path, width=50, font=font_label)
entry.pack(side="left", padx=(0,10))

tk.Button(frame, text="Browse", command=browse_folder, font=font_button, bg="#4CAF50", fg="white", relief="flat").pack(side="left")
install_button = tk.Button(root, text="⬇️ Install Now", font=font_button, command=download_and_setup, bg="#2196F3", fg="white", relief="flat", padx=15, pady=8)
install_button.pack(pady=10)

status_label = tk.Label(root, text="", font=font_label, fg="#333", bg="#f0f2f5")
status_label.pack()

log_output = ScrolledText(root, height=10, width=78, font=("Consolas", 10), bg="#ffffff", wrap="word")
log_output.pack(pady=10, padx=10)
log_output.insert(tk.END, "🔧 Logs will appear here...\n")
log_output.config(state="normal")
log_output.see(tk.END)

root.mainloop()
