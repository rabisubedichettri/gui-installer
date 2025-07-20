import subprocess
import os
import tkinter as tk
from tkinter import messagebox, scrolledtext
import socket
import threading
from datetime import datetime
import pystray
from PIL import Image, ImageDraw

# Configuration
# CURRENT_DIR = os.path.dirname(os.path.abspath("C:\Users\alpha\Desktop\mysoftware"))
CURRENT_DIR = os.path.dirname(__file__)
root_dir = os.path.dirname(CURRENT_DIR)                   # go up to root
server_dir = os.path.join(root_dir, 'server') 
VENV_DIR = os.path.join(server_dir, "venv")
PYTHON_PATH = os.path.join(VENV_DIR, "Scripts", "python.exe")

# App window setup
root = tk.Tk()
root.title("🌐 E-learning Server Controller")
root.geometry("700x550")
root.resizable(False, False)
root.configure(bg="#f8f9fa")

# Host & Port (default)
host_var = tk.StringVar(value="127.0.0.1")
port_var = tk.StringVar(value="12000")
host_option_var = tk.StringVar(value="local")  # 'local' or 'public'

# Styling
LABEL_FONT = ("Segoe UI", 10)
BUTTON_FONT = ("Segoe UI", 11, "bold")
ENTRY_FONT = ("Consolas", 10)

def update_host_var():
    if host_option_var.get() == "local":
        host_var.set("127.0.0.1")
    else:
        host_var.set("0.0.0.0")

# Top Inputs Frame
frame_top = tk.Frame(root, bg="#f8f9fa")
frame_top.pack(pady=15)

tk.Label(frame_top, text="Select Host Type:", font=LABEL_FONT, bg="#f8f9fa").grid(row=0, column=0, padx=6, sticky="e")
tk.Radiobutton(frame_top, text="Localhost (127.0.0.1)", variable=host_option_var, value="local", bg="#f8f9fa", command=update_host_var).grid(row=0, column=1, sticky="w")
tk.Radiobutton(frame_top, text="Public (0.0.0.0)", variable=host_option_var, value="public", bg="#f8f9fa", command=update_host_var).grid(row=0, column=2, sticky="w")

tk.Label(frame_top, text="🌍 Host (Editable):", font=LABEL_FONT, bg="#f8f9fa").grid(row=1, column=0, padx=6, sticky="e")
tk.Entry(frame_top, textvariable=host_var, width=18, font=ENTRY_FONT).grid(row=1, column=1, columnspan=2, sticky="w")

tk.Label(frame_top, text="🔢 Port:", font=LABEL_FONT, bg="#f8f9fa").grid(row=1, column=3, padx=6, sticky="e")
tk.Entry(frame_top, textvariable=port_var, width=10, font=ENTRY_FONT).grid(row=1, column=4)

# Log output box
log_text = scrolledtext.ScrolledText(root, wrap=tk.WORD, font=("Consolas", 10), bg="#ffffff", relief="solid")
log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

def update_log(msg, clear=False):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_msg = f"[{timestamp}] {msg}"
    def insert():
        if clear:
            log_text.delete(1.0, tk.END)
        log_text.insert(tk.END, full_msg + "\n")
        log_text.see(tk.END)
    root.after(0, insert)

def is_port_in_use(host, port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex((host, int(port))) == 0
    except Exception:
        return False

server_process = None

def start_server():
    global server_process
    root.after(0, lambda: btn_start.config(state="disabled"))
    root.after(0, lambda: btn_stop.config(state="normal"))

    host = host_var.get()
    port = port_var.get()
    update_log("🔁 Starting server...", clear=True)

    if is_port_in_use(host, port):
        update_log(f"⚠️ Port {port} already in use on {host}. Stop it first.")
        root.after(0, lambda: btn_start.config(state="normal"))
        root.after(0, lambda: btn_stop.config(state="disabled"))
        return

    if not os.path.exists(PYTHON_PATH):
        update_log(PYTHON_PATH)
        update_log("❌ Virtual environment not found.")
        root.after(0, lambda: btn_start.config(state="normal"))
        root.after(0, lambda: btn_stop.config(state="disabled"))
        return

    try:
        update_log("✅ Virtual environment detected.")
        update_log("📂 Running migrations (commented out)...")
        # subprocess.run([PYTHON_PATH, "manage.py", "migrate"], check=True)

        update_log(f"🚀 Launching server at http://{host}:{port} (100%)...")

        # server_process = subprocess.run(
        #     [PYTHON_PATH, "manage.py", "runserver", f"{host}:{port}"],
        #     creationflags=subprocess.DETACHED_PROCESS if os.name == 'nt' else 0
        # )

        subprocess.run(
            [PYTHON_PATH, "manage.py", "runserver", f"{host}:{port}"],
            cwd=server_dir,  creationflags=subprocess.CREATE_NO_WINDOW

        )

        update_log("✅ Server is running.")

        # root.after(0, lambda: messagebox.showinfo("Started", f"Server is now running at:\nhttp://{host}:{port}/"))

    except subprocess.CalledProcessError as e:
        update_log(f"❌ Error during startup: {str(e)}")
        root.after(0, lambda: messagebox.showerror("Error", str(e)))
        root.after(0, lambda: btn_start.config(state="normal"))
        root.after(0, lambda: btn_stop.config(state="disabled"))

def stop_server():
    global server_process
    port = port_var.get()
    update_log("⛔ Attempting to stop server...")

    try:
        if os.name == 'nt':
            result = subprocess.check_output(f'netstat -ano | findstr :{port}', shell=True).decode()
            lines = result.strip().split('\n')
            pids = set()
            for line in lines:
                parts = line.strip().split()
                if len(parts) >= 5:
                    pids.add(parts[-1])
            for pid in pids:
                subprocess.call(["taskkill", "/PID", pid, "/F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            result = subprocess.check_output(f"lsof -ti tcp:{port}", shell=True).decode().strip()
            if result:
                for pid in result.split("\n"):
                    subprocess.call(["kill", "-9", pid])

        if server_process and server_process.poll() is None:
            server_process.terminate()
            server_process = None

        update_log(f"✅ Server on port {port} has been stopped.")
        root.after(0, lambda: messagebox.showinfo("Stopped", f"Server on port {port} has been terminated."))

        root.after(0, lambda: btn_start.config(state="normal"))
        root.after(0, lambda: btn_stop.config(state="disabled"))

    except Exception as e:
        update_log(f"⚠️ Failed to stop server: {e}")
        # root.after(0, lambda: messagebox.showerror("Stop Failed", str(e)))

btn_frame = tk.Frame(root, bg="#f8f9fa")
btn_frame.pack(pady=10)

btn_start = tk.Button(btn_frame, text="▶ Start Server (Run)", font=BUTTON_FONT, bg="#28a745", fg="white",
                      width=25, command=lambda: threading.Thread(target=start_server, daemon=True).start())
btn_start.pack(side=tk.LEFT, padx=15)

btn_stop = tk.Button(btn_frame, text="⏹ Stop Server (Kill)", font=BUTTON_FONT, bg="#dc3545", fg="white",
                     width=25, state="disabled", command=lambda: threading.Thread(target=stop_server, daemon=True).start())
btn_stop.pack(side=tk.LEFT, padx=15)

# ===== System Tray Integration =====
icon = None

def create_image():
    # Create a simple square icon with a color (you can customize)
    width = 64
    height = 64
    color1 = "#28a745"  # green
    image = Image.new('RGB', (width, height), color1)
    dc = ImageDraw.Draw(image)
    dc.rectangle((width // 4, height // 4, width * 3 // 4, height * 3 // 4), fill="white")
    return image

def on_quit(icon, item):
    icon.stop()
    root.destroy()

def on_show(icon, item):
    root.after(0, root.deiconify)

def minimize_to_tray():
    root.withdraw()
    global icon
    if icon is None:
        icon = pystray.Icon("django-controller", create_image(), "Django Server Controller", menu=pystray.Menu(
            pystray.MenuItem("Show", on_show),
            pystray.MenuItem("Quit", on_quit)
        ))
        threading.Thread(target=icon.run, daemon=True).start()

# Override window close button to minimize to tray instead of close
def on_closing():
    minimize_to_tray()

root.protocol("WM_DELETE_WINDOW", on_closing)

# Add a minimize button to trigger minimize_to_tray
def add_minimize_button():
    btn_minimize = tk.Button(btn_frame, text="🗕 Minimize to Tray", font=BUTTON_FONT, bg="#6c757d", fg="white",
                             width=20, command=minimize_to_tray)
    btn_minimize.pack(side=tk.LEFT, padx=15)

add_minimize_button()

root.mainloop()
